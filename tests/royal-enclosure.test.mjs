import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import vm from 'node:vm';
import ts from 'typescript';
import * as core from '@iwsdk/core';
import {Locomotor} from '@iwsdk/locomotor';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
function glb(path){
 const bytes=fs.readFileSync(path),length=bytes.readUInt32LE(12),json=JSON.parse(bytes.subarray(20,20+length)),bin=28+length;
 function accessor(index){const a=json.accessors[index],v=json.bufferViews[a.bufferView],n={SCALAR:1,VEC2:2,VEC3:3,VEC4:4}[a.type],size={5126:4,5125:4,5123:2}[a.componentType],result=[];
  for(let i=0;i<a.count;i++)for(let c=0;c<n;c++){const at=bin+(v.byteOffset??0)+(a.byteOffset??0)+i*(v.byteStride??n*size)+c*size;result.push(a.componentType===5126?bytes.readFloatLE(at):size===4?bytes.readUInt32LE(at):bytes.readUInt16LE(at));}return result;
 }
 function imageHash(index){const im=json.images[json.textures[index].source],v=json.bufferViews[im.bufferView];return crypto.createHash('sha256').update(bytes.subarray(bin+(v.byteOffset??0),bin+(v.byteOffset??0)+v.byteLength)).digest('hex');}
 return{json,accessor,imageHash};
}
const path=glb('public/gltf/royal-enclosure/arrivalPath.glb');
test('new path shares the exact color and normal image bytes and roughness with castle gravel',()=>{
 const reference=glb('public/gltf/garden/pathLong.glb'),a=reference.json.materials[0],b=path.json.materials[0];
 assert.equal(path.imageHash(b.pbrMetallicRoughness.baseColorTexture.index),reference.imageHash(a.pbrMetallicRoughness.baseColorTexture.index));
 assert.equal(path.imageHash(b.normalTexture.index),reference.imageHash(a.normalTexture.index));
 assert.equal(b.pbrMetallicRoughness.roughnessFactor,a.pbrMetallicRoughness.roughnessFactor);
});
test('every gravel triangle stays outside the eight metre arrival circle',()=>{
 const primitive=path.json.meshes[0].primitives[0],p=path.accessor(primitive.attributes.POSITION),indices=path.accessor(primitive.indices);
 for(let i=0;i<indices.length;i+=3){
  const points=indices.slice(i,i+3).map(k=>[p[k*3],p[k*3+2]]);
  for(let j=0;j<3;j++){
   const a=points[j],b=points[(j+1)%3],dx=b[0]-a[0],dz=b[1]-a[1],t=Math.max(0,Math.min(1,-(a[0]*dx+a[1]*dz)/(dx*dx+dz*dz||1)));
   assert.ok(Math.hypot(a[0]+t*dx,a[1]+t*dz)>=8,`triangle ${i/3} enters circle`);
  }
 }
 const start=[];for(let i=0;i<p.length;i+=3)if(Math.hypot(p[i],p[i+2])<8.03)start.push([p[i],p[i+2]]);
 assert.ok(start.length>=17,'curved edge is tessellated around the circle');
});
test('royal gate and complete decorated enclosure are present in both scenes',()=>{
 const flatten=nodes=>nodes.flatMap(n=>[n,...flatten(n.children??[])]);
 for(const name of ['arrival','plaisance']){
  const doc=read(`public/scenes/${name}.iwsdk.scene.json`),nodes=flatten(doc.nodes),assets=nodes.map(n=>n.content?.asset);
  assert.ok(assets.includes(name==='arrival'?'royalGateFar':'royalGate'));
  assert.ok(assets.includes(name==='arrival'?'royalFenceFar':'royalFence'));
  assert.ok(!assets.includes('arrivalGateway'));assert.ok(!assets.includes('gardenBorder'));
 }
 const baseline=read('artifacts/royal-enclosure/arrival-before.json'),current=read('public/scenes/arrival.iwsdk.scene.json');
 for(const node of baseline.nodes.filter(n=>!n.id.startsWith('landscape-')))assert.deepEqual(current.nodes.find(n=>n.id===node.id),node);
 assert.deepEqual(current.player,baseline.player);
 for(const [name,minHeight] of [['royalGate',8],['royalFence',4]]){
  const model=glb(`public/gltf/royal-enclosure/${name}.glb`);
  const ymax=Math.max(...model.json.meshes.flatMap(m=>m.primitives.map(p=>model.json.accessors[p.attributes.POSITION].max[1])));assert.ok(ymax>=minHeight);
  assert.ok(model.json.materials.some(m=>m.name.startsWith('Dorure royale')));
 }
});
const compile=p=>ts.transpileModule(fs.readFileSync(p,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const collision={};vm.runInNewContext(compile('src/scene-assets/static-collision.ts'),{exports:collision,require:()=>core});
const asset={};vm.runInNewContext(compile('src/scene-assets/royal-enclosure-collision.scene-asset.ts'),{exports:asset,require:id=>id==='@iwsdk/core'?core:collision});
test('enclosure and the full-height invisible gate wall block passage behind the return portal',async()=>{
 const wall=asset.default;wall.updateMatrixWorld(true);const ray=new core.Raycaster(),hits=[];
 for(const [x,z,dx,dz] of [[0,-5,1,0],[0,-5,-1,0],[0,-5,0,-1],[-15,-5,0,1],[15,-5,0,1],[0,-5,30,-35],[0,-5,-30,35]]){
  ray.set(new core.Vector3(x,1.6,z),new core.Vector3(dx,0,dz).normalize());hits.length=0;ray.intersectObject(wall,true,hits);assert.ok(hits.length);
 }
 for(const x of [-5,-2.5,0,2.5,5])for(const y of [.05,1.6,4,8.5]){
  ray.set(new core.Vector3(x,y,29.5),new core.Vector3(0,0,1));hits.length=0;ray.intersectObject(wall,true,hits);
  assert.ok(hits.some(h=>Math.abs(h.point.z-29.85)<.001),'opening is closed behind the portal at every height');
 }
 wall.traverse(o=>{if(o.isMesh)assert.equal(o.material.visible,false);});
 const engine=new Locomotor({useWorker:false,initialPlayerPosition:new core.Vector3(0,0,24)});await engine.initialize();
 try{
  const floor=new core.Group(),mesh=new core.Mesh(new core.BoxGeometry(70,.2,100));mesh.position.y=-.1;floor.add(mesh);
  engine.addEnvironment(collision.createStaticCollision(floor));engine.addEnvironment(wall.clone(true));
  for(let i=0;i<450;i++){engine.slide(new core.Vector3(0,0,2));engine.update(1/90);}
  // Return trigger starts at local z=28 (-67 in the merged domain).
  assert.ok(engine.position.z>28&&engine.position.z<29.85,`can reach the return trigger, but cannot pass the wall: z=${engine.position.z}`);
 }finally{engine.terminate();}
});
