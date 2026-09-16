import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';

const budgets = { bench: 3500, basin: 8000, water: 4000, lateralJet: 800, centralJet: 2000 };
const report = {};
for (const [id, budget] of Object.entries(budgets)) {
  const bytes = readFileSync(`public/gltf/estate/${id}.glb`);
  assert.equal(bytes.readUInt32LE(0), 0x46546c67);
  const jsonLength = bytes.readUInt32LE(12);
  const gltf = JSON.parse(bytes.subarray(20, 20 + jsonLength));
  const binary = bytes.subarray(28 + jsonLength);
  assert.ok((gltf.images ?? []).every(image => image.bufferView !== undefined), `${id}: embedded textures`);
  assert.ok(gltf.buffers.every(buffer => !buffer.uri), `${id}: embedded geometry`);
  const triangles = gltf.meshes.reduce((sum, mesh) => sum + mesh.primitives.reduce((n, p) => n + gltf.accessors[p.indices].count / 3, 0), 0);
  assert.ok(triangles <= budget, `${id}: triangle budget`);
  function floats(index) {
    const accessor = gltf.accessors[index];
    assert.equal(accessor.componentType, 5126);
    const view = gltf.bufferViews[accessor.bufferView];
    assert.equal(view.byteStride, undefined);
    const offset = (view.byteOffset ?? 0) + (accessor.byteOffset ?? 0);
    return Array.from({ length: accessor.count }, (_, i) => binary.readFloatLE(offset + i * 4));
  }
  const animation = [];
  for (const clip of gltf.animations ?? []) {
    for (const channel of clip.channels) {
      assert.equal(channel.target.path, 'weights');
      const node = gltf.nodes[channel.target.node];
      const mesh = gltf.meshes[node.mesh];
      const count = mesh.primitives[0].targets.length;
      const sampler = clip.samplers[channel.sampler];
      const times = floats(sampler.input);
      const weights = floats(sampler.output);
      assert.equal(times[0], 0);
      assert.equal(times.at(-1), 4);
      assert.notEqual(node.name, 'water', 'Avoid the scene group name masking the animated mesh');
      for (let i = 0; i < count; i++) assert.ok(Math.abs(weights[i] - weights[weights.length-count+i]) < 1e-5, `${id}: seamless loop`);
      for (let frame = 0; frame < times.length; frame++) {
        const sum = weights.slice(frame*count, (frame+1)*count).reduce((a,b) => a+b, 0);
        assert.ok(Math.abs(sum-1) < 1e-4, `${id}: normalized sample weights`);
      }
      // Each second must contain changing weights, guarding against held end frames.
      for (let second = 0; second < 4; second++) {
        const frames = times.map((t,i) => t >= second && t < second+1 ? i : -1).filter(i=>i>=0);
        const states = new Set(frames.map(i=>weights.slice(i*count,(i+1)*count).map(v=>v.toFixed(4)).join(',')));
        assert.ok(states.size > 3, `${id}: motion in second ${second}`);
      }
      animation.push({ mesh: node.name, duration: 4, morphTargets: count, samples: times.length });
    }
  }
  if (['water','centralJet','lateralJet'].includes(id)) assert.ok(animation.length > 0);
  report[id] = { bytes: bytes.length, triangles, drawCalls: gltf.meshes.reduce((n,m)=>n+m.primitives.length,0), animation };
}
writeFileSync('artifacts/blender/glb-verification.json', JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
