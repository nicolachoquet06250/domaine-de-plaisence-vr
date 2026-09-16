import { readFileSync, writeFileSync, copyFileSync, existsSync } from 'node:fs';
const path='public/scenes/plaisance.iwsdk.scene.json';
if (!existsSync('artifacts/castle/scene-before.json')) copyFileSync(path,'artifacts/castle/scene-before.json');
const scene=JSON.parse(readFileSync(path,'utf8'));
const castle=scene.nodes.find(n=>n.id==='castle');
const shell=castle.children.find(n=>n.id==='castle/palace');
shell.children=shell.children.filter(n=>n.id==='castle/collision');
const asset=(id,name,model,position=[0,0,0],shadow=false)=>({id,name,content:{type:'asset',asset:model,castShadow:shadow,receiveShadow:true},transform:{position}});
castle.children=[shell,
  asset('castle/interior','Salons, galerie et escalier','palaceInterior'),
  asset('castle/glazing','Vitrages transparents','palaceGlass'),
];
const doors=[['entrance','Porte du vestibule',[0,.64,6],0,[1,2.9/3.5,1]],
  ['west-salon','Porte du salon ouest',[-4.65,.64,3.8],-90,[1,1,1]],
  ['east-salon','Porte du salon est',[4.65,.64,3.8],90,[1,1,1]],
  ['west-gallery','Porte ouest de la galerie',[-4.65,5.04,3.8],-90,[1,1,1]],
  ['east-gallery','Porte est de la galerie',[4.65,5.04,3.8],90,[1,1,1]]];
for(const [suffix,name,position,yaw,scale] of doors){
  const id=`castle/door-${suffix}`,node=asset(id,name,'palaceDoor',position);
  node.transform.rotationDeg=[0,yaw,0];node.transform.scale=scale;
  node.components={PalaceDoor:{automatic:true,approachDistance:3.2},RayInteractable:{}};
  const blocker=asset(`${id}/blocker`,`${name} — collision`,'palaceDoorCollision');
  blocker.components={PalaceDoorBlocker:{owner:{type:'node',id}}};node.children=[blocker];castle.children.push(node);
}
for(const [name,position,intensity,distance] of [['vestibule',[0,7.9,0],85,13],['salon-west',[-10.6,3.54,0],38,10],['salon-east',[10.6,3.54,0],38,10],['gallery-west',[-10.6,7.94,0],38,10],['gallery-east',[10.6,7.94,0],38,10]]){
  castle.children.push({id:`castle/light-${name}`,name:`Lustre ${name}`,content:{type:'group'},transform:{position},components:{PointLight:{color:[1,.80,.57,1],intensity,distance,decay:2,castShadow:false}}});
}
scene.authoring.views=scene.authoring.views.filter(v=>!['castle-facade','castle-hall','castle-salon','castle-gallery'].includes(v.id));
const views=[['castle-facade',[29,15,0],[0,7,-28],55],['castle-hall',[0,2.3,-23.5],[0,3.9,-30.2],80],['castle-salon',[6.3,2.25,-24.7],[15.5,2.1,-29],75],['castle-gallery',[0,6.7,-23.9],[0,3.4,-30.8],80]];
for(const [id,position,target,fov] of views)scene.authoring.views.push({id,role:'diagnostic',projection:'perspective',position,target,fov});
writeFileSync(path,JSON.stringify(scene,null,2)+'\n');
const local=structuredClone(castle);local.transform.position=[0,0,0];
const scratch={version:'iwsdk.scene.v1',units:'meters',resources:{},components:scene.components,environment:scene.environment,nodes:[structuredClone(scene.nodes.find(n=>n.id==='sun')),local],authoring:{views:views.map(([id,pos,target,fov])=>({id,role:id==='castle-facade'?'hero':'diagnostic',projection:'perspective',position:[pos[0],pos[1],pos[2]+28],target:[target[0],target[1],target[2]+28],fov}))}};
writeFileSync('public/scenes/modules/castle-blender.iwsdk.scene.json',JSON.stringify(scratch,null,2)+'\n');
console.log('Replaced castle visuals; five animated doors, interior and glazing placed. Garden unchanged.');
