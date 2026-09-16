import {readFileSync,writeFileSync} from 'node:fs';
for(const path of ['public/scenes/plaisance.iwsdk.scene.json','public/scenes/modules/castle-blender.iwsdk.scene.json']){
  const doc=JSON.parse(readFileSync(path));
  const parent=doc.nodes.find(n=>n.id==='castle')??doc.nodes.find(n=>n.id==='chateau');
  const children=parent?.children??doc.nodes;
  for(const [id,asset,x,name] of [['royal-francois','bustFrancoisI',-12.8,'François Ier — d’après Clouet'],['royal-louis','bustLouisXIV',12.8,'Louis XIV — inspiré du Bernin']]){
    const index=children.findIndex(n=>n.id===id);if(index>=0)children.splice(index,1);
    children.push({id,name,content:{type:'asset',asset,castShadow:true,receiveShadow:true},transform:{position:[x,6.14,1]}});
  }
  writeFileSync(path,JSON.stringify(doc,null,2)+'\n');
}
const path='public/scenes/arrival.iwsdk.scene.json',doc=JSON.parse(readFileSync(path));
if(!doc.nodes.some(n=>n.id==='arrival-lawn-relief'))doc.nodes.push({id:'arrival-lawn-relief',name:'Pelouse en relief',content:{type:'asset',asset:'arrivalLawnRelief',receiveShadow:true,castShadow:false}});
writeFileSync(path,JSON.stringify(doc,null,2)+'\n');
