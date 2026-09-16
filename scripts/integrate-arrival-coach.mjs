import fs from 'node:fs';
const path='public/scenes/arrival.iwsdk.scene.json';
const scene=JSON.parse(fs.readFileSync(path,'utf8'));
const report=JSON.parse(fs.readFileSync('artifacts/arrival-coach/model-stats.json','utf8'));
const asset=(id,name,asset,position,rotationDeg=[0,0,0])=>({id,name,content:{type:'asset',asset,castShadow:true,receiveShadow:true},transform:{position,rotationDeg}});
const additions=[
 asset('arrival-wicket','Portillon royal ferme','arrivalWicket',report.gatePosition,report.gateRotationDeg),
 asset('arrival-coach','Attelage royal a cinq metres du portillon','royalCoach',report.coachPosition,report.coachRotationDeg),
];
scene.nodes=scene.nodes.filter(n=>!additions.some(a=>a.id===n.id));scene.nodes.push(...additions);
const views=[
 {id:'arrival-wicket',role:'diagnostic',projection:'perspective',position:[5,1.65,2.4],target:[9.8,1,0],fov:66},
 {id:'arrival-coach',role:'diagnostic',projection:'perspective',position:[17,4.2,8],target:[14.5,1.5,-.6],fov:54},
 {id:'arrival-exit-top',role:'diagnostic',projection:'orthographic',height:19,position:[11,23,0],target:[11,0,0]},
 {id:'arrival-spawn',role:'diagnostic',projection:'perspective',position:[0,1.65,2],target:[0,2,-4],fov:75},
];
scene.authoring.views=scene.authoring.views.filter(v=>!views.some(a=>a.id===v.id));scene.authoring.views.push(...views);
fs.writeFileSync(path,JSON.stringify(scene,null,2)+'\n');
const review={version:scene.version,units:'meters',resources:{prefabs:[]},components:scene.components,environment:scene.environment,authoring:{views:[
 {id:'hero',role:'hero',projection:'perspective',position:[8,4,7],target:[2.2,1.3,0],fov:52},
 {id:'horses',role:'diagnostic',projection:'perspective',position:[7.8,2.8,4],target:[4.1,1.2,0],fov:48},
 {id:'wicket',role:'diagnostic',projection:'perspective',position:[2,1.6,3],target:[0,.6,0],fov:45},
]},nodes:[asset('coach','Attelage royal','royalCoach',[0,0,0])]};
fs.writeFileSync('public/scenes/review-coach.iwsdk.scene.json',JSON.stringify(review,null,2)+'\n');
review.nodes=[asset('wicket','Portillon','arrivalWicket',[0,0,0])];review.authoring.views=review.authoring.views.filter(v=>v.id==='wicket');
fs.writeFileSync('public/scenes/review-wicket.iwsdk.scene.json',JSON.stringify(review,null,2)+'\n');
console.log('Arrival coach and wicket integrated; both original collision nodes preserved.');
