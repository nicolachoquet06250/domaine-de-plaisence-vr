import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

function glb(name) {
  const b = readFileSync(`public/gltf/castle/${name}.glb`), length = b.readUInt32LE(12);
  return { doc: JSON.parse(b.toString('utf8', 20, 20 + length)), bin: b.subarray(28 + length) };
}
const glass = glb('palaceGlass'), retained = new Set();
let centralVertices = 0;
for (const mesh of glass.doc.meshes) for (const p of mesh.primitives) {
  const a = glass.doc.accessors[p.attributes.POSITION], view = glass.doc.bufferViews[a.bufferView];
  assert.equal(a.componentType, 5126);
  for (let i = 0; i < a.count; i++) {
    const offset = (view.byteOffset ?? 0) + (a.byteOffset ?? 0) + i * (view.byteStride ?? 12);
    const x = glass.bin.readFloatLE(offset), y = glass.bin.readFloatLE(offset + 4), z = glass.bin.readFloatLE(offset + 8);
    if (Math.abs(Math.abs(x) - 21) > .02 || y < 1.2 || y > 9.1) continue;
    if (Math.abs(z) < 1.3) centralVertices++;
    if (Math.abs(Math.abs(z) - 3.7) < .86) retained.add(`${Math.sign(x)}:${y < 5 ? 0 : 1}:${Math.sign(z)}`);
  }
}
assert.equal(centralVertices, 0, 'no glass remains behind any fireplace');
assert.equal(retained.size, 8, 'all eight neighbouring end-wall windows retain glazing');
assert.equal(glb('palace').doc.nodes.filter(n => n.name?.includes('Maconnerie baie condamnee')).length, 4);
assert.equal(glb('palaceInterior').doc.nodes.filter(n => n.name?.includes('Dosseret cheminees')).length, 2);
const solids = JSON.parse(readFileSync('src/scene-assets/castle-collision-data.json'));
for (const side of [-1, 1]) {
  const solid = solids.find(s => s.position?.[0] === side * 20.3825 && s.size?.[0] === .835);
  assert.ok(solid);
  assert.ok(Math.abs(Math.abs(solid.position[0]) - solid.size[0] / 2 - 19.965) < 1e-9, 'plaster touches the frame backs');
}
for (const path of ['public/scenes/plaisance.iwsdk.scene.json', 'public/scenes/modules/castle-blender.iwsdk.scene.json']) {
  const doc = JSON.parse(readFileSync(path)); let mirrors = 0;
  function walk(nodes) { for (const n of nodes) {
    if (/^mirror-(west|east)-(salon|gallery)$/.test(n.id)) {
      mirrors++; assert.equal(Math.abs(n.transform.position[0]), 19.925, 'reflecting plane stays in front of masonry');
    }
    if (n.children) walk(n.children);
  } }
  walk(doc.nodes); assert.equal(mirrors, 4);
}
console.log('Four obstructed windows removed and infilled; eight adjacent windows preserved; chimney breasts and mirrors aligned.');
