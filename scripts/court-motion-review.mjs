import {readFileSync,writeFileSync} from 'node:fs';
const path='public/scenes/modules/court-review.iwsdk.scene.json';
const doc=JSON.parse(readFileSync(path));
for(const [id,position,target,fov] of [
  ['coiffures-rear',[0,1.15,-3.5],[0,.92,0],46],
  ['court-lady-face',[.68,1.57,.70],[.60,1.53,0],43],
]) {
  doc.authoring.views=doc.authoring.views.filter(v=>v.id!==id);
  doc.authoring.views.push({id,role:'diagnostic',projection:'perspective',position,target,fov});
}
writeFileSync(path,JSON.stringify(doc,null,2)+'\n');
