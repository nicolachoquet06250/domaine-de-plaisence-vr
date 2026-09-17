import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
import * as core from '@iwsdk/core';

const source = ts.transpileModule(readFileSync(new URL('../src/court-avatar.ts', import.meta.url),'utf8'), {
  compilerOptions: {module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022},
}).outputText;
const ik = {};
const reflections = {};
const speech = {};
const hair = {};
vm.runInNewContext(ts.transpileModule(readFileSync('src/hair-particles.ts','utf8'), {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{exports:hair,require:()=>core});
vm.runInNewContext(ts.transpileModule(readFileSync('src/speech-visemes.ts','utf8').replaceAll('import.meta.env.BASE_URL','"/"'), {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{exports:speech});
vm.runInNewContext(ts.transpileModule(readFileSync(new URL('../src/planar-reflection.ts', import.meta.url),'utf8'), {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{exports:reflections,require:()=>core});
vm.runInNewContext(ts.transpileModule(readFileSync(new URL('../src/court-avatar-ik.ts', import.meta.url),'utf8'), {
  compilerOptions: {module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022},
}).outputText, {exports: ik, require:()=>core});

function fixture() {
  const pending = [], models = [];
  const geometry = new core.BufferGeometry();
  const material = new core.MeshBasicMaterial();
  let geometryDisposals = 0, materialDisposals = 0, skeletonDisposals = 0;
  geometry.addEventListener('dispose',()=>geometryDisposals++);
  material.addEventListener('dispose',()=>materialDisposals++);
  const exports = {};
  const assets = {
    loadGLTFById: id => new Promise((resolve,reject)=>pending.push({id,resolve,reject})),
    getGLTF(id) {
      const scene = new core.Group(), bone = new core.Bone(); bone.name='Spine';
      const mesh = new core.SkinnedMesh(geometry, material); mesh.name='Head';
      mesh.morphTargetDictionary=Object.fromEntries(speech.VISEME_NAMES.map((name,i)=>[name,i]));
      mesh.morphTargetInfluences=new Array(15).fill(0);
      mesh.add(bone);scene.add(mesh);
      const body = new core.Mesh(geometry, material); body.name='Coat'; body.layers.enable(7); scene.add(body);
      const skeleton = new core.Skeleton([bone]); mesh.bind(skeleton);
      const dispose = skeleton.dispose.bind(skeleton);
      skeleton.dispose=()=>{skeletonDisposals++;dispose();};
      models.push({id, scene, bone, mesh, body});
      return {scene,animations:[
        new core.AnimationClip('Idle',1,[new core.NumberKeyframeTrack('Spine.rotation[x]',[0,1],[0,0])]),
        new core.AnimationClip('Walking',1,[new core.NumberKeyframeTrack('Spine.rotation[x]',[0,.5,1],[0,1,0])]),
        new core.AnimationClip('StrafeLeft',1,[new core.NumberKeyframeTrack('Spine.rotation[z]',[0,.5,1],[0,.6,0])]),
        new core.AnimationClip('StrafeRight',1,[new core.NumberKeyframeTrack('Spine.rotation[z]',[0,.5,1],[0,-.6,0])]),
      ]};
    },
  };
  vm.runInNewContext(source, {exports,require:id=>id.includes('hair-particles') ? hair : id.includes('speech-visemes') ? speech : id.includes('court-avatar-ik') ? ik : id.includes('planar-reflection') ? reflections : ({...core,AssetManager:assets})});
  return {api:exports,pending,models,resources:()=>({geometryDisposals,materialDisposals,skeletonDisposals})};
}

test('first-person head stays available to mirrors while hidden from both direct eye cameras',async()=>{
  const h=fixture(),root=new core.Group();const loading=h.api.setCourtAvatar(root,'female',true);h.pending.shift().resolve();await loading;
  const head=h.models[0].mesh;assert.equal(head.visible,true);
  for(const mask of [1,3,5]){const camera=new core.Camera();camera.layers.mask=mask;assert.equal(camera.layers.test(head.layers),false);camera.layers.enable(reflections.REFLECTION_ONLY_LAYER);assert.equal(camera.layers.test(head.layers),true);}
  h.api.releaseCourtAvatar(root);
});

test('desktop reflection-only view survives loading and restores the VR body layers on repeated switches',async()=>{
  const h=fixture(),root=new core.Group();
  const loading=h.api.setCourtAvatar(root,'female',true);
  h.api.setCourtAvatarView(root,'reflection-only');
  h.pending.shift().resolve();await loading;
  const {mesh:head,body,bone}=h.models[0];
  const reflection=new core.Camera();reflection.layers.enable(reflections.REFLECTION_ONLY_LAYER);
  for(let i=0;i<3;i++){
    h.api.setCourtAvatarView(root,'reflection-only');
    for(const mask of [1,3,5]){
      const direct=new core.Camera();direct.layers.mask=mask;
      for(const mesh of [head,body]){
        assert.equal(mesh.visible,true);
        assert.equal(direct.layers.test(mesh.layers),false);
        assert.equal(reflection.layers.test(mesh.layers),true);
      }
    }
    let minimum=Infinity,maximum=-Infinity;
    for(let frame=0;frame<24;frame++){
      h.api.animateCourtAvatar(root,1/72,1.35);
      minimum=Math.min(minimum,bone.rotation.x);maximum=Math.max(maximum,bone.rotation.x);
    }
    assert.ok(maximum-minimum>.1,'reflection-only skeleton still animates');
    h.api.setCourtAvatarView(root,'first-person');
    assert.equal(body.layers.mask,1 | 1<<7,'custom body layers restored');
    assert.equal(head.layers.mask,1<<reflections.REFLECTION_ONLY_LAYER);
  }
});

test('local body follows the desktop camera and remains reflected across XR entry and exit',async()=>{
  const h=fixture(),root=new core.Group(), exports={};
  const multiplayerSource=readFileSync(new URL('../src/multiplayer.ts',import.meta.url),'utf8').replaceAll('import.meta.env.BASE_URL','"/"');
  vm.runInNewContext(ts.transpileModule(multiplayerSource,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{
    exports,require:id=>id==='@iwsdk/core'?{...core,createSystem:()=>class{}}:id.includes('court-avatar.js')?h.api:{},
  });
  const system=new exports.MultiplayerSystem();
  const player=new core.Group(), camera=new core.PerspectiveCamera(),head=new core.Object3D();
  player.position.set(7,5.04,-31);player.head=head;player.add(head,camera);
  camera.position.y=1.65;head.position.y=1.8;
  Object.assign(system,{voice:{localVisemes(){}},localBody:{object3D:root},room:'test',participant:true,avatarGender:'female',player,camera,xrManager:{isPresenting:false},world:{xrSession:null},connection:{setValue(){},getVectorView(){return new Float32Array(3);}}});
  const loading=h.api.setCourtAvatar(root,'female',true);h.pending.shift().resolve();await loading;
  for(const immersive of [false,true,false]){
    system.xrManager.isPresenting=immersive;system.updateLocalBody(1/72);
    assert.equal(root.visible,true,'local model must never be globally hidden while visiting');
    assert.ok(Math.abs(root.scale.x*1.649*.95-(immersive?1.8:1.65))<1e-6,'calibrate from the active viewer');
    assert.ok(Math.abs(root.position.y-5.04)<1e-6);
    assert.equal(h.models[0].body.layers.mask,immersive?1|1<<7:1<<reflections.REFLECTION_ONLY_LAYER);
    assert.equal(h.api.courtAvatarDiagnostics(root).mode,'Idle','switching view is not walking');
  }
  camera.position.x=.02;system.updateLocalBody(1/72);
  assert.equal(h.api.courtAvatarDiagnostics(root).mode,'StrafeRight');
  system.participant=false;system.updateLocalBody(1/72);assert.equal(root.visible,false,'observer has a reserved room but no local body');
  system.room='';system.updateLocalBody(1/72);assert.equal(root.visible,false,'leaving hides the local model');
});

test('independent mixers blend Idle/Walking, then return to rest without mutating other avatars',async()=>{
  const h=fixture(), one=new core.Group(),two=new core.Group();
  const first=h.api.setCourtAvatar(one,'male');h.pending.shift().resolve();await first;
  const second=h.api.setCourtAvatar(two,'female');h.pending.shift().resolve();await second;
  assert.deepEqual(h.models.map(m=>m.id),['courtMale','courtFemale']);
  assert.notEqual(h.models[0].mesh.skeleton,h.models[1].mesh.skeleton);
  for(let i=0;i<24;i++) {h.api.animateCourtAvatar(one,1/72,1.35);h.api.animateCourtAvatar(two,1/72,0);}
  assert.ok(h.models[0].bone.rotation.x > .45,'walking advances the actual bone track');
  assert.equal(h.models[1].bone.rotation.x,0,'other avatar remains idle');
  for(let i=0;i<144;i++)h.api.animateCourtAvatar(one,1/72,0);
  assert.ok(Math.abs(h.models[0].bone.rotation.x)<.001,'stopping blends back to idle');
  h.api.releaseCourtAvatar(one);assert.equal(one.children.length,0);
  assert.deepEqual(h.resources(),{geometryDisposals:0,materialDisposals:0,skeletonDisposals:1});
  assert.equal(two.children.length,1,'removing one avatar leaves its peer intact');
});

test('strafing follows local anatomical left/right and preserves the body yaw', async()=>{
  const h=fixture(),root=new core.Group();root.rotation.y=Math.PI/2;
  const loading=h.api.setCourtAvatar(root,'male');h.pending.shift().resolve();await loading;
  const initial=root.quaternion.clone();
  const motion={velocity:new core.Vector3(0,0,-1.35),left:{tracked:false},right:{tracked:false}};
  for(let i=0;i<24;i++)h.api.animateCourtAvatar(root,1/72,0,motion);
  assert.equal(h.api.courtAvatarDiagnostics(root).mode,'StrafeLeft');
  assert.ok(h.models[0].bone.rotation.z>.2);
  assert.ok(root.quaternion.equals(initial),'strafing never rotates body');
  motion.velocity.set(0,0,1.35);
  for(let i=0;i<100;i++)h.api.animateCourtAvatar(root,1/72,0,motion);
  assert.equal(h.api.courtAvatarDiagnostics(root).mode,'StrafeRight');
  assert.ok(h.models[0].bone.rotation.z<-.1);
  motion.velocity.set(0,0,0);
  for(let i=0;i<144;i++)h.api.animateCourtAvatar(root,1/72,0,motion);
  assert.equal(h.api.courtAvatarDiagnostics(root).mode,'Idle');
  assert.ok(Math.abs(h.models[0].bone.rotation.z)<.001);
});

test('changing identity during load and leaving before completion cannot resurrect obsolete avatars',async()=>{
  const h=fixture(),root=new core.Group();
  const male=h.api.setCourtAvatar(root,'male');
  const female=h.api.setCourtAvatar(root,'female');
  h.pending[1].resolve();await female;
  h.pending[0].resolve();await male;
  assert.deepEqual(h.models.map(m=>m.id),['courtFemale']);assert.equal(root.children.length,1);
  const reselect=h.api.setCourtAvatar(root,'male');h.api.releaseCourtAvatar(root);
  h.pending[2].resolve();await reselect;assert.equal(root.children.length,0);
  const cancelled=h.api.setCourtAvatar(root,'female');h.api.releaseCourtAvatar(root);
  h.pending[3].reject(Error('obsolete request'));await cancelled;
  const failed=h.api.setCourtAvatar(root,'male');h.pending[4].reject(Error('offline'));
  await assert.rejects(failed,/offline/);
});

test('mouth morphs are independent per visitor and combine with walking and reflection layers',async()=>{
  const h=fixture(),one=new core.Group(),two=new core.Group();
  const a=h.api.setCourtAvatar(one,'male',true);h.pending.shift().resolve();await a;
  const b=h.api.setCourtAvatar(two,'female');h.pending.shift().resolve();await b;
  const weights=new Float32Array(15);weights[0]=.6;weights[3]=.2;
  h.api.setCourtAvatarView(one,'reflection-only');
  h.api.animateCourtAvatar(one,.016,1.35);h.api.animateCourtMouth(one,weights);
  assert.equal(h.models[0].mesh.morphTargetInfluences[0],weights[0]);
  assert.equal(h.models[1].mesh.morphTargetInfluences[0],0);
  assert.equal(h.models[0].mesh.layers.mask,1<<reflections.REFLECTION_ONLY_LAYER);
  h.api.animateCourtMouth(one);assert.ok(h.models[0].mesh.morphTargetInfluences.every(n=>n===0));
});
