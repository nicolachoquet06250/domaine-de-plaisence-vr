import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
import * as core from '@iwsdk/core';
import { Locomotor } from '@iwsdk/locomotor';
const compile=f=>ts.transpileModule(fs.readFileSync(f,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const collision={};vm.runInNewContext(compile('src/scene-assets/static-collision.ts'),{exports:collision,require:()=>core});
const assets={};vm.runInNewContext(compile('src/scene-assets/arrival-boundary.scene-asset.ts'),{exports:assets,require:id=>id==='@iwsdk/core'?core:collision});
test('arrival wall blocks all 360 degrees, including segment seams, without rendering',()=>{
 const wall=assets.default;wall.updateMatrixWorld(true);const ray=new core.Raycaster(),hits=[];
 for(let i=0;i<768;i++) {
  const a=i*2*Math.PI/768;ray.set(new core.Vector3(0,1.6,0),new core.Vector3(Math.sin(a),0,Math.cos(a)));
  hits.length=0;ray.intersectObject(wall,true,hits);assert.ok(hits.length>0,`closed at angle ${a}`);assert.ok(hits[0].distance<8.1);
 }
 wall.traverse(o=>{if(o.isMesh)assert.equal(o.material.visible,false);});
});
test('recovery compensates room-scale headset offset and stays inactive inside the place',()=>{
 const api={},component={};vm.runInNewContext(compile('src/arrival-boundary.ts'),{exports:api,require:id=>id==='@iwsdk/core'?{...core,createSystem:()=>class{}}:{ArrivalBoundary:component}});
 const system=new api.ArrivalBoundarySystem(),root=new core.Group(),scene=new core.Scene();scene.add(root);
 const player=new core.Group(),head=new core.Group();scene.add(player);player.add(head);player.head=head;head.position.set(0,1.7,2);
 const values={radius:8.1,recoveries:0},entity={object3D:root,getValue:(_,k)=>values[k],setValue:(_,k,v)=>values[k]=v,getVectorView:()=>new Float32Array([0,0,2])};
 let target;
 Object.assign(system,{queries:{bounds:{entities:new Set([entity])}},player,camera:head,xrManager:{isPresenting:true},world:{getSystem:()=>({setPlayerPosition:p=>target=p.clone()})}});
 system.update(.016);assert.equal(target,undefined);
 head.position.x=10;system.update(.016);assert.equal(target.x,-10);assert.equal(target.z,0);assert.equal(values.recoveries,1);
 player.position.copy(target);system.update(1);assert.equal(values.recoveries,1,'tracked head is now inside');
 player.position.y=-2;system.update(1);assert.equal(values.recoveries,2);assert.equal(target.y,0);
 system.queries.bounds.entities.clear();system.update(1);assert.equal(values.recoveries,2,'no effect outside arrival');
});

test('actual Locomotor is stopped by the invisible wall in sixteen directions',async()=>{
 const floor=new core.Group();const mesh=new core.Mesh(new core.BoxGeometry(24,.2,24));mesh.position.y=-.1;floor.add(mesh);
 for(let i=0;i<16;i++){
  const engine=new Locomotor({useWorker:false,initialPlayerPosition:new core.Vector3(0,0,0)});
  await engine.initialize();
  try{
   engine.addEnvironment(collision.createStaticCollision(floor));engine.addEnvironment(assets.default.clone(true));
   const angle=i*Math.PI*2/16,direction=new core.Vector3(Math.sin(angle)*2,0,Math.cos(angle)*2);
   for(let frame=0;frame<500;frame++){engine.slide(direction);engine.update(1/90);}
   const r=Math.hypot(engine.position.x,engine.position.z);
   assert.ok(r>7&&r<8,`blocked at radius ${r}, direction ${i}`);assert.ok(engine.position.y>-.1);
  }finally{engine.terminate();}
 }
});
