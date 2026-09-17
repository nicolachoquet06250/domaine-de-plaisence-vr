import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const json=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const before=json('artifacts/arrival-landscape/arrival-before.json'),after=json('public/scenes/arrival.iwsdk.scene.json');
test('arrival keeps existing placement, UI and spawn; palace keeps non-boundary placements',()=>{
 for(const node of before.nodes)assert.deepEqual(after.nodes.find(n=>n.id===node.id),node);
 assert.deepEqual(after.player,before.player);
 const omitBorders=nodes=>nodes.filter(n=>n.content?.asset!=='gardenBorder'&&n.id!=='royal-enclosure').map(n=>{const copy=structuredClone(n);if(copy.children)copy.children=omitBorders(copy.children);return copy;});
 assert.deepEqual(omitBorders(json('public/scenes/plaisance.iwsdk.scene.json').nodes),omitBorders(json('artifacts/arrival-landscape/plaisance-before.json').nodes));
 assert.equal(after.imports,undefined);
});
test('distant estate includes exterior placements only and keeps the approved offset',()=>{
 const source=json('artifacts/arrival-landscape/exterior-placements.json');
 assert.equal(source.placements.length,51);
 for(const item of source.placements)assert.doesNotMatch(item.path,/interior|furniture|bust|mirror|hearth|avatar/i);
 assert.deepEqual(after.nodes.find(n=>n.id==='landscape-estate').transform.position,[100,0,-95]);
});
test('forest and connecting path leave the plaza, avenue and estate clear',()=>{
 const trees=json('artifacts/arrival-landscape/forest-placements.json'),path=json('artifacts/arrival-landscape/path.json');
 assert.equal(trees.length,132);assert.deepEqual(path.samples.at(-1),[100,-68]);assert.equal(path.widthEnd,7);
 for(const tree of trees){
  assert.ok(Math.hypot(tree.x,tree.z)>=19);
  assert.ok(!(tree.x>57&&tree.x<143&&tree.z>-154&&tree.z<-49));
  assert.ok(path.samples.every(([x,z])=>Math.hypot(tree.x-x,tree.z-z)>=9));
 }
});
test('all new GLBs are embedded and leaf materials use alpha cutout without blending',()=>{
 for(const name of ['forest','terrain','path','estateExterior','gateway','oak1','oak1Far','oak2','oak2Far','oak3','oak3Far']){
  const b=fs.readFileSync(`public/gltf/arrival-landscape/${name}.glb`);
  assert.equal(b.readUInt32LE(0),0x46546c67);assert.equal(b.readUInt32LE(8),b.length);
  const gltf=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)).toString());
  assert.ok(gltf.meshes.length);assert.ok(gltf.buffers.every(v=>!v.uri));assert.ok((gltf.images??[]).every(v=>!v.uri));
  for(const m of gltf.materials)if(m.name.startsWith('Feuilles decoupees'))assert.equal(m.alphaMode,'MASK');
 }
 const stats=json('artifacts/arrival-landscape/asset-stats.json').assets;
 assert.ok(stats.forest.triangles<90000);assert.ok(stats.estateExterior.triangles<120000);
});
