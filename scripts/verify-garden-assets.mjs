import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
const budgets={ground:20,path:20,pathLong:20,pathCross:20,pathTerrace:20,gardenBorder:3000,urn:4500,parterre:27000,cypress:5100};
const report={};
for(const [id,budget] of Object.entries(budgets)){
  const bytes=readFileSync(`public/gltf/garden/${id}.glb`);
  assert.equal(bytes.readUInt32LE(0),0x46546c67);
  const length=bytes.readUInt32LE(12), gltf=JSON.parse(bytes.subarray(20,20+length));
  const binary=bytes.subarray(28+length);
  assert.ok(gltf.images.every(i=>i.bufferView!==undefined));
  assert.ok(gltf.buffers.every(b=>!b.uri));
  assert.equal(gltf.nodes.length,1,`${id}: merged reusable hierarchy`);
  assert.ok(!gltf.animations?.length);
  let triangles=0;
  const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
  for(const mesh of gltf.meshes)for(const p of mesh.primitives){
    triangles+=gltf.accessors[p.indices].count/3;
    const pos=gltf.accessors[p.attributes.POSITION];
    for(let axis=0;axis<3;axis++){min[axis]=Math.min(min[axis],pos.min[axis]);max[axis]=Math.max(max[axis],pos.max[axis]);}
    const uv=gltf.accessors[p.attributes.TEXCOORD_0];
    assert.ok(uv,`${id}: UVs present`);
    assert.equal(p.attributes.TEXCOORD_1,undefined,`${id}: one consistent UV layer`);
    const view=gltf.bufferViews[uv.bufferView], offset=(view.byteOffset??0)+(uv.byteOffset??0);
    const samples=Array.from({length:uv.count*2},(_,i)=>binary.readFloatLE(offset+i*4));
    assert.ok(samples.every(Number.isFinite));
    assert.ok(Math.max(...samples)-Math.min(...samples)>.01,`${id}: nonconstant UV mapping`);
    const mat=gltf.materials[p.material];
    assert.notEqual(mat.alphaMode,'BLEND',`${id}: no vegetation blending/overdraw`);
  }
  assert.ok(triangles<=budget,`${id}: triangle budget`);
  assert.ok(bytes.length<2_000_000,`${id}: payload budget`);
  report[id]={bytes:bytes.length,triangles,drawCalls:gltf.meshes.reduce((n,m)=>n+m.primitives.length,0),bounds:{min,max}};
}
const before=JSON.parse(readFileSync('artifacts/garden/plaisance-before.iwsdk.scene.json'));
const after=JSON.parse(readFileSync('public/scenes/plaisance.iwsdk.scene.json'));
assert.ok(!after.imports);
const restored=structuredClone(after);let pathCount=0;
function walk(nodes){for(const n of nodes){if(['pathLong','pathCross','pathTerrace'].includes(n.content?.asset)){n.content.asset='path';pathCount++;}walk(n.children??[]);}}
walk(restored.nodes);assert.equal(pathCount,4);
assert.deepEqual(restored,before,'Only gravel UV asset IDs change; preserve scene composition, spawn and collision children');
writeFileSync('artifacts/garden/glb-verification.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
