import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
function glb(name){
 const bytes=fs.readFileSync(name),length=bytes.readUInt32LE(12),json=JSON.parse(bytes.subarray(20,20+length)),bin=28+length;
 function points(primitive){
  const a=json.accessors[primitive.attributes.POSITION],v=json.bufferViews[a.bufferView],result=[];
  for(let i=0;i<a.count;i++)result.push([0,1,2].map(c=>bytes.readFloatLE(bin+(v.byteOffset??0)+(a.byteOffset??0)+i*(v.byteStride??12)+c*4)));
  return result;
 }
 return {json,points};
}
const scene=read('public/scenes/arrival.iwsdk.scene.json'),stats=read('artifacts/arrival-coach/model-stats.json');
const coach=glb('public/gltf/arrival-coach/royalCoach.glb'),wicket=glb('public/gltf/arrival-coach/wicket.glb');

test('Blender opening removes the east balustrade while preserving terrace floor and other furnishings',()=>{
 const old=glb('public/gltf/arrival/arrival.glb'),now=glb('public/gltf/arrival-coach/arrival.glb');
 for(const prefix of ['01','03','04','05']){
  const coordinates=asset=>asset.json.nodes.filter(n=>n.name.startsWith(prefix)).flatMap(n=>asset.json.meshes[n.mesh].primitives.flatMap(p=>asset.points(p).map(point=>point.join(',')))).sort();
  assert.deepEqual(coordinates(now),coordinates(old),`original group ${prefix}`);
 }
 const vertices=now.json.nodes.filter(n=>n.name.startsWith('02')).flatMap(n=>now.json.meshes[n.mesh].primitives.flatMap(now.points));
 assert.ok(!vertices.some(([x,y,z])=>x>7.3&&y>.15&&Math.abs(z)<1.1),'clear visual opening at path');
 assert.ok(vertices.some(([x])=>x<-7.3),'opposite enclosure retained');
});

test('low royal wicket occupies the opening and both closed collision systems remain authored',()=>{
 const node=scene.nodes.find(n=>n.id==='arrival-wicket');
 assert.deepEqual(node.transform.position,stats.gatePosition);
 const points=wicket.json.meshes.flatMap(m=>m.primitives.flatMap(wicket.points));
 assert.ok(Math.max(...points.map(p=>p[1]))<=1.12);
 assert.ok(wicket.json.materials.some(m=>m.name.startsWith('Dorure royale')));
 const flatten=nodes=>nodes.flatMap(n=>[n,...flatten(n.children??[])]),nodes=flatten(scene.nodes);
 for(const asset of ['arrivalCollision','arrivalBoundary'])assert.ok(nodes.some(n=>n.content?.asset===asset&&Object.keys(n.components??{}).some(c=>c.endsWith('StaticCollision'))));
 assert.ok(nodes.some(n=>Object.keys(n.components??{}).some(c=>c.endsWith('ArrivalBoundary'))));
});

test('carriage anchor is five metres along the gravel from the wicket; every hoof stays on the path',()=>{
 const node=scene.nodes.find(n=>n.id==='arrival-coach'),[x,y,z]=node.transform.position;
 const path=read('artifacts/royal-enclosure/model-stats.json').pathSamples;
 let distance=path[0][0]-stats.gatePosition[0];let measured;
 for(let i=0;i<path.length-1;i++){
  const a=path[i],b=path[i+1],length=Math.hypot(b[0]-a[0],b[1]-a[1]);
  const t=((x-a[0])*(b[0]-a[0])+(z-a[1])*(b[1]-a[1]))/(length*length);
  if(t>=0&&t<=1&&Math.hypot(x-a[0]-t*(b[0]-a[0]),z-a[1]-t*(b[1]-a[1]))<1e-6){measured=distance+t*length;break;}
  distance+=length;
 }
 assert.ok(Math.abs(measured-5)<1e-6);
 const angle=node.transform.rotationDeg[1]*Math.PI/180,c=Math.cos(angle),s=Math.sin(angle);
 const hooves=coach.json.meshes.flatMap(m=>m.primitives.filter(p=>coach.json.materials[p.material].name.startsWith('Corne des sabots')).flatMap(coach.points));
 assert.ok(hooves.length>100);
 for(const [px,py,pz] of hooves){
  const wx=x+c*px+s*pz,wz=z-s*px+c*pz;
  assert.ok(Math.min(...path.map(([xx,zz])=>Math.hypot(xx-wx,zz-wz)))<1.7,'hoof within the 3.6 m path');
  const ground=.048+.18*Math.sin(Math.PI*Math.max(0,Math.min(1,(Math.hypot(wx,wz)-8)/16)))**2;
  assert.ok(y+py-ground>-.012&&y+py-ground<.16,'hoof rests on gravel surface');
 }
});

test('two sculpted horses have coat materials, and the decorative asset stays bounded and self-contained',()=>{
 assert.equal(coach.json.nodes.filter(n=>/Cheval \d - anatomie/.test(n.name)).length,2);
 for(const n of coach.json.nodes.filter(n=>/anatomie/.test(n.name))){
  for(const p of coach.json.meshes[n.mesh].primitives)assert.match(coach.json.materials[p.material].name,/Robe/);
 }
 assert.ok(coach.json.materials.some(m=>/Noyer/.test(m.name)&&m.pbrMetallicRoughness.baseColorTexture));
 assert.ok(stats.assets.royalCoach.triangles<70000);
 assert.ok(coach.json.buffers.every(b=>!b.uri));assert.ok(coach.json.images.every(i=>!i.uri));
 assert.equal(coach.json.animations,undefined);
});
