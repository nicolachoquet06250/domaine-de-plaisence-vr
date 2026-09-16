import {readFileSync,writeFileSync} from 'node:fs';
const env=JSON.parse(readFileSync('public/scenes/arrival.iwsdk.scene.json'));
const scene={version:'iwsdk.scene.v1',units:'meters',resources:{},components:env.components,environment:env.environment,
  authoring:{views:[{id:'hero',role:'hero',projection:'perspective',position:[0,1.15,3.5],target:[0,.92,0],fov:46},
  {id:'francois',role:'diagnostic',projection:'perspective',position:[-1.42,.80,1.55],target:[-1.5,.59,0],fov:48},
  {id:'louis',role:'diagnostic',projection:'perspective',position:[1.60,.82,1.68],target:[1.5,.56,0],fov:48},
  {id:'male',role:'diagnostic',projection:'perspective',position:[-.7,1.03,2.5],target:[-.6,.97,0],fov:44},
  {id:'female',role:'diagnostic',projection:'perspective',position:[.7,1.03,2.5],target:[.6,.90,0],fov:44}]},
  nodes:[structuredClone(env.nodes.find(n=>n.id==='sun')),
    ...[['portrait-francois','bustFrancoisI',-1.5],['portrait-louis','bustLouisXIV',1.5],['avatar-male','courtMale',-.6],['avatar-female','courtFemale',.6]].map(([id,asset,x])=>({id,content:{type:'asset',asset},transform:{position:[x,0,0]}}))]};
writeFileSync('public/scenes/modules/court-review.iwsdk.scene.json',JSON.stringify(scene,null,2)+'\n');
for(const [path,offset] of [['public/scenes/plaisance.iwsdk.scene.json',-28],['public/scenes/modules/castle-blender.iwsdk.scene.json',0]]){
  const doc=JSON.parse(readFileSync(path));
  for(const [id,p,t,fov] of [['door-jamb',[6.0,2.35,2.0],[4.65,2.1,2.16],65],['royal-francois',[-12.5,6.95,2.6],[-12.8,6.76,1],52],['royal-louis',[12.8,6.95,2.6],[12.8,6.76,1],52],['lawn-relief',[9,.45,19],[12,.08,15],65],['flower-stems',[10.1,1.05,9.8],[10.5,.55,9],65]]){
    doc.authoring.views=doc.authoring.views.filter(v=>v.id!==id);
    doc.authoring.views.push({id,role:'diagnostic',projection:'perspective',position:[p[0],p[1],p[2]+(id==='lawn-relief'||id==='flower-stems'?0:offset)],target:[t[0],t[1],t[2]+(id==='lawn-relief'||id==='flower-stems'?0:offset)],fov});
  }
  writeFileSync(path,JSON.stringify(doc,null,2)+'\n');
}
