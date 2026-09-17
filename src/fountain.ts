import { AnimationMixer, AssetManager, createSystem, LoopRepeat, Object3D } from '@iwsdk/core';
import { FountainWater, WaterJet } from './fountain-components.js';
import { sharedRoomTime } from './multiplayer.js';
/** Plays Blender-authored morph clips on each placed GLB hierarchy. */
export class FountainSystem extends createSystem({
  jets: { required: [WaterJet] }, water: { required: [FountainWater] },
}) {
  private playback = new WeakMap<Object3D, { mixer: AnimationMixer; duration: number }>();

  private bind(root: Object3D, assetId: string) {
    if (this.playback.has(root)) return;
    const gltf = AssetManager.getGLTF(assetId, { shared: true });
    if (!gltf?.animations.length) {
      console.error(`Missing Blender water animation: ${assetId}`);
      return;
    }
    const mixer = new AnimationMixer(root);
    let duration = 0;
    for (const clip of gltf.animations) {
      mixer.clipAction(clip).setLoop(LoopRepeat, Infinity).play();
      duration = Math.max(duration, clip.duration);
    }
    this.playback.set(root, { mixer, duration });
  }

  private release(root: Object3D | undefined) {
    if (!root) return;
    const state = this.playback.get(root);
    state?.mixer.stopAllAction();
    state?.mixer.uncacheRoot(root);
    this.playback.delete(root);
  }

  init() {
    this.cleanupFuncs.push(
      this.queries.jets.subscribe('qualify', (entity) => {
        if (entity.object3D) this.bind(entity.object3D, entity.getValue(WaterJet, 'kind') === 1 ? 'centralJet' : 'lateralJet');
      }),
      this.queries.water.subscribe('qualify', (entity) => {
        if (entity.object3D) this.bind(entity.object3D, 'water');
      }),
      this.queries.jets.subscribe('disqualify', (entity) => this.release(entity.object3D)),
      this.queries.water.subscribe('disqualify', (entity) => this.release(entity.object3D)),
      () => {
        for (const entity of this.queries.jets.entities) this.release(entity.object3D);
        for (const entity of this.queries.water.entities) this.release(entity.object3D);
      },
    );
    for (const entity of this.queries.jets.entities) {
      if (entity.object3D) this.bind(entity.object3D, entity.getValue(WaterJet, 'kind') === 1 ? 'centralJet' : 'lateralJet');
    }
    for (const entity of this.queries.water.entities) {
      if (entity.object3D) this.bind(entity.object3D, 'water');
    }
  }

  update() {
    const time = sharedRoomTime();
    for (const entity of this.queries.jets.entities) {
      const state = entity.object3D && this.playback.get(entity.object3D);
      if (!state) continue;
      const elapsed = (time + (entity.getValue(WaterJet, 'phase') ?? 0)) % state.duration;
      state.mixer.setTime(elapsed);
      entity.setValue(WaterJet, 'elapsed', elapsed);
    }
    for (const entity of this.queries.water.entities) {
      const state = entity.object3D && this.playback.get(entity.object3D);
      if (state) state.mixer.setTime(time % state.duration);
    }
  }
}
