import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
import * as core from '@iwsdk/core';
const api={};
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/portal-direction.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{exports:api,console,require:id=>id==='@iwsdk/core'?{...core,createSystem:()=>class{}}:{}});

test('camera-local left/right remains correct in front and behind, with stable central dead zones',()=>{
 const side=(x,z,previous=0)=>api.portalDirectionSide(new core.Vector3(x,0,z),previous);
 assert.equal(side(4,-2),1);assert.equal(side(-4,-2),-1);
 assert.equal(side(4,2),1);assert.equal(side(-4,2),-1);
 assert.equal(side(0,-5),0);assert.equal(side(.02,5,-1),-1);assert.equal(side(-.02,5,1),1);
 assert.equal(side(.6,-5,0),0);assert.equal(side(.6,-5,1),1,'hysteresis avoids flickering at the front threshold');
 assert.equal(side(.1,-.2,1),0,'hide very close to the portal');
});

test('hint follows actual camera rotation and position, animates, and disappears when unavailable or boarding',()=>{
 const system=new api.PortalDirectionSystem(),camera=new core.PerspectiveCamera(60,1.5,.1,200),head=new core.Group(),portal=new core.Group(),hint=new core.Group();
 camera.position.set(0,1.65,2);head.position.set(0,1.65,2);portal.position.set(7.15,0,0);
 const state={phase:'arrival',identityReady:true},hintState={side:0};
 Object.assign(system,{camera,player:{head},xrManager:{isPresenting:false},visibilityState:{peek:()=>core.VisibilityState.NonImmersive},queries:{journeys:{entities:[{getValue:(_,k)=>state[k]}]},portals:{entities:[{object3D:portal,getValue:()=> 'castle'}]},hints:{entities:[{object3D:hint,getValue:(_,k)=>hintState[k],setValue:(_,k,v)=>hintState[k]=v}]}}});
 system.update(.05);assert.equal(hintState.side,1);assert.equal(hint.visible,true);
 const first=hint.position.clone();system.update(.05);assert.ok(hint.position.distanceTo(first)>.0001,'gentle side animation');
 camera.rotation.y=Math.PI;system.update(.05);assert.equal(hintState.side,-1,'turning changes the side in camera space');
 const local=hint.position.clone().sub(camera.position).applyQuaternion(camera.quaternion.clone().invert());assert.ok(local.x<0&&Math.abs(local.z+1.7)<1e-6);
 camera.lookAt(7.15,1.65,0);system.update(.05);assert.equal(hint.visible,false,'portal straight ahead');
 camera.rotation.set(0,0,0);portal.visible=false;system.update(.05);assert.equal(hint.visible,false,'wait for actual portal availability');
 portal.visible=true;state.identityReady=false;system.update(.05);assert.equal(hint.visible,false);
 state.identityReady=true;state.phase='outbound';system.update(.05);assert.equal(hint.visible,false);
 state.phase='arrival';camera.position.x=10;system.update(.05);assert.equal(hint.visible,false,'only inside the circle');
 system.xrManager.isPresenting=true;head.rotation.y=Math.PI;system.update(.05);assert.equal(hintState.side,-1,'XR uses tracked head instead of desktop camera');
 const xrLocal=hint.position.clone().sub(head.position).applyQuaternion(head.quaternion.clone().invert());assert.ok(xrLocal.x<0&&Math.abs(xrLocal.z+1.7)<1e-6);
});
