import fs from 'node:fs';
import {createCoachRoutes} from '../src/coach-route.ts';
const dir='artifacts/unity-interactions';
const routes=createCoachRoutes();
const source=JSON.parse(fs.readFileSync('artifacts/scene-fbx/composition-input.json','utf8'));
const config={placements:source.nodes.filter(n=>n.asset==='palaceDoor'||['water','centralJet','lateralJet'].includes(n.asset)).map(n=>({id:n.id,asset:n.asset,matrix:n.matrix})),routes:[],morphs:[]};
for(const [name,route] of Object.entries(routes)) {
 const points=[];for(let i=0;i<route.points.length;i+=3)points.push({x:-route.points[i],y:route.points[i+1],z:route.points[i+2]});
 config.routes.push({name,length:route.length,points});
}
for (const name of ['water','centralJet','lateralJet']) {
 const bytes=fs.readFileSync(`public/gltf/estate/${name}.glb`);const doc=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)));
 for (const animation of doc.animations) {
  const channel=animation.channels[0];const sampler=animation.samplers[channel.sampler];
  config.morphs.push({asset:name,node:doc.nodes[channel.target.node].name,duration:doc.accessors[sampler.input].max[0]});
 }
}
const bytes=fs.readFileSync('public/gltf/arrival-coach/royalCoachAnimated.glb');const size=bytes.readUInt32LE(12);const doc=JSON.parse(bytes.subarray(20,20+size));
const bin=bytes.subarray(28+size);
for(let i=0;i<(doc.images||[]).length;i++) {const v=doc.bufferViews[doc.images[i].bufferView];fs.writeFileSync(`${dir}/carrosse-texture-${i}.png`,bin.subarray(v.byteOffset,v.byteOffset+v.byteLength));}
config.coachMaterials=doc.materials.map(m=>({name:m.name,normalTexture:m.normalTexture ? `carrosse-texture-${doc.textures[m.normalTexture.index].source}.png`:null,baseTexture:m.pbrMetallicRoughness?.baseColorTexture ? `carrosse-texture-${doc.textures[m.pbrMetallicRoughness.baseColorTexture.index].source}.png`:null}));
fs.writeFileSync(`${dir}/interaction-config.json`,JSON.stringify(config));
console.log('Routes and source animation timings prepared.');
