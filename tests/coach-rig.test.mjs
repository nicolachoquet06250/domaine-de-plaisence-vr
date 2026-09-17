import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const bytes=fs.readFileSync('public/gltf/arrival-coach/royalCoachAnimated.glb');
const jsonLength=bytes.readUInt32LE(12), gltf=JSON.parse(bytes.subarray(20,20+jsonLength)),binOffset=28+jsonLength;
function accessor(id){
 const a=gltf.accessors[id],view=gltf.bufferViews[a.bufferView],size={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT4:16}[a.type];
 const component={5121:[1,'readUInt8',255],5123:[2,'readUInt16LE',65535],5125:[4,'readUInt32LE',4294967295],5126:[4,'readFloatLE',1]}[a.componentType];
 const offset=binOffset+(view.byteOffset??0)+(a.byteOffset??0),stride=view.byteStride??size*component[0];
 return Array.from({length:a.count},(_,i)=>Array.from({length:size},(_,j)=>bytes[component[1]](offset+i*stride+j*component[0])/(a.normalized?component[2]:1)));
}

test('both horses have articulated normalized skin weights on body, hair and hoof meshes',()=>{
 assert.equal(gltf.skins.length,2);
 for(let skin=0;skin<2;skin++){
  const s=gltf.skins[skin];assert.equal(s.joints.length,16);
  const names=s.joints.map(i=>gltf.nodes[i].name);
  for(const part of ['Front','Rear'])for(const side of ['L','R'])for(const segment of ['Upper','Lower','Foot'])assert.ok(names.some(n=>n.startsWith(part+side+segment)));
  const nodes=gltf.nodes.filter(n=>n.skin===skin);assert.equal(nodes.length,2);
  const jointsUsed=new Set();
  for(const n of nodes)for(const p of gltf.meshes[n.mesh].primitives){
   const weights=accessor(p.attributes.WEIGHTS_0),joints=accessor(p.attributes.JOINTS_0);
   assert.equal(weights.length,accessor(p.attributes.POSITION).length);
   weights.forEach((w,i)=>{
    assert.ok(Math.abs(w.reduce((a,b)=>a+b,0)-1)<1e-5);
    w.forEach((v,j)=>{assert.ok(Number.isFinite(v)&&v>=0&&v<=1);if(v>0){assert.ok(joints[i][j]<s.joints.length);jointsUsed.add(joints[i][j]);}});
   });
  }
  assert.equal(jointsUsed.size,16,'all anatomical bones deform real vertices');
 }
});

test('idle and walking clips loop, have finite samples and animate both horses without moving the coach root',()=>{
 assert.deepEqual(gltf.animations.map(a=>a.name).sort(),['HorseIdle','HorseWalk']);
 for(const animation of gltf.animations){
  const targets=new Set(animation.channels.map(c=>c.target.node));
  for(const skin of gltf.skins)assert.ok(skin.joints.every(j=>targets.has(j)));
  assert.ok([...targets].every(j=>gltf.skins.some(s=>s.joints.includes(j))));
  const duration=animation.name==='HorseIdle'?3:1.2;
  let moving=0;
  for(const channel of animation.channels){
   const sampler=animation.samplers[channel.sampler],times=accessor(sampler.input).flat(),values=accessor(sampler.output);
   assert.ok(Math.abs(times.at(-1)-duration)<1e-6);
   assert.ok(times.every((t,i)=>Number.isFinite(t)&&(i===0||t>times[i-1])));
   assert.ok(values.flat().every(Number.isFinite));
   const first=values[0],last=values.at(-1);
   const error=channel.target.path==='rotation'?1-Math.abs(first.reduce((sum,v,i)=>sum+v*last[i],0)):Math.max(...first.map((v,i)=>Math.abs(v-last[i])));
   assert.ok(error<.0001,'continuous loop seam');
   if(values.some(v=>v.some((component,i)=>Math.abs(component-first[i])>.005)))moving++;
  }
  assert.ok(moving>2);
 }
});

test('four independent wheels have centred local pivots and the coach remains mobile-budget bounded',()=>{
 for(const axle of ['Front','Rear'])for(const side of ['L','R']){
  const node=gltf.nodes.find(n=>n.name===`Wheel${axle}${side}`);assert.ok(node);
  const radius=axle==='Rear'?.76:.59;assert.ok(Math.abs(node.translation[1]-radius)<1e-6);
  const positions=gltf.meshes[node.mesh].primitives.flatMap(p=>accessor(p.attributes.POSITION));
  for(const axis of [0,1]){
   const low=Math.min(...positions.map(p=>p[axis])),high=Math.max(...positions.map(p=>p[axis]));
   assert.ok(Math.abs(low+high)<.008,'wheel geometry centred on axle');
   assert.ok(high>radius-.03&&high<radius+.05);
  }
 }
 const count=gltf.meshes.reduce((sum,m)=>sum+m.primitives.reduce((s,p)=>s+gltf.accessors[p.indices].count/3,0),0);
 assert.ok(count<70000);assert.ok(bytes.length<4000000);
 assert.ok(gltf.images.every(i=>!i.uri));assert.ok(gltf.buffers.every(b=>!b.uri));
});

test('evaluated Blender hoof motion stays grounded, lifts gently, and loops without snapping',()=>{
 const check=JSON.parse(fs.readFileSync('artifacts/coach-journey-rig/deformation-check.json','utf8'));
 assert.equal(check.horses.length,2);
 for(const horse of check.horses){
  assert.ok(horse.minimumHoofY>-.002);assert.ok(horse.maximumHoofLift>.10&&horse.maximumHoofLift<.15);
  for(const name of Object.keys(horse.samples[0])){
   const feet=horse.samples.map(row=>row[name]);
   assert.ok(Math.max(...feet.map(f=>f.meanX))-Math.min(...feet.map(f=>f.meanX))>.70);
   assert.ok(feet.filter(f=>f.minY<.015).length>=18,'most of each gait cycle bears weight');
   assert.ok(Math.abs(feet[0].meanX-feet.at(-1).meanX)<.0001);
   assert.ok(Math.abs(feet[0].minY-feet.at(-1).minY)<.0001);
  }
 }
});
