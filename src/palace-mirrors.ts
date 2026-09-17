import { createSystem, Mesh, Vector3, type Object3D, type Material, type MeshPhysicalMaterial } from '@iwsdk/core';
import { PalaceMirror } from './mirror-components.js';
import { PlanarReflection } from './planar-reflection.js';
import { CoachJourney } from './coach-journey-components.js';

/** At most one nearby, front-facing mirror per frame, with a separate XR image per eye. */
export class PalaceMirrorSystem extends createSystem({ mirrors: { required: [PalaceMirror] }, journeys:{required:[CoachJourney]} }) {
  private states = new WeakMap<Object3D, PlanarReflection>();
  private viewer = new Vector3();
  private forward = new Vector3();
  private point = new Vector3();
  private normal = new Vector3();
  private direction = new Vector3();
  private frame = 0;
  private reflecting = false;
  private glassCache = new WeakMap<MeshPhysicalMaterial, MeshPhysicalMaterial>();
  private glassMaterials = new Set<Material>();
  private glassSwaps: {mesh:Mesh;original:Material;reflection:Material}[] = [];
  private glassBindings = new WeakMap<Mesh,{mesh:Mesh;original:Material;reflection:Material}>();
  private simplifyGlass = (object:Object3D) => {
    const mesh=object as Mesh;if(!mesh.isMesh||Array.isArray(mesh.material))return;
    const original=mesh.material as MeshPhysicalMaterial;if(!(original.transmission>0))return;
    let binding=this.glassBindings.get(mesh);
    if(!binding||binding.original!==original) {
      let reflection=this.glassCache.get(original);
      if(!reflection) {
        reflection=original.clone();reflection.transmission=0;reflection.transparent=true;
        reflection.opacity=.22;reflection.depthWrite=false;
        this.glassCache.set(original,reflection);this.glassMaterials.add(reflection);
      }
      binding={mesh,original,reflection};this.glassBindings.set(mesh,binding);
    }
    this.glassSwaps.push(binding);mesh.material=binding.reflection;
  };
  private before = () => {
    this.reflecting=true;
    for(const entity of this.queries.mirrors.entities){const s=entity.object3D&&this.states.get(entity.object3D);if(s){s.previousVisible=s.mesh.visible;s.mesh.visible=false;}}
    // Reflective glass needs no nested scene-refraction pass for each eye.
    // Reuse transparent substitutes only during reflection, restoring main materials below.
    this.scene.traverse(this.simplifyGlass);
  };
  private after = () => {
    for(const entity of this.queries.mirrors.entities){const s=entity.object3D&&this.states.get(entity.object3D);if(s)s.mesh.visible=s.previousVisible;}
    for(const binding of this.glassSwaps)binding.mesh.material=binding.original;
    this.glassSwaps.length=0;
    this.reflecting=false;
  };
  private bind(root: Object3D): void {
    if(this.states.has(root))return;
    let mesh: Mesh | undefined;root.traverse(o=>{if((o as Mesh).isMesh)mesh=o as Mesh;});
    if(!mesh)return;
    const state=new PlanarReflection(mesh);this.states.set(root,state);
    mesh.onBeforeRender=(renderer,scene,camera)=>{
      if(this.reflecting)return;
      const eyes=renderer.xr.isPresenting?renderer.xr.getCamera().cameras:undefined;
      const eye=eyes&&camera===eyes[1]?1:0;
      state.bindEye(eye);
    };
  }
  private release(root?: Object3D): void {if(root){this.states.get(root)?.dispose();this.states.delete(root);}}
  init(): void {
    const scene = this.scene, original = scene.onBeforeRender;
    const capture: typeof scene.onBeforeRender = (...args) => {
      original.apply(scene, args);
      if (this.reflecting) return;
      for (const entity of this.queries.mirrors.entities) {
        const state = entity.object3D && this.states.get(entity.object3D);
        if (state?.enabled) state.capture(args[0], scene, args[2], this.frame, this.before, this.after);
      }
    };
    scene.onBeforeRender = capture;
    this.cleanupFuncs.push(() => { if (scene.onBeforeRender === capture) scene.onBeforeRender = original; });
    this.cleanupFuncs.push(()=>{for(const material of this.glassMaterials)material.dispose();this.glassMaterials.clear();});
    this.cleanupFuncs.push(this.queries.mirrors.subscribe('qualify',e=>{if(e.object3D)this.bind(e.object3D);}),this.queries.mirrors.subscribe('disqualify',e=>this.release(e.object3D)),()=>{for(const e of this.queries.mirrors.entities)this.release(e.object3D);});
    for(const e of this.queries.mirrors.entities)if(e.object3D)this.bind(e.object3D);
  }
  update(): void {
    this.frame++;
    let effects=true;
    for(const e of this.queries.journeys?.entities??[])effects=!!e.getValue(CoachJourney,'effectsEnabled');
    if(!effects){
      for(const e of this.queries.mirrors.entities){const state=e.object3D&&this.states.get(e.object3D);if(state)state.enabled=false;e.setValue(PalaceMirror,'active',false);}
      return;
    }
    const camera=this.xrManager.isPresenting?this.player.head:this.camera;
    camera.getWorldPosition(this.viewer);this.forward.set(0,0,-1).transformDirection(camera.matrixWorld);
    let best: PlanarReflection | undefined, score=Infinity;
    for(const entity of this.queries.mirrors.entities){
      const state=entity.object3D&&this.states.get(entity.object3D);if(!state)continue;
      state.enabled=false;state.mesh.updateWorldMatrix(true,false);
      this.point.setFromMatrixPosition(state.mesh.matrixWorld);
      this.normal.set(0,0,1).transformDirection(state.mesh.matrixWorld);
      this.direction.subVectors(this.point,this.viewer);const distance=this.direction.length();
      const facing=this.direction.dot(this.forward);
      if(distance<(entity.getValue(PalaceMirror,'maxDistance')??18)&&this.direction.dot(this.normal)<-.02&&facing>distance*.15&&distance<score){score=distance;best=state;}
      entity.setValue(PalaceMirror,'captures',state.captures);entity.setValue(PalaceMirror,'active',false);
    }
    if(best)best.enabled=true;
    for(const e of this.queries.mirrors.entities){const s=e.object3D&&this.states.get(e.object3D);if(s?.enabled)e.setValue(PalaceMirror,'active',true);}
  }
}
