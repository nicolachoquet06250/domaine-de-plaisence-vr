import fs from 'node:fs';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const path='public/scenes/arrival.iwsdk.scene.json',arrival=read(path),palace=read('public/scenes/plaisance.iwsdk.scene.json');
const portal=(id,destination,position,yaw)=>({id,name:destination==='castle'?'Embarquement pour le chateau':'Retour en carrosse',content:{type:'asset',asset:'coachPortal',castShadow:false},transform:{position,rotationDeg:[0,yaw,0]},components:{CoachPortal:{destination}}});
arrival.nodes=arrival.nodes.filter(n=>!['coach-departure','coach-turning-court'].includes(n.id));
arrival.nodes.push(portal('coach-departure','castle',[7.15,0,0],90));
arrival.nodes.push({id:'coach-turning-court',name:'Aire de retournement en gravier',content:{type:'asset',asset:'coachTurningCourt',castShadow:false,receiveShadow:true}});
fs.writeFileSync(path,JSON.stringify(arrival,null,2)+'\n');
const visit=structuredClone(arrival);
visit.nodes=visit.nodes.filter(n=>!['landscape-estate','landscape-gateway','landscape-royal-fence','landscape-fountain'].includes(n.id));
// Preserve castle node IDs (systems resolve estate-panel and native door nodes by ID).
visit.nodes.push({id:'complete-estate',name:'Domaine complet pendant la visite',transform:{position:[100,0,-95]},children:palace.nodes.filter(n=>n.id!=='sun')});
function trimForecourt(nodes){for(const node of nodes){if(node.content?.asset==='ground')node.content.asset='coachEstateLawn';if(node.children)trimForecourt(node.children);}}
trimForecourt(visit.nodes);
visit.nodes.push(portal('coach-return','arrival',[100,0,-65.5],0));
visit.authoring.views.push(
 {id:'visit-gate',role:'diagnostic',projection:'perspective',position:[106,3,-51],target:[100,3,-72],fov:66},
 {id:'visit-interior',role:'diagnostic',projection:'perspective',position:[100,2,-96],target:[100,3,-109],fov:70},
 {id:'visit-overview',role:'diagnostic',projection:'perspective',position:[154,95,30],target:[60,0,-50],fov:65},
);
fs.writeFileSync('public/scenes/visit.iwsdk.scene.json',JSON.stringify(visit,null,2)+'\n');
const review={version:arrival.version,units:'meters',resources:{prefabs:[]},components:arrival.components,authoring:{views:[
 {id:'hero',role:'hero',projection:'perspective',position:[7,3.5,6],target:[2,1.3,0],fov:55},
 {id:'passenger',role:'diagnostic',projection:'perspective',position:[-.6,2.08,0],target:[7,2.08,0],fov:78},
]},nodes:[{id:'animated-coach',content:{type:'asset',asset:'royalCoachAnimated',castShadow:false}}]};
fs.writeFileSync('public/scenes/review-coach-journey.iwsdk.scene.json',JSON.stringify(review,null,2)+'\n');
console.log('Merged visit scene authored; lightweight arrival remains the initial load.');
