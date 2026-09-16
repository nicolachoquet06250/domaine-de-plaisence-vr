import assert from 'node:assert/strict';
import { readFileSync,writeFileSync } from 'node:fs';
import ts from 'typescript';
import { Raycaster,Vector3 } from '@iwsdk/core';
import { Locomotor } from '@iwsdk/locomotor';
const report={assets:{},checks:[]};
for(const id of ['palace','palaceInterior','palaceGlass','palaceDoor']){
  const data=readFileSync(`public/gltf/castle/${id}.glb`),length=data.readUInt32LE(12);
  const gltf=JSON.parse(data.subarray(20,20+length)),bin=data.subarray(28+length);
  assert.equal(data.readUInt32LE(0),0x46546c67);
  assert.ok(gltf.buffers.every(b=>!b.uri));assert.ok((gltf.images??[]).every(i=>i.bufferView!==undefined));
  const triangles=gltf.meshes.reduce((n,m)=>n+m.primitives.reduce((n,p)=>n+gltf.accessors[p.indices].count/3,0),0);
  assert.ok(triangles<100000 && data.length<5_000_000);
  if(id==='palaceGlass'){
    assert.ok(gltf.materials.every(m=>m.alphaMode==='BLEND' && m.pbrMetallicRoughness.baseColorFactor[3]<.3 && m.pbrMetallicRoughness.roughnessFactor<.1));
    report.checks.push('transparent low-roughness glazing');
  }
  if(id==='palaceDoor'){
    const rotations=gltf.animations.flatMap(a=>a.channels.filter(c=>c.target.path==='rotation').map(c=>({animation:a,channel:c})));
    assert.equal(rotations.length,2);
    for(const {animation,channel} of rotations){
      const sampler=animation.samplers[channel.sampler],acc=gltf.accessors[sampler.output],view=gltf.bufferViews[acc.bufferView];
      const offset=(view.byteOffset??0)+(acc.byteOffset??0);
      const first=Array.from({length:4},(_,i)=>bin.readFloatLE(offset+i*4));
      const last=Array.from({length:4},(_,i)=>bin.readFloatLE(offset+(acc.count-1)*16+i*4));
      const angle=2*Math.acos(Math.abs(first.reduce((n,v,i)=>n+v*last[i],0)))*180/Math.PI;
      assert.ok(Math.abs(angle-105)<.05,'authored hinge swings 105 degrees');
    }
    report.checks.push('two Blender hinge clips, each 105 degrees');
  }
  report.assets[id]={bytes:data.length,triangles,drawCalls:gltf.meshes.reduce((n,m)=>n+m.primitives.length,0)};
}
let source=readFileSync('src/scene-assets/palace-collision.scene-asset.ts','utf8');
source=source.replace("import solids from './castle-collision-data.json';",`const solids=${readFileSync('src/scene-assets/castle-collision-data.json','utf8')};`);
const url=new URL('../artifacts/castle/collision-proxy.mjs',import.meta.url);
writeFileSync(url,ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText);
const {default:root}=await import(url.href);root.updateMatrixWorld(true);
function hit(x,y,z,dx,dy,dz,far=100){return new Raycaster(new Vector3(x,y,z),new Vector3(dx,dy,dz),0,far).intersectObject(root,true)[0];}
assert.ok(!hit(0,2.1,9.6,0,0,-1,4.1),'entrance stays hollow');
for(const y of [2.2,6.65])for(const x of [-4.65,4.65])assert.ok(!hit(x-.45,y,3.8,1,0,0,.9),'salon opening stays hollow');
for(const floor of [.64,5.04])for(const x of [-4.65,4.65])for(const dy of [.3,1.7,3.3]){
  for(const z of [1.95,2.04,2.18,5.42,5.48])assert.ok(hit(x-.45,floor+dy,z,1,0,0,.9),'door wall joins frame without a slit');
  for(const z of [2.3,3.8,5.3])assert.ok(!hit(x-.45,floor+dy,z,1,0,0,.9),'clear interior doorway width');
}
report.checks.push('60 wall-to-door seam probes and 36 clear opening probes');
const solids=JSON.parse(readFileSync('src/scene-assets/castle-collision-data.json'));
for(const ramp of solids.filter(s=>s.kind==='ramp'))for(let i=0;i<=20;i++){
  const t=i/20,x=ramp.from[0],y=ramp.from[1]*(1-t)+ramp.to[1]*t,z=ramp.from[2]*(1-t)+ramp.to[2]*t;
  const sample=hit(x,y+.09,z,0,-1,0,.3);
  assert.ok(sample && Math.abs(sample.point.y-y)<.025,`continuous stair support at ${x},${y},${z}`);
  assert.ok(sample.face.normal.y>.8,'outward walkable slope');
}
assert.ok(hit(5.7,2.1,7,0,0,-1,1.5),'windows block passage');
for(const x of [-8,8])assert.ok(Math.abs(hit(x,5.2,3.8,0,-1,0,.5).point.y-5.04)<1e-5,'upper salon floor');
report.checks.push('entrance and four salon openings clear','63 stair support samples','upper floors supported','window collision');
for(const x of [-3.8,0,3.8]){
  const lower=hit(x,2.93,-5.75,0,-1,0,.4);
  assert.ok(lower && Math.abs(lower.point.y-2.84)<1e-5,'intermediate landing reaches the rear wall');
  const upper=hit(x,5.15,-5.75,0,-1,0,.4);
  assert.ok(!upper,'inaccessible rear upper slab and its collision are removed');
}
for(const x of [-3.15,3.15]){
  assert.ok(!hit(x-.70,1.8,0,1,0,0,1.4),'open space below return flight, between columns');
  assert.ok(hit(x-.70,1.8,1.05,1,0,0,1.4),'support column blocks passage');
}
report.checks.push('intermediate landing joins wall; inaccessible upper slab removed','return stairs have a traversable underside with solid support columns');
// Exercise the real locomotion capsule/BVH, not only point rays, around the turn.
const locomotor=new Locomotor({useWorker:false,initialPlayerPosition:new Vector3(0,.65,4.3)});
await locomotor.initialize();locomotor.addEnvironment(root);
const route=[];
for(const [x,z] of [[0,-3.05],[3.15,-3.05],[3.15,3.8],[7,3.8]]){
  let reached=false;
  for(let frame=0;frame<1800;frame++){
    const dx=x-locomotor.position.x,dz=z-locomotor.position.z,dist=Math.hypot(dx,dz);
    if(dist<.07){reached=true;break;}
    locomotor.slide(new Vector3(dx/dist*1.6,0,dz/dist*1.6));locomotor.update(1/72);
  }
  route.push(locomotor.position.toArray());
  assert.ok(reached,`capsule reaches stair waypoint ${x},${z}: ${locomotor.position.toArray()}`);
}
assert.ok(Math.abs(locomotor.position.y-5.04)<.12,'capsule climbs to the upper salon');
locomotor.terminate();report.route=route;report.checks.push('real locomotion capsule climbs both flights and turns into upper salon');
const before=JSON.parse(readFileSync('artifacts/castle/scene-before.json'));
const after=JSON.parse(readFileSync('public/scenes/plaisance.iwsdk.scene.json'));
assert.deepEqual(after.nodes.filter(n=>n.id!=='castle'),before.nodes.filter(n=>n.id!=='castle'));
assert.deepEqual(after.player,before.player);
report.checks.push('garden, fountain and player spawn preserved');
writeFileSync('artifacts/castle/verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
