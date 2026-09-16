import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {Matrix4, Vector3, Quaternion, Euler} from '@iwsdk/core';
import {mirrorOval, mirrorRectangle} from '../src/scene-assets/mirrors.scene-asset.ts';
import {hearthFire} from '../src/scene-assets/hearth-fire.scene-asset.ts';
import coachPortal from '../src/scene-assets/coach-portal.scene-asset.ts';

const root=process.cwd(), out=path.join(root,'artifacts/scene-fbx');
fs.mkdirSync(out,{recursive:true});
const source='public/scenes/visit.iwsdk.scene.json';
const document=JSON.parse(fs.readFileSync(source,'utf8'));
const assetsText=fs.readFileSync('src/assets.ts','utf8');
const assets={};
for(const match of assetsText.matchAll(/(\w+):\s*\{\s*url:\s*`\$\{import\.meta\.env\.BASE_URL\}([^`]+)`/g)) {
  assets[match[1]]={path:'public/'+match[2].split('?')[0]};
}
for(const [id,object] of Object.entries({mirrorOval,mirrorRectangle,hearthFire,coachPortal})) {
  object.updateMatrixWorld(true);
  const meshes=[];
  object.traverse(o=>{
    if(!o.isMesh) return;
    const g=o.geometry,m=o.material;
    meshes.push({name:o.name||id,matrix:o.matrixWorld.toArray(),
      positions:Array.from(g.attributes.position.array),uv:g.attributes.uv?Array.from(g.attributes.uv.array):null,
      indices:g.index?Array.from(g.index.array):null,seed:g.attributes.flameSeed?Array.from(g.attributes.flameSeed.array):null,
      material:{name:m.name||id,color:m.color?.toArray()??[1,.25,.025],metalness:m.metalness??0,roughness:m.roughness??.5,
        opacity:m.opacity,transparent:m.transparent,doubleSided:m.side===2,unlit:m.isMeshBasicMaterial??false,shader:m.isShaderMaterial??false}});
  });
  assets[id]={meshes};
}
const nodes=[],excluded=[],missing=[];
function visit(list,parent=new Matrix4(),inside=false) {
  for(const n of list) {
    if(n.content?.type && !['asset','group'].includes(n.content.type)) throw Error('Unexpanded node '+n.id);
    const t=n.transform??{}, scale=typeof t.scale==='number'?[t.scale,t.scale,t.scale]:t.scale??[1,1,1];
    const q=t.quaternion?new Quaternion(...t.quaternion):new Quaternion().setFromEuler(new Euler(...(t.rotationDeg??[0,0,0]).map(v=>v*Math.PI/180),'XYZ'));
    const matrix=parent.clone().multiply(new Matrix4().compose(new Vector3(...(t.position??[0,0,0])),q,new Vector3(...scale)));
    const isInterior=inside||n.id==='castle/interior'||/^castle\/door-(west|east)/.test(n.id)||/^castle\/light-/.test(n.id)||/^(mirror-|hearth-|royal-(francois|louis|catherine|anne))/.test(n.id);
    const asset=n.content?.asset;
    if(asset) {
      if(/Collision$|Boundary$/.test(asset)) excluded.push({id:n.id,asset,reason:'Non-rendered collision helper'});
      else if(asset.endsWith('-panel')) excluded.push({id:n.id,asset,reason:'Runtime UIKitML interface, not modeled geometry'});
      else if(!assets[asset]) missing.push({id:n.id,asset});
      else nodes.push({id:n.id,name:n.name??n.id,asset,matrix:matrix.toArray(),interior:isInterior});
    }
    for(const [component,props] of Object.entries(n.components??{})) {
      if(/(Directional|Point|Spot|RectArea)Light$/.test(component)) nodes.push({id:n.id,name:n.name??n.id,matrix:matrix.toArray(),interior:isInterior,light:{type:component.split('.').at(-1),...props}});
    }
    visit(n.children??[],matrix,isInterior);
  }
}
visit(document.nodes);
if(missing.length) throw Error(JSON.stringify({missing}));
const used=new Set(nodes.map(n=>n.asset).filter(Boolean));
for(const id of Object.keys(assets)) {
  if(!used.has(id)) {delete assets[id];continue;}
  if(assets[id].path) {
    const b=fs.readFileSync(assets[id].path);
    assets[id].sha256=crypto.createHash('sha256').update(b).digest('hex');
  }
}
fs.writeFileSync(path.join(out,'composition-input.json'),JSON.stringify({source,sourceSha256:crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex'),assets,nodes,excluded,views:document.authoring.views},null,2));
console.log(JSON.stringify({nodes:nodes.length,interior:nodes.filter(n=>n.interior).length,assets:Object.keys(assets).length,excluded:excluded.length}));
