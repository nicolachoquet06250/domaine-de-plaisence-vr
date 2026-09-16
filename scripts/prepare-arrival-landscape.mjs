import fs from 'node:fs';
import {Matrix4,Euler,Quaternion,Vector3} from '@iwsdk/core';
const scene=JSON.parse(fs.readFileSync('artifacts/arrival-landscape/plaisance-before.json','utf8'));
const manifest=fs.readFileSync('src/assets.ts','utf8'),urls={};
for(const m of manifest.matchAll(/(\w+): \{ url: `\$\{import.meta.env.BASE_URL\}([^`]+)`/g))urls[m[1]]='public/'+m[2].split('?')[0];
const keep=new Set(['palace','palaceGlass','palaceDoor','ground','parterre','cypress','urn','pathLong','pathCross','pathTerrace','bench','gardenBorder','basin']);
const placements=[];
function walk(nodes,parent=new Matrix4()) {for(const node of nodes){
 const t=node.transform??{},r=t.rotationDeg??[0,0,0],s=t.scale??[1,1,1];
 const local=new Matrix4().compose(new Vector3(...(t.position??[0,0,0])),new Quaternion().setFromEuler(new Euler(...r.map(v=>v*Math.PI/180))),new Vector3(...(typeof s==='number'?[s,s,s]:s)));
 const world=parent.clone().multiply(local),asset=node.content?.asset;
 if(keep.has(asset)&&(asset!=='palaceDoor'||node.id==='castle/door-entrance'))placements.push({id:node.id,asset,path:urls[asset],matrix:world.elements});
 if(node.children)walk(node.children,world);
}}
walk(scene.nodes);
fs.writeFileSync('artifacts/arrival-landscape/exterior-placements.json',JSON.stringify({offset:[100,0,-95],placements},null,2));
console.log(`${placements.length} exterior placements; no interior assets`);
