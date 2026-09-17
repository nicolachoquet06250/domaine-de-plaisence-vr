import {
  BufferAttribute, BufferGeometry, Group, InstancedMesh, Matrix4, Mesh,
  MeshBasicMaterial, Object3D, Vector3,
} from '@iwsdk/core';

/** Bake solid prototypes into the indexed triangle format consumed by Locomotor.
 * Its environment collector neither expands instances nor normalizes attributes.
 * Build once at manifest evaluation; placements share this immutable geometry.
 */
export function createStaticCollision(source: Object3D): Group {
  const parts: { mesh: Mesh; count: number }[] = [];
  let vertexCount = 0;
  let indexCount = 0;
  source.updateWorldMatrix(true, true);
  source.traverse((object) => {
    if (!(object instanceof Mesh) || !object.geometry.getAttribute('position')) return;
    const count = object instanceof InstancedMesh ? object.count : 1;
    parts.push({ mesh: object, count });
    vertexCount += object.geometry.getAttribute('position').count * count;
    indexCount += (object.geometry.index?.count ?? object.geometry.getAttribute('position').count) * count;
  });
  const positions = new Float32Array(vertexCount * 3);
  const indices = new Uint32Array(indexCount);
  const rootInverse = new Matrix4().copy(source.matrixWorld).invert();
  const matrix = new Matrix4();
  const instance = new Matrix4();
  const vertex = new Vector3();
  let vertexOffset = 0;
  let indexOffset = 0;
  for (const { mesh, count } of parts) {
    const position = mesh.geometry.getAttribute('position');
    const index = mesh.geometry.index;
    const size = index?.count ?? position.count;
    for (let copy = 0; copy < count; copy++) {
      matrix.multiplyMatrices(rootInverse, mesh.matrixWorld);
      if (mesh instanceof InstancedMesh) {
        mesh.getMatrixAt(copy, instance);
        matrix.multiply(instance);
      }
      for (let i = 0; i < position.count; i++) {
        vertex.fromBufferAttribute(position, i).applyMatrix4(matrix);
        vertex.toArray(positions, (vertexOffset + i) * 3);
      }
      // Preserve outward winding for mirrored instances too.
      const mirrored = matrix.determinant() < 0;
      for (let i = 0; i < size; i += 3) {
        indices[indexOffset++] = vertexOffset + (index ? index.getX(i) : i);
        const second = i + (mirrored ? 2 : 1);
        const third = i + (mirrored ? 1 : 2);
        indices[indexOffset++] = vertexOffset + (index ? index.getX(second) : second);
        indices[indexOffset++] = vertexOffset + (index ? index.getX(third) : third);
      }
      vertexOffset += position.count;
    }
  }
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new BufferAttribute(positions, 3));
  geometry.setIndex(new BufferAttribute(indices, 1));
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  const material = new MeshBasicMaterial();
  material.visible = false; // Locomotor still reads triangles; no extra rendering or shadows.
  const collision = new Group();
  collision.name = `Collisions — ${source.name || 'decor'}`;
  collision.add(new Mesh(geometry, material));
  return collision;
}
