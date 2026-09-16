import {readFile,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const root='artifacts/busts-makehuman';
async function glb(file){const b=await readFile(file);assert.equal(b.readUInt32LE(0),0x46546c67);const n=b.readUInt32LE(12);const j=JSON.parse(b.subarray(20,20+n));return {j,b:b.subarray(28+n),bytes:b.length};}
function acc(g,id){const a=g.j.accessors[id],v=g.j.bufferViews[a.bufferView],dim={SCALAR:1,VEC2:2,VEC3:3,VEC4:4}[a.type];const size={5126:4,5125:4,5123:2,5121:1}[a.componentType];const read={5126:'readFloatLE',5125:'readUInt32LE',5123:'readUInt16LE',5121:'readUInt8'}[a.componentType];const o=(v.byteOffset??0)+(a.byteOffset??0),stride=v.byteStride??dim*size;return Array.from({length:a.count},(_,i)=>Array.from({length:dim},(_,k)=>g.b[read](o+i*stride+k*size)));}
const ids=['bustFrancoisI','bustLouisXIV','bustCatherineMedici','bustAnneFrance'];const report={busts:{},scenes:{}};
for(const id of ids){const g=await glb(`public/gltf/castle/${id}.glb`);assert.equal(g.j.meshes.length,1);assert(g.j.nodes[0].name.includes('MakeHuman'));let triangles=0;const bounds=[[Infinity,-Infinity],[Infinity,-Infinity],[Infinity,-Infinity]];
 for(const p of g.j.meshes[0].primitives){triangles+=g.j.accessors[p.indices].count/3;for(const v of acc(g,p.attributes.POSITION)){v.forEach((x,i)=>{assert(Number.isFinite(x));bounds[i][0]=Math.min(bounds[i][0],x);bounds[i][1]=Math.max(bounds[i][1],x);});}}
 assert(bounds[0][1]-bounds[0][0]>.65);assert(bounds[2][1]-bounds[2][0]>.4);assert(Math.abs(bounds[1][0])<.00001);assert(bounds[1][1]>1&&bounds[1][1]<1.3);assert(g.j.meshes[0].primitives.length<=5);report.busts[id]={bytes:g.bytes,triangles,bounds,primitives:g.j.meshes[0].primitives.length};
}
for(const file of ['public/scenes/visit.iwsdk.scene.json','public/scenes/plaisance.iwsdk.scene.json','public/scenes/modules/castle-blender.iwsdk.scene.json']){
 const d=JSON.parse(await readFile(file));assert(!d.imports);const found=[];const walk=ns=>{for(const n of ns??[]){if(ids.includes(n.content?.asset))found.push(n);walk(n.children);}};walk(d.nodes);assert.equal(found.length,4);assert.equal(new Set(found.map(n=>n.content.asset)).size,4);for(const n of found)assert.equal(n.transform.position[1],ids.indexOf(n.content.asset)<2?6.14:1.74);report.scenes[file]=found.map(n=>({id:n.id,asset:n.content.asset,position:n.transform.position}));
}
// Exact geometry audit outside the two obsolete sculpted assemblies. Material,
// triangle ordering and indexing are irrelevant to the preserved vertex positions.
function triangles(g,filterOld){const list=[];let excluded=0;
 for(const m of g.j.meshes)for(const p of m.primitives){const vs=acc(g,p.attributes.POSITION),ix=acc(g,p.indices).flat();const material=g.j.materials[p.material].name;
  for(let i=0;i<ix.length;i+=3){const vv=ix.slice(i,i+3).map(k=>vs[k]);const old=(material.includes('Moulures ivoire')||material.includes('Marbre noir'))&&vv.every(v=>Math.abs(Math.abs(v[0])-6.1)<.36&&Math.abs(v[2]+4.25)<.25&&v[1]>1.725&&v[1]<2.70);
   if(filterOld&&old){excluded++;continue;}list.push(vv.map(v=>v.map(x=>Math.round(x*100000)).join(',')).sort().join('|'));
  }
 }return {hash:createHash('sha256').update(list.sort().join('\n')).digest('hex'),triangles:list.length,excluded};}
const before=triangles(await glb(`${root}/before/palaceInterior.glb`),true),after=triangles(await glb('public/gltf/castle/palaceInterior.glb'),false);
assert.equal(before.hash,after.hash,'Unrelated castle interior geometry changed');assert(before.excluded>1000);report.interior={before,after,unrelatedGeometryIdentical:true};
await writeFile(`${root}/verification.json`,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
