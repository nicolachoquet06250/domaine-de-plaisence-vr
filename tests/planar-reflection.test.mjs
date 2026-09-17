import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
import * as core from '@iwsdk/core';
const api={};vm.runInNewContext(ts.transpileModule(readFileSync('src/planar-reflection.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{exports:api,require:()=>core});

test('mirror portal fills the texture, preserves eye separation and clips the rear room',()=>{
  const surface=new core.Mesh(new core.PlaneGeometry(1,1));surface.position.set(2,1,-3);surface.rotation.y=.4;surface.updateMatrixWorld();
  const normal=new core.Vector3(0,0,1).transformDirection(surface.matrixWorld),point=surface.position;
  const camera=new core.PerspectiveCamera(70,1,.05,100);camera.position.copy(point).addScaledVector(normal,2);camera.lookAt(point);camera.updateMatrixWorld();
  camera.projectionMatrix.elements[8]=.07;
  const reflection=new api.ReflectionCamera();assert.equal(reflection.update(surface,camera),true);
  assert.ok(reflection.camera.position.distanceTo(point.clone().addScaledVector(normal,-2))<1e-6);
  for(const x of [-.5,.5])for(const y of [-.5,.5]) {
    const corner=new core.Vector3(x,y,0).applyMatrix4(surface.matrixWorld).project(reflection.camera);
    assert.ok(Math.abs(Math.abs(corner.x)-1)<1e-6,'horizontal edge fills texture');
    assert.ok(Math.abs(Math.abs(corner.y)-1)<1e-6,'vertical edge fills texture');
  }
  const stable=reflection.textureMatrix.clone();camera.rotation.z=.2;camera.updateMatrixWorld();reflection.update(surface,camera);
  assert.deepEqual(reflection.textureMatrix.elements,stable.elements,'head rotation cannot move a fixed world reflection');
  const front=point.clone().addScaledVector(normal,.3).project(reflection.camera);
  const behind=point.clone().addScaledVector(normal,-.3).project(reflection.camera);
  assert.ok(front.z>-1&&front.z<1,'objects in front of the glass are retained');
  assert.ok(behind.z< -1,'objects behind the glass are clipped');
  const first=reflection.camera.position.clone();camera.position.x+=.064;camera.updateMatrixWorld();reflection.update(surface,camera);
  assert.ok(Math.abs(first.distanceTo(reflection.camera.position)-.064)<1e-6,'eye separation is preserved');
  camera.position.copy(point).addScaledVector(normal,-1);camera.updateMatrixWorld();assert.equal(reflection.update(surface,camera),false);
});

test('independent eye targets restore renderer and mirror state even when rendering throws',()=>{
  const mesh=new core.Mesh(new core.PlaneGeometry(1,1),new core.MeshBasicMaterial());mesh.updateMatrixWorld();
  const original=mesh.material,mirror=new api.PlanarReflection(mesh),camera=new core.PerspectiveCamera();camera.position.z=2;camera.updateMatrixWorld();mirror.enabled=true;
  let restores=0,activeTarget=null,viewport=new core.Vector4(1,2,800,600),scissor=viewport.clone(),testEnabled=true,depthWritable=false;
  const renderer={xr:{enabled:true},shadowMap:{autoUpdate:true},state:{buffers:{depth:{setMask:v=>depthWritable=v}}},getRenderTarget:()=>activeTarget,getActiveCubeFace:()=>0,getActiveMipmapLevel:()=>0,getScissorTest:()=>testEnabled,getViewport:v=>v.copy(viewport),getScissor:v=>v.copy(scissor),setViewport:v=>viewport.copy(v),setScissor:v=>scissor.copy(v),setScissorTest:v=>testEnabled=v,setRenderTarget:t=>activeTarget=t,clear(){assert.equal(depthWritable,true,'each capture clears depth even after transparent flames');},render(){depthWritable=false;throw Error('render failure');}};
  assert.throws(()=>mirror.capture(renderer,new core.Scene(),camera,1,()=>{},()=>restores++),/render failure/);
  assert.equal(restores,1);assert.equal(renderer.xr.enabled,true);assert.equal(renderer.shadowMap.autoUpdate,true);assert.equal(activeTarget,null);assert.equal(testEnabled,true);
  const right=camera.clone();right.position.x=.064;right.updateMatrixWorld();
  const stereo=new core.ArrayCamera([camera,right]);
  renderer.render=()=>{depthWritable=false;};mirror.capture(renderer,new core.Scene(),stereo,1,()=>{},()=>{});
  assert.equal(mirror.captures,2);assert.notEqual(mirror.targets[0].texture,mirror.targets[1].texture);
  mirror.capture(renderer,new core.Scene(),stereo,1,()=>{},()=>{});assert.equal(mirror.captures,2,'one capture per eye/frame');
  assert.notDeepEqual(mirror.matrices[0].elements,mirror.matrices[1].elements,'multiview must not reflect from the combined culling camera');
  mirror.bindEye(0);
  assert.equal(mirror.material.uniforms.reflection.value,mirror.targets[0].texture);
  assert.equal(mirror.material.uniforms.reflectionRight.value,mirror.targets[1].texture);
  assert.equal(mirror.material.uniforms.readyRight.value,1);
  mirror.bindEye(1);
  assert.equal(mirror.material.uniforms.reflection.value,mirror.targets[1].texture,'sequential stereo still binds the right eye');
  let mirrorFrame=1;
  for(const distance of [2,.5,.08,.5,2]){
    camera.position.z=right.position.z=distance;camera.updateMatrixWorld();right.updateMatrixWorld();
    mirror.capture(renderer,new core.Scene(),stereo,++mirrorFrame,()=>{},()=>{});
    assert.ok(mirror.matrices.every(m=>m.elements.every(Number.isFinite)));
  }
  let released=0;for(const target of mirror.targets)target.addEventListener('dispose',()=>released++);
  mirror.dispose();assert.equal(mesh.material,original);assert.equal(released,2);
});

test('mirror captures finish before the XR draw pass and never interrupt flame or glass drawing',()=>{
  const systemApi={};
  vm.runInNewContext(ts.transpileModule(readFileSync('src/palace-mirrors.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{
    exports:systemApi,require:id=>id==='@iwsdk/core'?{...core,createSystem:()=>class{}}:id.includes('planar-reflection')?api:{},
  });
  const scene=new core.Scene(),root=new core.Group(),mesh=new core.Mesh(new core.PlaneGeometry(1,1),new core.MeshBasicMaterial());
  root.add(mesh);scene.add(root);scene.updateMatrixWorld();
  const glass=new core.Mesh(new core.PlaneGeometry(1,1),new core.MeshPhysicalMaterial({transmission:1}));
  const originalGlass=glass.material;scene.add(glass);
  const values={maxDistance:18,captures:0,active:false};
  const entity={object3D:root,getValue:(_,key)=>values[key],setValue:(_,key,v)=>values[key]=v};
  const camera=new core.PerspectiveCamera(70,1,.05,220);camera.position.z=.15;camera.updateMatrixWorld();
  const right=camera.clone();right.position.x=.064;right.updateMatrixWorld();
  const stereo=new core.ArrayCamera([camera,right]);
  const system=new systemApi.PalaceMirrorSystem();
  Object.assign(system,{scene,camera,player:{head:camera},xrManager:{isPresenting:true},queries:{mirrors:{entities:new Set([entity]),subscribe:()=>()=>{}}},cleanupFuncs:[]});
  let captures=0,phase='before-main',target={isWebGLMultiviewRenderTarget:true},depthWritable=false,originalCalls=0;
  const original=()=>originalCalls++;scene.onBeforeRender=original;
  const renderer={xr:{enabled:true,isPresenting:true,getCamera:()=>stereo},shadowMap:{autoUpdate:true},state:{buffers:{depth:{setMask:v=>depthWritable=v}}},getRenderTarget:()=>target,getActiveCubeFace:()=>0,getActiveMipmapLevel:()=>0,getScissorTest:()=>false,getViewport:v=>v.set(0,0,1024,1024),getScissor:v=>v.set(0,0,1024,1024),setViewport(){},setScissor(){},setScissorTest(){},setRenderTarget:t=>target=t,clear(){assert.equal(depthWritable,true);},render(s,c){
    assert.equal(phase,'before-main','no reflection render from inside a main draw callback');
    assert.equal(mesh.visible,false,'no recursion or mirror feedback');
    assert.equal(glass.material.transmission,0,'reflection cannot trigger another glass transmission scene pass');
    assert.equal(originalGlass.transmission,1,'shared main-view material is immutable');
    assert.equal(this.xr.enabled,false);assert.equal(c.isArrayCamera,undefined);
    captures++;s.onBeforeRender(this,s,c,target);depthWritable=false;
  }};
  system.init();system.update();scene.onBeforeRender(renderer,scene,stereo,target);
  assert.equal(captures,2);assert.equal(mesh.visible,true);assert.equal(renderer.xr.enabled,true);assert.equal(target.isWebGLMultiviewRenderTarget,true);
  assert.equal(glass.material,originalGlass,'main view restores full glass material');
  phase='main-draw';mesh.onBeforeRender(renderer,scene,stereo);mesh.onBeforeRender(renderer,scene,camera);mesh.onBeforeRender(renderer,scene,right);
  assert.equal(captures,2,'main stereo, flame and transmission passes cannot trigger more captures');
  assert.equal(originalCalls,3,'existing scene hook remains chained');
  system.cleanupFuncs.forEach(fn=>fn());assert.equal(scene.onBeforeRender,original);
});
