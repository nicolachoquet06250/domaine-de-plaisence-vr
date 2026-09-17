import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import ts from 'typescript';
import * as core from '@iwsdk/core';
import { Locomotor } from '@iwsdk/locomotor';

// Run the actual procedural prototypes with the SDK's own Three.js exports.
const cache = new Map();
function load(url) {
  if (cache.has(url.href)) return cache.get(url.href);
  const exports = {};
  cache.set(url.href, exports);
  const code = ts.transpileModule(readFileSync(url, 'utf8'), {
    compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022},
  }).outputText;
  new Function('exports', 'require', code)(exports, (name) => {
    if (name === '@iwsdk/core') return core;
    return load(new URL(name.replace(/\.js$/, '.ts'), url));
  });
  return exports;
}
const assetUrl = (name) => new URL(`../src/scene-assets/${name}`, import.meta.url);
const { createStaticCollision } = load(assetUrl('static-collision.ts'));
const { default: palace } = load(assetUrl('palace.scene-asset.ts'));
const garden = load(assetUrl('garden.scene-asset.ts'));
const { basin } = load(assetUrl('fountain.scene-asset.ts'));
const solids = {palace, ...garden, basin};
const collisions = Object.fromEntries(Object.entries(solids).map(([id, source]) => [id, createStaticCollision(source)]));
const {BoxGeometry, Group, Mesh, InstancedMesh, Matrix4, MeshBasicMaterial, Vector3, Box3} = core;

test('expands translated, rotated, scaled instances and mixed indexed/non-indexed geometry', () => {
  const root = new Group();
  root.position.set(100, 2, -20); // Root placement belongs to composition, not baked vertices.
  const branch = new Group(); branch.position.x = 4; root.add(branch);
  const geometry = new BoxGeometry(2, 2, 2);
  const repeated = new InstancedMesh(geometry, new MeshBasicMaterial(), 2);
  repeated.position.z = 3;
  repeated.setMatrixAt(0, new Matrix4().makeTranslation(0, 0, 5));
  repeated.setMatrixAt(1, new Matrix4().makeRotationY(Math.PI / 2).scale(new Vector3(2, 1, 1)).setPosition(-8, 0, 0));
  branch.add(repeated);
  const plain = new Mesh(geometry.toNonIndexed(), new MeshBasicMaterial());
  plain.position.y = 7; root.add(plain);
  const collider = createStaticCollision(root);
  const baked = collider.children[0].geometry;
  assert.equal(baked.index.count, 36 * 3);
  assert.deepEqual(Array.from(baked.index.array.slice(0,36)), Array.from(geometry.index.array));
  assert.deepEqual(Array.from(baked.index.array.slice(72)), Array.from({length:36}, (_, i) => i + 48));
  assert.deepEqual(baked.boundingBox.min.toArray(), [-5, -1, -1]);
  assert.deepEqual(baked.boundingBox.max.toArray(), [5, 8, 9]);
  assert.deepEqual(Object.keys(baked.attributes), ['position']);
  assert.equal(collider.children[0].material.visible, false);
  assert.equal(collider.parent, null);
  assert.equal(repeated.geometry, geometry);
  assert.equal(geometry.index.count, 36);
  assert.equal(collider.clone(true).children[0].geometry, baked);
});

test('every solid prototype retains all triangles and its exact geometry bounds', (t) => {
  for (const [id, source] of Object.entries(solids)) {
    let expected = 0;
    source.traverse(mesh => {
      if (mesh.isMesh) expected += (mesh.geometry.index?.count ?? mesh.geometry.attributes.position.count) * (mesh.isInstancedMesh ? mesh.count : 1);
    });
    const geometry = collisions[id].children[0].geometry;
    assert.equal(geometry.index.count, expected, id);
    assert.ok(geometry.attributes.position.array.every(Number.isFinite), id);
    // Box3's InstancedMesh shortcut encloses transformed bounding boxes, which
    // overestimates rotated foliage. Expand clones for an independent precise bound.
    const expanded = source.clone(true);
    const instances = [];
    expanded.traverse(mesh => { if (mesh.isInstancedMesh) instances.push(mesh); });
    for (const batch of instances) {
      const group = new Group(); group.copy(batch, false);
      for (let i = 0; i < batch.count; i++) {
        const mesh = new Mesh(batch.geometry, batch.material);
        batch.getMatrixAt(i, mesh.matrix); mesh.matrixAutoUpdate = false;
        group.add(mesh);
      }
      batch.parent.add(group); batch.removeFromParent();
    }
    const bounds = new Box3().setFromObject(expanded, true);
    assert.ok(bounds.min.distanceTo(geometry.boundingBox.min) < 0.0001, `${id} min`);
    assert.ok(bounds.max.distanceTo(geometry.boundingBox.max) < 0.0001, `${id} max`);
    t.diagnostic(`${id}: ${expected / 3} collision triangles`);
  }
});

const doc = JSON.parse(readFileSync(new URL('../public/scenes/plaisance.iwsdk.scene.json', import.meta.url), 'utf8'));
test('each solid scene placement has one inherited collision child; fluids and UI remain traversable', () => {
  let solidCount = 0, environmentCount = 0;
  const excluded = new Set(['water','centralJet','lateralJet','estate-panel']);
  function visit(nodes) {
    for (const node of nodes) {
      const asset = node.content?.asset;
      const env = Object.keys(node.components ?? {}).some(k => /(^|\.)StaticCollision$/.test(k));
      if (env) {
        environmentCount++;
        assert.ok(asset.endsWith('Collision'), node.id);
      }
      if (asset && !asset.endsWith('Collision') && !excluded.has(asset)) {
        assert.ok(solids[asset], `Uncovered solid: ${asset}`);
        const child = node.children?.filter(n => n.content?.asset === asset + 'Collision');
        assert.equal(child?.length, 1, node.id);
        assert.equal(child[0].transform, undefined, node.id);
        assert.equal(env, false, 'Do not collect both visible meshes and collision proxies');
        solidCount++;
      }
      if (excluded.has(asset)) assert.equal(env, false, asset);
      visit(node.children ?? []);
    }
  }
  visit(doc.nodes);
  assert.equal(solidCount, 49);
  assert.equal(environmentCount, solidCount);
});

test('deferred activation captures ancestor translation, rotation and scale before registering with Locomotor', async () => {
  const { StaticCollisionSystem } = load(new URL('../src/static-collisions.ts', import.meta.url));
  const engine = new Locomotor({useWorker:false});
  await engine.initialize();
  try {
    const parent = new Group();
    parent.position.set(12, 0, -28);
    parent.rotation.y = Math.PI / 2;
    parent.scale.set(2, 1, 3);
    const collider = collisions.bench.clone(true);
    const pending = new Set();
    const entity = {object3D:collider, addComponent(component) {
      assert.equal(component, core.LocomotionEnvironment);
      engine.addEnvironment(collider);
      pending.delete(this);
    }};
    pending.add(entity);
    const system = {queries:{pending:{entities:pending}}};
    StaticCollisionSystem.prototype.update.call(system);
    assert.equal(pending.size, 1, 'wait for TransformSystem to attach the hierarchy');
    parent.add(collider);
    StaticCollisionSystem.prototype.update.call(system);
    assert.equal(pending.size, 0);
    // Public hit test uses the registered BVH, not the visual mesh hierarchy.
    // Aim at the slat at local z=.08; z=0 is an intentional gap in the seat.
    engine.requestHitTest(new Vector3(12.24, 2, -28), new Vector3(0, -1, 0));
    assert.equal(engine.hitTestTarget.visible, true);
    assert.ok(engine.hitTestTarget.position.y > .5 && engine.hitTestTarget.position.y < 1.1);
    assert.ok(Math.abs(engine.hitTestTarget.position.x - 12.24) < 1e-5);
  } finally { engine.terminate(); }
});

async function engineFor(asset, start) {
  const locomotor = new Locomotor({useWorker:false, initialPlayerPosition:new Vector3(...start)});
  await locomotor.initialize();
  locomotor.addEnvironment(collisions.ground.clone(true));
  locomotor.addEnvironment(collisions[asset].clone(true));
  for (let i = 0; i < 120; i++) locomotor.update(1 / 90);
  return locomotor;
}
function walk(engine, direction, frames = 450) {
  const step = new Vector3(...direction).multiplyScalar(2);
  for (let i = 0; i < frames; i++) { engine.slide(step); engine.update(1 / 90); }
  return engine.position.clone();
}

test('actual Locomotor climbs the palace stairs, then stops at the closed entrance', async () => {
  const engine = await engineFor('palace', [0, 0, 11]);
  try {
    const top = walk(engine, [0, 0, -1], 350);
    assert.ok(top.y > .48 && top.y < .8, `stairs ${top.toArray()}`);
    const wall = walk(engine, [0, 0, -1]);
    assert.ok(wall.z > 6 && wall.z < 8, `facade ${wall.toArray()}`);
  } finally { engine.terminate(); }
});

test('actual Locomotor cannot pass through the instanced palace balustrade', async () => {
  const engine = await engineFor('palace', [12, 0, 11]);
  try {
    const position = walk(engine, [0, 0, -1]);
    assert.ok(position.z > 7 && position.z < 7.6, `railing ${position.toArray()}`);
    assert.ok(position.y > .4 && position.y < .8, 'feet remain on the staircase');
  } finally { engine.terminate(); }
});

for (const [asset, start, limit] of [
  ['cypress', [0, 0, 3], .2],
  ['bench', [0, 0, 3], .2],
  ['gardenBorder', [0, 0, 3], .2],
]) {
  test(`actual Locomotor stops at ${asset}`, async () => {
    const engine = await engineFor(asset, start);
    try {
      const position = walk(engine, [0, 0, -1]);
      assert.ok(position.z > limit && position.z < start[2] - .2, `${asset}: ${position.toArray()}`);
    } finally { engine.terminate(); }
  });
}

test('rounded urn deflects the player around its solid body', async () => {
  const engine = await engineFor('urn', [0, 0, 3]);
  try {
    const position = walk(engine, [0, 0, -1]);
    assert.ok(Math.abs(position.x) > .8, `must walk around the vase: ${position.toArray()}`);
  } finally { engine.terminate(); }
});

for (const [asset, start, height] of [
  ['parterre', [0, 0, 9], .4],
  ['basin', [0, 0, 7], .65],
]) {
  test(`low ${asset} surfaces support the player when climbed`, async () => {
    const engine = await engineFor(asset, start);
    let peak = 0;
    try {
      for (let frame = 0; frame < 450; frame++) {
        const position = walk(engine, [0, 0, -1], 1);
        peak = Math.max(peak, position.y);
        assert.ok(position.y > -.02, 'must stay above ground');
      }
      assert.ok(peak > height, `must rise onto solid surfaces, peak=${peak}`);
    } finally { engine.terminate(); }
  });
}
