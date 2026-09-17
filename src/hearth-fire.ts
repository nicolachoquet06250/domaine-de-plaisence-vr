import { createSystem, Mesh, Object3D, PointLightComponent, ShaderMaterial, Vector3 } from '@iwsdk/core';
import { HearthFire, HearthGlow } from './hearth-components.js';
import { CoachJourney } from './coach-journey-components.js';

type FireState = { mesh: Mesh; original: ShaderMaterial; material: ShaderMaterial };
export class HearthFireSystem extends createSystem({ fires: { required: [HearthFire] }, glows: { required: [HearthGlow, PointLightComponent] }, journeys:{required:[CoachJourney]} }) {
  private states = new WeakMap<Object3D, FireState>();
  private eye = new Vector3();
  private position = new Vector3();
  private clock = 0;
  private bind(root: Object3D): void {
    if (this.states.has(root)) return;
    let mesh: Mesh | undefined;
    root.traverse(object => {
      if ((object as Mesh).isMesh && (object as Mesh).material instanceof ShaderMaterial) mesh = object as Mesh;
    });
    if (!mesh) return;
    const original = mesh.material as ShaderMaterial, material = original.clone();
    mesh.material = material;
    this.states.set(root, { mesh, original, material });
  }
  private release(root?: Object3D): void {
    if (!root) return;
    const state = this.states.get(root);
    if (state) { state.mesh.material = state.original; state.material.dispose(); this.states.delete(root); }
  }
  init(): void {
    this.cleanupFuncs.push(
      this.queries.fires.subscribe('qualify', e => { if (e.object3D) this.bind(e.object3D); }),
      this.queries.fires.subscribe('disqualify', e => this.release(e.object3D)),
      () => { for (const e of this.queries.fires.entities) this.release(e.object3D); },
    );
    for (const e of this.queries.fires.entities) if (e.object3D) this.bind(e.object3D);
  }
  update(delta: number): void {
    let effects=true;
    for(const e of this.queries.journeys?.entities??[])effects=!!e.getValue(CoachJourney,'effectsEnabled');
    this.clock = (this.clock + Math.min(delta, .1)) % 3600;
    (this.xrManager.isPresenting ? this.player.head : this.camera).getWorldPosition(this.eye);
    for (const e of this.queries.fires.entities) {
      const root = e.object3D, state = root && this.states.get(root);
      if (!root || !state) continue;
      root.getWorldPosition(this.position);
      const near = effects && this.eye.distanceToSquared(this.position) < 28 * 28;
      const t = this.clock + (e.getValue(HearthFire, 'phase') ?? 0);
      state.mesh.visible = near;
      if(effects)state.material.uniforms.time.value = t;
      e.setValue(HearthFire, 'elapsed', t);
    }
    // IWSDK owns the actual lights outside the authored object hierarchy.
    // Animate their components so LightSystem can apply the change reliably.
    for (const e of this.queries.glows.entities) {
      if (!e.object3D) continue;
      e.object3D.getWorldPosition(this.position);
      const near = effects && this.eye.distanceToSquared(this.position) < 28 * 28;
      const t = this.clock + (e.getValue(HearthGlow, 'phase') ?? 0);
      e.setValue(PointLightComponent, 'intensity', near ? 3 + .45 * Math.sin(t * 8.7) + .25 * Math.sin(t * 17.3) : 0);
    }
  }
}
