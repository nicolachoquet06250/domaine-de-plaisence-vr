import { readFileSync, writeFileSync, copyFileSync } from 'node:fs';
const path='public/scenes/plaisance.iwsdk.scene.json';
copyFileSync(path,'artifacts/garden/plaisance-before.iwsdk.scene.json');
const scene=JSON.parse(readFileSync(path,'utf8'));
let changes=0;
function visit(nodes){
  for(const node of nodes){
    if(node.content?.asset==='path'){
      const [x,,z]=node.transform.scale;
      const variant=x===7&&z===54?'pathLong':x===45&&z===7?'pathCross':x===45&&z===6?'pathTerrace':null;
      if(!variant) throw new Error(`Unmapped path dimensions ${node.id}`);
      node.content.asset=variant; changes++;
    }
    visit(node.children??[]);
  }
}
visit(scene.nodes);
if(changes!==4) throw new Error(`Expected 4 paths, got ${changes}`);
writeFileSync(path,JSON.stringify(scene,null,2)+'\n');
console.log('Updated four gravel UV variants; placements and collision nodes unchanged.');
