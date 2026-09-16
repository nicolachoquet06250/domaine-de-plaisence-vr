import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const data = readFileSync('public/gltf/castle/hearth.glb');
const gltf = JSON.parse(data.toString('utf8', 20, 20 + data.readUInt32LE(12)));
assert.equal(gltf.scenes.length, 1, 'export contains only the new Blender scene');
assert.equal(gltf.meshes.length, 1, 'one shared mesh, no accidental castle export');
assert.equal(gltf.materials.length, 6);
let triangles = 0;
for (const primitive of gltf.meshes[0].primitives) {
  const a = gltf.accessors[primitive.attributes.POSITION];
  assert.ok(a.min[0] >= -.84 && a.max[0] <= .84, 'fits the 1.68 m opening');
  assert.ok(a.min[1] >= -.011 && a.max[1] <= 1.09, 'backing seats 1 cm into the slab; top stays under lintel');
  assert.ok(a.min[2] >= -.14 && a.max[2] <= .48, 'fits in front of the black back and on the stone slab');
  triangles += gltf.accessors[primitive.indices].count / 3;
}
assert.ok(triangles <= 15000 && data.length <= 800000, 'VR asset budget');
for (const path of ['public/scenes/plaisance.iwsdk.scene.json', 'public/scenes/modules/castle-blender.iwsdk.scene.json']) {
  const doc = JSON.parse(readFileSync(path));
  assert.ok(!doc.imports, 'preserve flattened scenes');
  const nodes = doc.nodes.find(n => n.id === 'castle')?.children ?? doc.nodes;
  const fires = nodes.filter(n => n.components?.HearthFire);
  assert.equal(fires.length, 4);
  for (const fire of fires) {
    assert.equal(fire.children.filter(n => n.content?.asset === 'hearth').length, 1);
    assert.equal(fire.children.filter(n => n.content?.asset === 'hearthFire').length, 1);
    const glow = fire.children.find(n => n.components?.HearthGlow);
    assert.equal(glow.components.PointLight.castShadow, false);
    assert.ok(glow.components.PointLight.distance <= 3);
    const [x, y, z] = fire.transform.position;
    assert.ok(Math.abs(x) === 19.84 && z === 0 && (Math.abs(y - .82) < 1e-8 || Math.abs(y - 5.22) < 1e-8));
    assert.equal(fire.transform.rotationDeg[1], x > 0 ? -90 : 90, 'screen faces the room');
  }
}
console.log(JSON.stringify({ fireplaces: 4, trianglesPerInsert: triangles, sharedAssetBytes: data.length, materialPrimitives: 6, flameTrianglesPerFire: 32 }));
