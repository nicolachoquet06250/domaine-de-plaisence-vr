import {readFileSync,writeFileSync} from 'node:fs';
const views=[
  ['castle-bedroom',[6.2,6.8,1.5],[10.1,6.05,-2.9],75],
  ['castle-bathroom',[15.3,6.85,1.5],[18.0,5.95,-2.8],75],
  ['castle-bathroom-fixtures',[15.3,6.75,1.3],[18.4,5.9,3.8],75],
  ['castle-understairs',[.2,1.55,-.8],[3.2,2.55,.3],78],
  ['castle-landing',[0,4.4,-2.8],[3.8,3.1,-5.45],78],
  ['castle-balustrade',[11.8,2.7,10.5],[12.8,1.3,7.3],63],
];
for(const [path,zOffset] of [['public/scenes/plaisance.iwsdk.scene.json',-28],['public/scenes/modules/castle-blender.iwsdk.scene.json',0]]){
  const doc=JSON.parse(readFileSync(path));
  for(const [id,position,target,fov] of views){
    doc.authoring.views=doc.authoring.views.filter(v=>v.id!==id);
    doc.authoring.views.push({id,role:'diagnostic',projection:'perspective',position:[position[0],position[1],position[2]+zOffset],target:[target[0],target[1],target[2]+zOffset],fov});
  }
  writeFileSync(path,JSON.stringify(doc,null,2)+'\n');
}
