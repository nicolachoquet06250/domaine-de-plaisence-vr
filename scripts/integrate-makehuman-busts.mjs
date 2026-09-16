import {readFile,writeFile,copyFile,mkdir} from 'node:fs/promises';
const out='artifacts/busts-makehuman';
await mkdir(`${out}/before`,{recursive:true});
const portraits=[
 {id:'royal-francois',asset:'bustFrancoisI',name:'François Ier — MakeHuman, d’après Clouet',p:[-12.8,6.14,1]},
 {id:'royal-louis',asset:'bustLouisXIV',name:'Louis XIV — MakeHuman, d’après Rigaud',p:[12.8,6.14,1]},
 {id:'royal-catherine',asset:'bustCatherineMedici',name:'Catherine de Médicis — MakeHuman, d’après Clouet',p:[-6.1,1.74,-4.25]},
 {id:'royal-anne',asset:'bustAnneFrance',name:'Anne de France — MakeHuman, d’après Jean Hey',p:[6.1,1.74,-4.25]},
];
for(const file of ['public/scenes/plaisance.iwsdk.scene.json','public/scenes/visit.iwsdk.scene.json','public/scenes/modules/castle-blender.iwsdk.scene.json']){
 const doc=JSON.parse(await readFile(file,'utf8'));
 await copyFile(file,`${out}/before/${file.split('/').at(-1)}`);
 const walk=(nodes,parentOffset=[0,0,0])=>{
  for(const n of nodes??[]){
   const offset=(n.transform?.position??[0,0,0]).map((v,i)=>v+parentOffset[i]);
   if(n.id==='castle'){
    n.children=n.children.filter(c=>!portraits.some(p=>p.id===c.id));
    n.children.push(...portraits.map(p=>({id:p.id,name:p.name,content:{type:'asset',asset:p.asset,castShadow:true,receiveShadow:true},transform:{position:p.p}})));
    doc.authoring??={};doc.authoring.views??=[];
    for(const p of portraits){
     const id='bust-'+p.id.slice(6);doc.authoring.views=doc.authoring.views.filter(v=>v.id!==id);
     const target=p.p.map((v,i)=>v+offset[i]+(i===1?.53:0));
     doc.authoring.views.push({id,role:'diagnostic',projection:'perspective',fov:44,position:[target[0]+.50,target[1]+.17,target[2]+2.1],target});
    }
   }else walk(n.children,offset);
  }
 };
 walk(doc.nodes);
 // Old authoring cameras retain stable IDs but receive the new portrait title.
 for(const v of doc.authoring?.views??[])if(v.id==='royal-louis'&&v.name)v.name='Louis XIV — Rigaud';
 await writeFile(file,JSON.stringify(doc,null,2)+'\n');
}
let assets=await readFile('src/assets.ts','utf8');await copyFile('src/assets.ts',`${out}/before/assets.ts`);
for(const id of ['palaceInterior','bustFrancoisI','bustLouisXIV'])assets=assets.replace(new RegExp(`gltf/castle/${id}\\.glb(?:\\?[^\x60]*)?`),`gltf/castle/${id}.glb?v=makehuman-busts-20260913`);
if(!assets.includes('  bustCatherineMedici:')){
 const additions=portraits.slice(2).map(p=>`  ${p.asset}: { url: \x60\${import.meta.env.BASE_URL}gltf/castle/${p.asset}.glb?v=makehuman-busts-20260913\x60, type: AssetType.GLTF, name: '${p.name}', priority: 'lazy' },`).join('\n');
 assets=assets.replace('  courtMale:',additions+'\n  courtMale:');
}
await writeFile('src/assets.ts',assets);
const review={version:'iwsdk.scene.v1',units:'meters',resources:{prefabs:[]},components:{'com.iwsdk.components.IBLGradient':{sky:[.8,.84,.9,1],equator:[.66,.65,.60,1],ground:[.24,.25,.28,1],intensity:.8},'com.iwsdk.components.DomeGradient':{sky:[.055,.075,.11,1],equator:[.09,.11,.14,1],ground:[.06,.07,.09,1],intensity:1}},authoring:{views:[{id:'hero',role:'hero',projection:'perspective',fov:40,position:[0,1.4,5.1],target:[0,.58,0]}]},nodes:[{id:'studio-key',transform:{position:[-3,4,4],rotationDeg:[-35,-30,0]},components:{DirectionalLight:{color:[1,.92,.81,1],intensity:2}}}]};
portraits.forEach((p,i)=>{
 const x=(i-1.5)*1.0;
 review.nodes.push({id:p.id,name:p.name,content:{type:'asset',asset:p.asset,castShadow:true,receiveShadow:true},transform:{position:[x,0,0]}});
 review.authoring.views.push({id:p.id,role:'diagnostic',projection:'perspective',fov:38,position:[x+.23,.75,1.85],target:[x,.59,0]});
 review.authoring.views.push({id:p.id+'-profile',role:'diagnostic',projection:'perspective',fov:36,position:[x+1.9,.81,.2],target:[x,.58,0]});
});
await writeFile('public/scenes/busts-makehuman-review.iwsdk.scene.json',JSON.stringify(review,null,2)+'\n');
console.log('Four portraits integrated in castle module, plaisance and visit; review cameras added.');
