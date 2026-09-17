import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
import * as core from '@iwsdk/core';
const api={};
vm.runInNewContext(ts.transpileModule(readFileSync('src/hair-particles.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{exports:api,require:()=>core});
const groom=()=>({version:1,points:Array.from({length:9},(_,i)=>[i*.018,0,0]),pointsPerStrand:9,gravity:9.81,damping:.965,shapeStiffness:.015,headCenter:[0,-2,0],headRadii:[.1,.1,.1],shoulderCenter:[0,-3,0],shoulderRadii:[.1,.1,.1]});

test('gravity sags free particles, roots remain pinned and segment lengths stay bounded',()=>{
  const sim=new api.HairParticleSolver(groom());const pose=new core.Matrix4();
  for(let i=0;i<240;i++)sim.update(1/120,pose);
  assert.ok(sim.positions[25]<-.025,'free end falls in world Y');
  assert.ok(sim.maxRootError<1e-7);assert.ok(sim.maxLengthError<.0025,`length error ${sim.maxLengthError}`);
  assert.ok([...sim.positions].every(Number.isFinite));
  const zero=new api.HairParticleSolver({...groom(),gravity:0});
  for(let i=0;i<240;i++)zero.update(1/120,pose);
  assert.ok(Math.abs(zero.positions[25])<1e-6,'no time-based fake sway without gravity or motion');
});

test('fixed substeps agree across frame rates, and world gravity survives head rotation',()=>{
  const a=new api.HairParticleSolver(groom()),b=new api.HairParticleSolver(groom());const pose=new core.Matrix4();
  for(let i=0;i<120;i++)a.update(1/60,pose);
  for(let i=0;i<180;i++)b.update(1/90,pose);
  assert.equal(a.simulatedSteps,b.simulatedSteps);
  assert.ok(a.positions.every((v,i)=>Math.abs(v-b.positions[i])<1e-6));
  const rotated=new api.HairParticleSolver(groom());pose.makeRotationY(Math.PI/2);
  for(let i=0;i<120;i++)rotated.update(1/60,pose);
  assert.ok(rotated.positions[25]<-.025);
});

test('head motion produces inertia, teleport resets safely, avatars do not share particle state',()=>{
  const a=new api.HairParticleSolver(groom()),b=new api.HairParticleSolver(groom());const pose=new core.Matrix4();
  a.update(1/60,pose);b.update(1/60,pose);const untouched=Array.from(b.positions);
  pose.makeTranslation(.12,0,0);a.update(1/120,pose);
  assert.ok(a.maxDeflection>.015);assert.deepEqual(Array.from(b.positions),untouched);
  pose.makeTranslation(10,2,3);a.update(0,pose);
  assert.ok(a.maxRootError<1e-6);assert.ok(a.maxDeflection<1e-5);
});

test('particles are projected out of the head collider',()=>{
  const data=groom();data.points=data.points.map((_,i)=>[.11-i*.008,0,0]);data.headCenter=[0,0,0];data.headRadii=[.1,.1,.1];
  const sim=new api.HairParticleSolver(data);
  for(let i=0;i<60;i++)sim.update(1/120,new core.Matrix4());
  for(let i=2;i<9;i++)assert.ok(Math.hypot(...sim.positions.slice(i*3,i*3+3))>=.0999);
});

test('rendered strand vertices follow physics; clones own their geometry and dispose safely',()=>{
  const data=groom(),geometry=new core.BufferGeometry();
  geometry.setAttribute('position',new core.Float32BufferAttribute(data.points.flat(),3));
  geometry.setAttribute('normal',new core.Float32BufferAttribute(data.points.flatMap(()=>[0,0,1]),3));
  geometry.setAttribute('_hair_particle',new core.Float32BufferAttribute(data.points.map((_,i)=>i),1));
  const material=new core.MeshBasicMaterial();
  function make(){
    const root=new core.Group(),head=new core.Bone();head.name='Head';root.add(head);
    const source=new core.SkinnedMesh(geometry,material);root.add(source);root.updateMatrixWorld(true);
    source.bind(new core.Skeleton([head],[new core.Matrix4()]));source.userData.hairDynamics=data;
    return {source,hair:api.createAvatarHair(root)[0]};
  }
  const a=make(),b=make();let sourceDisposed=false,ownedDisposed=false;
  geometry.addEventListener('dispose',()=>sourceDisposed=true);a.hair.mesh.geometry.addEventListener('dispose',()=>ownedDisposed=true);
  assert.equal(a.source.visible,false);assert.notEqual(a.hair.mesh.geometry,b.hair.mesh.geometry);
  const original=Array.from(b.hair.mesh.geometry.attributes.position.array);
  for(let i=0;i<120;i++)a.hair.update(1/60);
  assert.ok(a.hair.mesh.geometry.attributes.position.getY(8)<-.025);
  assert.deepEqual(Array.from(b.hair.mesh.geometry.attributes.position.array),original);
  assert.equal(geometry.attributes.position.getY(8),0);
  a.hair.dispose();assert.ok(ownedDisposed);assert.equal(sourceDisposed,false);assert.equal(a.source.visible,true);
  assert.equal(a.hair.mesh.parent,null);b.hair.dispose();material.dispose();geometry.dispose();
});

test('exported avatar grooms start outside their interior collider and remain anchored under gravity',()=>{
  for(const asset of ['courtMale','courtFemale']) {
    const file=readFileSync(`public/gltf/avatars/${asset}.glb`);
    const document=JSON.parse(file.subarray(20,20+file.readUInt32LE(12)).toString());
    const grooms=document.nodes.map(n=>n.extras?.hairDynamics).filter(Boolean);
    assert.ok(grooms.length>0);
    for(const data of grooms) {
      const minimum=Math.min(...data.points.map(p=>Math.hypot(...p.map((v,i)=>(v-data.headCenter[i])/data.headRadii[i]))));
      assert.ok(minimum>=1,`${asset}: rest groom intersects its interior collider (${minimum})`);
      const sim=new api.HairParticleSolver(data),pose=new core.Matrix4();
      for(let i=0;i<90;i++)sim.update(1/60,pose);
      assert.equal(sim.maxRootError,0);
      assert.ok(sim.maxLengthError<.003,`${asset}: rest strand stretch ${sim.maxLengthError}`);
      for(let i=1;i<=15;i++) {pose.makeRotationY(i*.025);sim.update(1/72,pose);}
      assert.equal(sim.maxRootError,0);
      assert.ok([...sim.positions].every(Number.isFinite));
      assert.ok(sim.maxLengthError<.008,`${asset}: moving strand stretch ${sim.maxLengthError}`);
    }
  }
});
