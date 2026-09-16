import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import ts from 'typescript';
import { Raycaster, Vector3 } from '@iwsdk/core';
const source=readFileSync('src/scene-assets/garden-collision.scene-asset.ts','utf8');
const output=new URL('../artifacts/garden/collision-proxies.mjs',import.meta.url);
writeFileSync(output,ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText);
const proxies=await import(output.href);
const report={};
for(const [id,root] of Object.entries(proxies)){
  root.updateMatrixWorld(true); let triangles=0;
  root.traverse(o=>{if(o.isMesh)triangles+=(o.geometry.index?.count??o.geometry.attributes.position.count)/3;});
  report[id]={triangles};
}
function down(root,x,z){return new Raycaster(new Vector3(x,3,z),new Vector3(0,-1,0)).intersectObject(root,true)[0];}
assert.ok(Math.abs(down(proxies.ground,0,24).point.y)<1e-6,'standing spawn supported');
assert.ok(Math.abs(down(proxies.path,0,0).point.y-.04)<1e-6,'walkable path top');
// Sample actual strip midpoints: outward faces must be hittable with FrontSide.
for(const [x,z,height] of [[4.56,4.56,.47],[4.79,3.6,.41],[1.9,0,.41]]){
  const hit=down(proxies.parterre,x,z);
  assert.ok(hit && Math.abs(hit.point.y-height)<1e-5,`hedge top ${x},${z}`);
  assert.ok(hit.face.normal.y>.99,'outward upward normal');
}
assert.ok(report.parterre.triangles<3000,'cheap collision envelopes');
writeFileSync('artifacts/garden/collision-verification.json',JSON.stringify({checks:'spawn, path and three hedge profiles supported; outward top faces',proxies:report},null,2));
console.log(JSON.stringify(report));
