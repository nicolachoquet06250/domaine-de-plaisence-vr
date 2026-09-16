import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';

// Verify the exported, production GLBs: footprint, genuinely raised grass,
// clear hardscape, bounded geometry and flower stems matching every corolla.
function rect(x,z,cx,cz,hx,hz) { return Math.max(Math.abs(x-cx)-hx,Math.abs(z-cz)-hz); }
function estateClearance(x,z) {
  const distances=[rect(x,z,0,0,3.57,27.07),rect(x,z,0,0,22.57,3.57),
    rect(x,z,0,-20,22.57,3.07),rect(x,z,0,24,22.57,3.07),rect(x,z,0,-28,21.3,7.3)];
  for(const px of [-12,12])for(const pz of [-10,10])distances.push(rect(x,z,px,pz,7.04,7.04));
  for(const wx of [-30,30])distances.push(rect(x,z,wx,-5,.39,35.15));
  for(const cx of [-23,23])for(const cz of [-25,-18,-11,-4,3,10,17,24])distances.push(Math.hypot(x-cx,z-cz)-.24);
  return Math.min(...distances);
}
function glb(path) {
  const bytes=readFileSync(path);
  assert.equal(bytes.readUInt32LE(0),0x46546c67);
  const length=bytes.readUInt32LE(12),data=JSON.parse(bytes.subarray(20,20+length)),binary=bytes.subarray(28+length);
  function positions(index) {
    const a=data.accessors[index],v=data.bufferViews[a.bufferView];
    assert.equal(a.componentType,5126);
    const offset=(v.byteOffset??0)+(a.byteOffset??0),stride=v.byteStride??12;
    return Array.from({length:a.count},(_,i)=>[0,1,2].map(k=>binary.readFloatLE(offset+i*stride+k*4)));
  }
  return {bytes,data,positions};
}
const report={};
for(const [id,budget] of [['estateLawnRelief',190000],['arrivalLawnRelief',80000]]) {
  const {bytes,data,positions}=glb(`public/gltf/vegetation/${id}.glb`);
  let triangles=0,grassVertices=0,raisedVertices=0,drawCalls=0;
  const bounds={min:[Infinity,Infinity,Infinity],max:[-Infinity,-Infinity,-Infinity]};
  for(const mesh of data.meshes)for(const p of mesh.primitives) {
    drawCalls++;
    triangles+=data.accessors[p.indices].count/3;
    const mat=data.materials[p.material],isGrass=mat.name.includes('folded blades');
    assert.notEqual(mat.alphaMode,'BLEND',`${id} must use opaque grass`);
    for(const v of positions(p.attributes.POSITION)) {
      assert.ok(v.every(Number.isFinite));
      v.forEach((value,k)=>{bounds.min[k]=Math.min(bounds.min[k],value);bounds.max[k]=Math.max(bounds.max[k],value);});
      if(!isGrass)continue;
      grassVertices++;
      if(v[1]>.05)raisedVertices++;
      const clearance=id==='estateLawnRelief'?estateClearance(v[0],v[2]):Math.min(Math.hypot(v[0],v[2])-8.03,20-Math.hypot(v[0],v[2]));
      assert.ok(clearance>.005,`${id}: blade intrudes into hardscape at ${v}`);
      assert.ok(v[1]>=-.001 && v[1]<.16,`${id}: grass height appropriate to cut lawn`);
    }
  }
  assert.ok(raisedVertices>10000,`${id}: enough actual above-ground geometry`);
  assert.ok(triangles<budget,`${id}: ${triangles} triangles exceed budget`);
  assert.ok(drawCalls<24,`${id}: bounded terrain chunks`);
  assert.ok(bytes.length<12_000_000,`${id}: bounded binary size`);
  assert.ok(data.images?.every(i=>i.bufferView!==undefined));
  if(id==='estateLawnRelief') {
    assert.ok(Math.abs(bounds.min[0]+35)<.06 && Math.abs(bounds.max[0]-35)<.06);
    assert.ok(Math.abs(bounds.min[2]+51)<.06 && Math.abs(bounds.max[2]-39)<.06);
  }
  report[id]={triangles,drawCalls,bytes:bytes.length,grassVertices,raisedVertices,bounds};
}
const flowerStats=JSON.parse(readFileSync('artifacts/vegetation/flower-stats.json'));
for(const [id,expected] of [['parterre',70],['urn',12]]) {
  const {data,positions}=glb(`public/gltf/garden/${id}.glb`);
  const vertices=[];
  for(const mesh of data.meshes)for(const p of mesh.primitives) {
    if(data.materials[p.material].name.includes('Rose stems and sepals'))vertices.push(...positions(p.attributes.POSITION));
  }
  assert.equal(flowerStats[id].flowersWithRootedStems,expected);
  assert.ok(vertices.length>expected*20);
  for(const [x,zBlender,soil,top] of flowerStats[id].flowerCenters) {
    const z=-zBlender;
    assert.ok(vertices.some(v=>Math.abs(v[1]-top)<.004 && Math.hypot(v[0]-x,v[2]-z)<.01),`${id}: corolla disconnected from stem`);
    assert.ok(vertices.some(v=>Math.abs(v[1]-soil)<.003 && Math.hypot(v[0]-x,v[2]-z)<.06),`${id}: stem does not reach soil`);
  }
  report[id]={rootedFlowers:expected,stemVertices:vertices.length,stemHeightMeters:flowerStats[id].stemHeightMeters};
}
mkdirSync('artifacts/vegetation',{recursive:true});
writeFileSync('artifacts/vegetation/verification.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
