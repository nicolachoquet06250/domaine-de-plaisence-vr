import { Matrix4, Mesh, Quaternion, Vector3, type Bone, type BufferAttribute, type Object3D, type SkinnedMesh } from '@iwsdk/core';

export type HairGroom = {
  version: 1; points: number[][]; pointsPerStrand: number;
  gravity: number; damping: number; shapeStiffness: number;
  headCenter: number[]; headRadii: number[]; shoulderCenter: number[]; shoulderRadii: number[];
};

/** A fixed-step, position-based strand solver. Positions are WORLD-space particles;
 * pinned roots follow the animated head, so motion produces actual inertia.
 * This is a strand solver, separate from Havok's rigid-body simulation. */
export class HairParticleSolver {
  readonly positions: Float32Array;
  readonly previous: Float32Array;
  readonly rest: Float32Array;
  readonly goals: Float32Array;
  readonly lengths: Float32Array;
  readonly inverseHead = new Matrix4();
  readonly lastOrigin = new Vector3();
  readonly localPoints: Float32Array;
  readonly rotations: Float32Array;
  gravity: number;
  maxRootError = 0;
  maxLengthError = 0;
  maxDeflection = 0;
  simulatedSteps = 0;
  private accumulated = 0;
  private initialized = false;
  private readonly point = new Vector3();
  private readonly tangent = new Vector3();
  private readonly restTangent = new Vector3();
  private readonly rotation = new Quaternion();
  private readonly origin = new Vector3();
  private readonly headCenter = new Vector3();
  private readonly shoulderCenter = new Vector3();
  private readonly headRadii = new Vector3();
  private readonly shoulderRadii = new Vector3();
  private readonly count: number;
  private readonly perStrand: number;
  private readonly damping: number;
  private readonly stiffness: number;

  constructor(readonly groom: HairGroom, toHeadLocal = new Matrix4()) {
    this.count = groom.points.length; this.perStrand = groom.pointsPerStrand;
    if (!Number.isInteger(this.perStrand) || this.perStrand < 3 || this.count % this.perStrand !== 0 || this.count > 5000)
      throw new Error('Invalid hair particle topology');
    this.rest = new Float32Array(this.count * 3);
    for (let i = 0; i < this.count; i++) {
      const p = groom.points[i];
      if (p.length !== 3 || !p.every(Number.isFinite)) throw new Error('Non-finite groom point');
      this.point.fromArray(p).applyMatrix4(toHeadLocal).toArray(this.rest, i * 3);
    }
    this.positions = new Float32Array(this.rest.length); this.previous = new Float32Array(this.rest.length);
    this.goals = new Float32Array(this.rest.length); this.localPoints = new Float32Array(this.rest.length);
    this.rotations = new Float32Array(this.count * 4); this.lengths = new Float32Array(this.count);
    for (let i = 1; i < this.count; i++) if (i % this.perStrand)
      this.lengths[i] = Math.hypot(this.rest[i * 3] - this.rest[(i - 1) * 3], this.rest[i * 3 + 1] - this.rest[(i - 1) * 3 + 1], this.rest[i * 3 + 2] - this.rest[(i - 1) * 3 + 2]);
    this.gravity = groom.gravity; this.damping = Math.min(.999, Math.max(0, groom.damping));
    this.stiffness = Math.max(0, groom.shapeStiffness) * 1600;
    this.headCenter.fromArray(groom.headCenter).applyMatrix4(toHeadLocal);
    this.shoulderCenter.fromArray(groom.shoulderCenter).applyMatrix4(toHeadLocal);
    // Avatar Head bind frames are Y-up, unit-scale. The runtime applies avatar scale
    // through headWorld; collision radii use the same local metre convention.
    this.headRadii.fromArray(groom.headRadii); this.shoulderRadii.fromArray(groom.shoulderRadii);
  }

  reset(headWorld: Matrix4): void {
    for (let i = 0; i < this.count; i++) this.point.fromArray(this.rest, i * 3).applyMatrix4(headWorld).toArray(this.positions, i * 3);
    this.previous.set(this.positions); this.goals.set(this.positions);
    this.lastOrigin.setFromMatrixPosition(headWorld); this.initialized = true; this.accumulated = 0;
  }

  update(delta: number, headWorld: Matrix4): void {
    this.origin.setFromMatrixPosition(headWorld);
    if (!this.initialized || this.lastOrigin.distanceToSquared(this.origin) > .25 || !Number.isFinite(delta)) this.reset(headWorld);
    this.lastOrigin.copy(this.origin); this.inverseHead.copy(headWorld).invert();
    for (let i = 0; i < this.count; i++) this.point.fromArray(this.rest, i * 3).applyMatrix4(headWorld).toArray(this.goals, i * 3);
    const e = headWorld.elements, scale = Math.hypot(e[0], e[1], e[2]);
    const dt = 1 / 120;
    this.accumulated += Math.max(0, Math.min(delta, .1));
    while (this.accumulated + 1e-10 >= dt) {
      this.accumulated -= dt; this.simulatedSteps++;
      for (let i = 0; i < this.count; i++) {
        const k = i * 3;
        if (i % this.perStrand < 2) {
          for (let a = 0; a < 3; a++) this.previous[k + a] = this.positions[k + a] = this.goals[k + a];
          continue;
        }
        for (let a = 0; a < 3; a++) {
          const p = this.positions[k + a], velocity = (p - this.previous[k + a]) * this.damping;
          const acceleration = (this.goals[k + a] - p) * this.stiffness - (a === 1 ? this.gravity : 0);
          this.previous[k + a] = p; this.positions[k + a] = p + velocity + acceleration * dt * dt;
        }
      }
      for (let iteration = 0; iteration < 7; iteration++) {
        for (let i = 2; i < this.count; i++) {
          if (i % this.perStrand < 2) continue;
          const b = i * 3, a = b - 3;
          const dx = this.positions[b] - this.positions[a], dy = this.positions[b + 1] - this.positions[a + 1], dz = this.positions[b + 2] - this.positions[a + 2];
          const length = Math.hypot(dx, dy, dz);
          if (length < 1e-9) continue;
          const correction = (length - this.lengths[i] * scale) / length;
          const previousFree = i % this.perStrand > 2, w = previousFree ? .5 : 1;
          this.positions[b] -= dx * correction * w; this.positions[b + 1] -= dy * correction * w; this.positions[b + 2] -= dz * correction * w;
          if (previousFree) {
            this.positions[a] += dx * correction * .5; this.positions[a + 1] += dy * correction * .5; this.positions[a + 2] += dz * correction * .5;
          }
          this.point.fromArray(this.positions, b).applyMatrix4(this.inverseHead);
          this.collide(this.headCenter, this.headRadii); this.collide(this.shoulderCenter, this.shoulderRadii);
          this.point.applyMatrix4(headWorld).toArray(this.positions, b);
        }
      }
    }
    this.maxRootError = 0; this.maxLengthError = 0; this.maxDeflection = 0;
    for (let i = 0; i < this.count; i++) {
      const k = i * 3;
      if (i % this.perStrand < 2) {
        for (let a = 0; a < 3; a++) this.positions[k + a] = this.goals[k + a];
      }
      this.point.fromArray(this.positions, k).applyMatrix4(this.inverseHead).toArray(this.localPoints, k);
      const deflection = Math.hypot(this.positions[k] - this.goals[k], this.positions[k + 1] - this.goals[k + 1], this.positions[k + 2] - this.goals[k + 2]);
      this.maxDeflection = Math.max(this.maxDeflection, deflection);
      if (i % this.perStrand < 2) this.maxRootError = Math.max(this.maxRootError, deflection);
      else this.maxLengthError = Math.max(this.maxLengthError, Math.abs(Math.hypot(this.positions[k] - this.positions[k - 3], this.positions[k + 1] - this.positions[k - 2], this.positions[k + 2] - this.positions[k - 1]) - this.lengths[i] * scale));
    }
    for (let i = 0; i < this.count; i++) {
      const j = i % this.perStrand === this.perStrand - 1 ? i - 1 : i + 1;
      this.restTangent.fromArray(this.rest, j * 3).sub(this.point.fromArray(this.rest, i * 3)).normalize();
      this.tangent.fromArray(this.localPoints, j * 3).sub(this.point.fromArray(this.localPoints, i * 3)).normalize();
      this.rotation.setFromUnitVectors(this.restTangent, this.tangent).toArray(this.rotations, i * 4);
    }
  }

  private collide(center: Vector3, radii: Vector3): void {
    const x = (this.point.x - center.x) / radii.x, y = (this.point.y - center.y) / radii.y, z = (this.point.z - center.z) / radii.z;
    const length = Math.hypot(x, y, z);
    if (length > 1e-6 && length < 1) this.point.set(center.x + x * radii.x / length, center.y + y * radii.y / length, center.z + z * radii.z / length);
  }
}

export class AvatarHair {
  readonly solver: HairParticleSolver;
  readonly mesh: Mesh;
  private readonly offsets: Float32Array;
  private readonly restNormals: Float32Array;
  private readonly indices: Uint32Array;
  private readonly position: BufferAttribute;
  private readonly normal: BufferAttribute;
  private readonly point = new Vector3();
  private readonly quaternion = new Quaternion();
  private readonly originalVisible: boolean;

  constructor(private readonly source: SkinnedMesh, private readonly head: Bone, groom: HairGroom) {
    const headIndex = source.skeleton.bones.indexOf(head);
    const toHead = new Matrix4().multiplyMatrices(source.skeleton.boneInverses[headIndex], source.bindMatrix);
    this.solver = new HairParticleSolver(groom, toHead);
    const geometry = source.geometry.clone();
    this.mesh = new Mesh(geometry, source.material); this.mesh.name = 'Hair particles — gravity';
    this.mesh.userData.firstPersonHidden = true; this.mesh.frustumCulled = false;
    this.position = geometry.getAttribute('position') as BufferAttribute; this.normal = geometry.getAttribute('normal') as BufferAttribute;
    const ids = geometry.getAttribute('_hair_particle') ?? geometry.getAttribute('_HAIR_PARTICLE');
    if (!ids) { geometry.dispose(); throw new Error('Groom is missing particle bindings'); }
    this.indices = new Uint32Array(this.position.count); this.offsets = new Float32Array(this.position.count * 3); this.restNormals = new Float32Array(this.position.count * 3);
    for (let i = 0; i < this.position.count; i++) {
      const id = Math.round(ids.getX(i));
      if (id < 0 || id >= groom.points.length) { geometry.dispose(); throw new Error('Invalid hair particle binding'); }
      this.indices[i] = id;
      this.point.fromBufferAttribute(this.position, i).applyMatrix4(toHead);
      this.position.setXYZ(i, this.point.x, this.point.y, this.point.z);
      this.point.x -= this.solver.rest[id * 3]; this.point.y -= this.solver.rest[id * 3 + 1]; this.point.z -= this.solver.rest[id * 3 + 2];
      this.point.toArray(this.offsets, i * 3);
      this.point.fromBufferAttribute(this.normal, i).transformDirection(toHead).toArray(this.restNormals, i * 3);
    }
    this.originalVisible = source.visible; source.visible = false; head.add(this.mesh);
  }

  update(delta: number): void {
    this.head.updateWorldMatrix(true, false); this.solver.update(delta, this.head.matrixWorld);
    for (let i = 0; i < this.position.count; i++) {
      const id = this.indices[i], k = id * 3;
      this.quaternion.fromArray(this.solver.rotations, id * 4);
      this.point.fromArray(this.offsets, i * 3).applyQuaternion(this.quaternion);
      this.position.setXYZ(i, this.solver.localPoints[k] + this.point.x, this.solver.localPoints[k + 1] + this.point.y, this.solver.localPoints[k + 2] + this.point.z);
      this.point.fromArray(this.restNormals, i * 3).applyQuaternion(this.quaternion); this.normal.setXYZ(i, this.point.x, this.point.y, this.point.z);
    }
    this.position.needsUpdate = true; this.normal.needsUpdate = true;
  }

  dispose(): void { this.mesh.removeFromParent(); this.mesh.geometry.dispose(); this.source.visible = this.originalVisible; }
}

export function createAvatarHair(model: Object3D): AvatarHair[] {
  const sources: SkinnedMesh[] = [], hair: AvatarHair[] = [];
  model.traverse(object => { if ((object as SkinnedMesh).isSkinnedMesh && object.userData.hairDynamics?.version === 1) sources.push(object as SkinnedMesh); });
  for (const source of sources) {
    const head = source.skeleton.bones.find(bone => bone.name === 'Head');
    if (!head) throw new Error('Hair particles require the avatar Head bone');
    hair.push(new AvatarHair(source, head, source.userData.hairDynamics));
  }
  return hair;
}
