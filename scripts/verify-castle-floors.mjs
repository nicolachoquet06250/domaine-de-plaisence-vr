import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {Matrix4,Vector3,Quaternion} from '@iwsdk/core';
// Test the EXPORTED visible triangles, independently of authoring dimensions.
const floors=[];
for(const id of ['palace','palaceInterior']){
  const bytes=readFileSync(`public/gltf/castle/${id}.glb`),len=bytes.readUInt32LE(12);
  const doc=JSON.parse(bytes.subarray(20,20+len)),bin=bytes.subarray(28+len);
  function accessor(index){
    const a=doc.accessors[index],v=doc.bufferViews[a.bufferView],size=a.componentType===5123?2:4;
    const width={SCALAR:1,VEC3:3}[a.type],stride=v.byteStride??size*width,base=(v.byteOffset??0)+(a.byteOffset??0);
    const read=a.componentType===5126?'readFloatLE':size===2?'readUInt16LE':'readUInt32LE';
    return Array.from({length:a.count},(_,i)=>Array.from({length:width},(_,j)=>bin[read](base+i*stride+j*size)));
  }
  function node(index,parent=new Matrix4()){
    const n=doc.nodes[index],local=n.matrix?new Matrix4().fromArray(n.matrix):new Matrix4().compose(new Vector3().fromArray(n.translation??[0,0,0]),new Quaternion().fromArray(n.rotation??[0,0,0,1]),new Vector3().fromArray(n.scale??[1,1,1]));
    const world=parent.clone().multiply(local);
    if(n.mesh!==undefined)for(const p of doc.meshes[n.mesh].primitives){
      const vertices=accessor(p.attributes.POSITION).map(v=>new Vector3().fromArray(v).applyMatrix4(world));
      const indices=accessor(p.indices).flat();
      for(let i=0;i<indices.length;i+=3){
        const t=indices.slice(i,i+3).map(j=>vertices[j]);
        const normal=t[1].clone().sub(t[0]).cross(t[2].clone().sub(t[0]));
        if(normal.y<=1e-8 || Math.max(...t.map(v=>v.y))-Math.min(...t.map(v=>v.y))>1e-5)continue;
        if(![.64,2.84,5.04].some(y=>Math.abs(y-t[0].y)<.018))continue;
        const material=doc.materials[p.material].name;
        // Only floor finishes and the exterior top tread; wall section caps are
        // buried inside the next storey's masonry and cannot cause visible flicker.
        const floorFinish=/Parquet|Marbre|Bronze/.test(material);
        const terrace=id==='palace' && /Moulures/.test(material) && Math.abs(t[0].y-.64)<1e-5 && t.every(v=>v.z>=5.79999);
        if(!floorFinish && !terrace)continue;
        const poly=t.map(v=>[v.x,v.z]);
        if(area(poly)<0)poly.reverse();
        floors.push({id,material:doc.materials[p.material].name,y:t[0].y,poly});
      }
    }
    for(const child of n.children??[])node(child,world);
  }
  for(const n of doc.scenes[doc.scene??0].nodes)node(n);
}
function area(p){return p.reduce((s,a,i)=>{const b=p[(i+1)%p.length];return s+a[0]*b[1]-a[1]*b[0];},0)/2;}
function cross(a,b,c){return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);}
function clip(poly,triangle){
  for(let j=0;j<3 && poly.length;j++){
    const a=triangle[j],b=triangle[(j+1)%3],out=[];
    for(let i=0;i<poly.length;i++){
      const p=poly[i],q=poly[(i+1)%poly.length],cp=cross(a,b,p),cq=cross(a,b,q);
      if(cp>=-1e-9)out.push(p);
      if((cp>0 && cq<0)||(cp<0 && cq>0)){const t=cp/(cp-cq);out.push([p[0]+(q[0]-p[0])*t,p[1]+(q[1]-p[1])*t]);}
    }
    poly=out;
  }
  return poly;
}
const overlaps=[];
for(let i=0;i<floors.length;i++)for(let j=i+1;j<floors.length;j++){
  const a=floors[i],b=floors[j];if(Math.abs(a.y-b.y)>.018)continue;
  const overlap=Math.abs(area(clip(a.poly,b.poly)));
  if(overlap>1e-5)overlaps.push({a,b,squareMetres:overlap});
}
writeFileSync('artifacts/castle-refinement/floor-overlap-check.json',JSON.stringify({trianglesChecked:floors.length,overlaps},null,2));
assert.equal(overlaps.length,0,'floor surfaces must not overlap, including nearly coplanar inlays; see floor-overlap-check.json');
console.log(`${floors.length} exported floor triangles checked: no coplanar or near-coplanar overlaps.`);
