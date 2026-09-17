import { AnimationMixer, AssetManager, createSystem, LocomotionEnvironment, LoopOnce, Object3D, Pressed, Vector3, type AnimationAction } from '@iwsdk/core';
import { PalaceDoor, PalaceDoorBlocker } from './palace-door-components.js';

/** Reverse the actual Blender hinge animation; proximity protects the doorway. */
export class PalaceDoorSystem extends createSystem({
  doors: { required: [PalaceDoor] },
  pressed: { required: [PalaceDoor, Pressed] },
  blockers: { required: [PalaceDoorBlocker] },
}) {
  private states = new WeakMap<Object3D, { mixer: AnimationMixer; actions: AnimationAction[]; duration: number; hold: number }>();
  private viewer = new Vector3();
  private localViewer = new Vector3();

  private bind(root: Object3D) {
    if (this.states.has(root)) return;
    const gltf=AssetManager.getGLTF('palaceDoor',{shared:true});
    if (!gltf?.animations.length) { console.error('Missing Blender palace door clip'); return; }
    const mixer=new AnimationMixer(root), actions: AnimationAction[]=[];
    let duration=0;
    for (const clip of gltf.animations) {
      const action=mixer.clipAction(clip); action.setLoop(LoopOnce,1); action.clampWhenFinished=true; action.play(); actions.push(action);
      duration=Math.max(duration,clip.duration);
    }
    this.states.set(root,{mixer,actions,duration,hold:0});
  }

  private release(root: Object3D | undefined) {
    if (!root) return;
    const state=this.states.get(root); state?.mixer.stopAllAction(); state?.mixer.uncacheRoot(root); this.states.delete(root);
  }

  init() {
    this.cleanupFuncs.push(
      this.queries.doors.subscribe('qualify',entity=>{ if (entity.object3D) this.bind(entity.object3D); }),
      this.queries.doors.subscribe('disqualify',entity=>this.release(entity.object3D)),
      this.queries.pressed.subscribe('qualify',entity=>entity.setValue(PalaceDoor,'requestedOpen',!entity.getValue(PalaceDoor,'requestedOpen'))),
      ()=>{ for (const entity of this.queries.doors.entities) this.release(entity.object3D); },
    );
    for (const entity of this.queries.doors.entities) if (entity.object3D) this.bind(entity.object3D);
  }

  update(delta: number) {
    this.player.head.getWorldPosition(this.viewer);
    for (const entity of this.queries.doors.entities) {
      const root=entity.object3D, state=root && this.states.get(root);
      if (!root || !state) continue;
      root.worldToLocal(this.localViewer.copy(this.viewer));
      const distance=entity.getValue(PalaceDoor,'approachDistance') ?? 3.2;
      const near=this.localViewer.y>-.2 && this.localViewer.y<3.8 &&
        Math.abs(this.localViewer.x)<1.9 && Math.abs(this.localViewer.z)<distance;
      if (entity.getValue(PalaceDoor,'automatic') && near) state.hold=2;
      else state.hold=Math.max(0,state.hold-delta);
      const desired=entity.getValue(PalaceDoor,'requestedOpen') || state.hold>0 ? 1 : 0;
      const previous=entity.getValue(PalaceDoor,'openness') ?? 0, step=Math.min(delta,.05)/state.duration;
      const next=desired ? Math.min(1,previous+step) : Math.max(0,previous-step);
      if (next!==previous) {
        // LoopOnce pauses at the end: reactivate before sampling in reverse.
        for (const action of state.actions) { action.paused=false; action.enabled=true; }
        state.mixer.setTime(next*state.duration); entity.setValue(PalaceDoor,'openness',next);
      }
    }
    for (const entity of this.queries.blockers.entities) {
      const owner=entity.getValue(PalaceDoorBlocker,'owner');
      if (!owner?.hasComponent(PalaceDoor) || !entity.object3D?.parent) continue;
      const openness=owner.getValue(PalaceDoor,'openness') ?? 0;
      if (openness>=.85 && entity.hasComponent(LocomotionEnvironment)) entity.removeComponent(LocomotionEnvironment);
      else if (openness===0 && !entity.hasComponent(LocomotionEnvironment)) {
        entity.object3D.updateWorldMatrix(true,true); entity.addComponent(LocomotionEnvironment);
      }
    }
  }
}
