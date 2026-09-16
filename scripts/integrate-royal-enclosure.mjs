import fs from 'node:fs';
const asset=(id,name,asset,position=[0,0,0])=>({id,name,content:{type:'asset',asset,castShadow:false,receiveShadow:true},transform:{position}});
const palacePath='public/scenes/plaisance.iwsdk.scene.json',arrivalPath='public/scenes/arrival.iwsdk.scene.json';
const palace=JSON.parse(fs.readFileSync(palacePath,'utf8')),arrival=JSON.parse(fs.readFileSync(arrivalPath,'utf8'));
function removeOldBorders(nodes){return nodes.filter(n=>n.content?.asset!=='gardenBorder'&&n.id!=='royal-enclosure').map(n=>{if(n.children)n.children=removeOldBorders(n.children);return n;});}
palace.nodes=removeOldBorders(palace.nodes);
palace.nodes.push({id:'royal-enclosure',name:'Enceinte et portail royaux',children:[
 asset('royal-enclosure/gate','Grand portail royal','royalGate'),
 asset('royal-enclosure/fence','Clotures en fer forge ornees','royalFence'),
 {...asset('royal-enclosure/collision','Collision enceinte et vantaux','royalEnclosureCollision'),components:{StaticCollision:{}}},
 {...asset('royal-enclosure/approach','Gravier sous le portail','royalGateApproach'),children:[{
  ...asset('royal-enclosure/approach/collision','Collision raccord gravier','pathCollision',[0,.008,29]),
  transform:{position:[0,.008,29],scale:[7,1,4]},components:{StaticCollision:{}}
 }]},
]});
arrival.nodes=arrival.nodes.filter(n=>n.id!=='landscape-royal-fence');
const gate=arrival.nodes.find(n=>n.id==='landscape-gateway');gate.content.asset='royalGateFar';gate.name='Grand portail royal au loin';gate.transform={position:[100,0,-95]};
arrival.nodes.push(asset('landscape-royal-fence','Enceinte royale complete au loin','royalFenceFar',[100,0,-95]));
function views(doc,items){doc.authoring.views=doc.authoring.views.filter(v=>!items.some(item=>item.id===v.id));doc.authoring.views.push(...items);}
views(palace,[
 {id:'royal-gate',role:'diagnostic',projection:'perspective',position:[12,5,48],target:[0,4,30],fov:58},
 {id:'royal-gate-detail',role:'diagnostic',projection:'perspective',position:[8,3.5,33],target:[3.8,2.8,27.4],fov:60},
 {id:'royal-enclosure-overview',role:'diagnostic',projection:'perspective',position:[80,83,88],target:[0,0,-5],fov:58},
]);
views(arrival,[
 {id:'royal-gate',role:'diagnostic',projection:'perspective',position:[112,5,-47],target:[100,4,-65],fov:58},
 {id:'arrival-path-junction',role:'diagnostic',projection:'perspective',position:[13,9,8],target:[8,0,0],fov:55},
]);
for(const [path,doc] of [[palacePath,palace],[arrivalPath,arrival]])fs.writeFileSync(path,JSON.stringify(doc,null,2)+'\n');
console.log('Royal enclosure installed in both scenes; circular arrival placements retained.');
