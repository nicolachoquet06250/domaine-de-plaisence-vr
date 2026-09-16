import {readFileSync,writeFileSync} from 'node:fs';
for(const path of ['public/scenes/plaisance.iwsdk.scene.json','public/scenes/modules/castle-blender.iwsdk.scene.json']){
  const doc=JSON.parse(readFileSync(path));const castle=doc.nodes.find(n=>n.id==='castle');const nodes=castle?.children??doc.nodes;
  for(let i=nodes.length-1;i>=0;i--)if(nodes[i].id.startsWith('mirror-'))nodes.splice(i,1);
  for(const side of [-1,1]){
    const label=side<0?'west':'east';
    nodes.push({id:`mirror-${label}-vanity`,name:`Miroir ovale ${label}`,content:{type:'asset',asset:'mirrorOval'},components:{PalaceMirror:{}},transform:{position:[side*7,7.07,-5.163],scale:[.505,.675,1]}});
    for(const floor of [.64,5.04])nodes.push({id:`mirror-${label}-${floor<1?'salon':'gallery'}`,name:`Miroir de cheminee ${label}`,content:{type:'asset',asset:'mirrorRectangle'},components:{PalaceMirror:{}},transform:{position:[side*19.925,floor+2.53,0],rotationDeg:[0,-side*90,0],scale:[1.79,1.74,1]}});
  }
  writeFileSync(path,JSON.stringify(doc,null,2)+'\n');
}
