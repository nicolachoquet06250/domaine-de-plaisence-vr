import fs from 'node:fs';
const path='public/scenes/arrival.iwsdk.scene.json',scene=JSON.parse(fs.readFileSync(path,'utf8'));
const palace=JSON.parse(fs.readFileSync('artifacts/arrival-landscape/plaisance-before.json','utf8'));
scene.nodes=scene.nodes.filter(n=>!n.id.startsWith('landscape-'));
const asset=(id,name,asset,position=[0,0,0])=>({id,name,content:{type:'asset',asset,castShadow:false,receiveShadow:true},transform:{position}});
scene.nodes.push(
 asset('landscape-terrain','Prairie autour du domaine','arrivalTerrain'),
 asset('landscape-forest','Foret de chenes','arrivalForest'),
 asset('landscape-path','Chemin sinueux vers le portail','arrivalPath'),
 asset('landscape-estate','Domaine au loin','arrivalEstate',[100,0,-95]),
 asset('landscape-gateway','Grand portail royal au loin','royalGateFar',[100,0,-95]),
 asset('landscape-royal-fence','Enceinte royale complete au loin','royalFenceFar',[100,0,-95]),
 {...asset('landscape-boundary','Protection invisible de la place','arrivalBoundary'),components:{StaticCollision:{},ArrivalBoundary:{}}},
);
const fountain=structuredClone(palace.nodes.find(n=>n.id==='fountain'));
function waterOnly(nodes){return nodes.flatMap(n=>{
 if(n.content?.asset==='basin'||Object.hasOwn(n.components??{},'StaticCollision'))return [];
 n.id='landscape-water/'+n.id;if(n.children)n.children=waterOnly(n.children);return [n];
});}
fountain.id='landscape-fountain';fountain.transform??={};
const p=fountain.transform.position??[0,0,0];fountain.transform.position=[p[0]+100,p[1],p[2]-95];
fountain.children=waterOnly(fountain.children??[]);scene.nodes.push(fountain);
scene.authoring.views=scene.authoring.views.filter(v=>!v.id.startsWith('landscape-'));
scene.authoring.views.push(
 {id:'landscape-vista',role:'diagnostic',projection:'perspective',fov:65,position:[3,1.65,2],target:[100,6,-115]},
 {id:'landscape-overview',role:'diagnostic',projection:'perspective',fov:57,position:[175,130,95],target:[50,0,-55]},
 {id:'landscape-top',role:'diagnostic',projection:'orthographic',height:255,position:[50,210,-60],target:[50,0,-60]},
);
fs.writeFileSync(path,JSON.stringify(scene,null,2)+'\n');
console.log('Arrival extended; original nodes and player transform retained.');
