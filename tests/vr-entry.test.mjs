import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';

const compile = path => ts.transpileModule(readFileSync(new URL(path, import.meta.url), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const devices = {};
vm.runInNewContext(compile('../src/vr-device.ts'), { exports: devices });
class Element {
  props = {}; listeners = new Map();
  setProperties(props) { Object.assign(this.props, props); }
  addEventListener(name, fn) { this.listeners.set(name, fn); }
  removeEventListener(name, fn) { if (this.listeners.get(name) === fn) this.listeners.delete(name); }
}
const quest = { userAgent: 'Mozilla/5.0 (Linux; Android 10; Quest 3) OculusBrowser/39.0', platform: 'Linux aarch64' };
function setup(device, supported = true) {
  const panels = new Map(['arrival-panel', 'estate-panel'].map(id => [id, new Map(['enter-vr', 'enter-vr-label', 'vr-status'].map(key => [key, new Element()]))]));
  let probes = 0, launches = 0;
  const xr = new Element(); xr.isSessionSupported = () => { probes++; return Promise.resolve(supported); };
  const manager = new Element(); manager.isPresenting = false;
  const exports = {};
  vm.runInNewContext(compile('../src/vr-entry.ts'), {
    exports, navigator: { ...device, xr }, isSecureContext: true,
    require: name => name === '@iwsdk/core' ? { createSystem: () => class { cleanupFuncs = []; } }
      : name === './vr-device.js' ? devices : { installVRViewHeight: () => () => {} },
  });
  const system = new exports.VREntrySystem();
  system.xrManager = manager;
  system.world = {
    getSceneObject: id => ({ requireElementById: key => panels.get(id).get(key) }),
    activeLevel: { subscribe(fn) { fn(); return () => {}; } },
    launchXR() { launches++; },
  };
  system.init();
  return { system, panels, get probes() { return probes; }, get launches() { return launches; } };
}
const settle = () => new Promise(resolve => setImmediate(resolve));

test('PCs, phones, tablets and desktop Quest emulation hide entry even with WebXR support', async () => {
  for (const device of [
    { userAgent: 'Windows Chrome', platform: 'Win32' },
    { userAgent: 'Android Mobile Chrome', platform: 'Linux aarch64' },
    { userAgent: 'iPhone Safari', platform: 'iPhone' },
    { userAgent: 'Macintosh Safari', platform: 'MacIntel' },
    { ...quest, platform: 'Win32' },
  ]) {
    const h = setup(device); await settle();
    assert.equal(h.probes, 0);
    for (const panel of h.panels.values()) {
      assert.equal(panel.get('enter-vr').props.display, 'none');
      assert.equal(panel.get('vr-status').props.display, 'none');
      assert.equal(panel.get('enter-vr').listeners.size, 0);
    }
  }
});
test('headset entry appears only after support is confirmed and launches from the click', async () => {
  const h = setup(quest);
  for (const p of h.panels.values()) assert.equal(p.get('enter-vr').props.display, 'none');
  await settle();
  for (const p of h.panels.values()) {
    assert.equal(p.get('enter-vr').props.display, 'flex');
    p.get('enter-vr').listeners.get('click')();
  }
  assert.equal(h.launches, 2);
});
test('unsupported headsets and stale asynchronous checks never reveal entry', async () => {
  const unsupported = setup(quest, false); await settle();
  for (const p of unsupported.panels.values()) assert.equal(p.get('enter-vr').props.display, 'none');
  let resolve;
  const pending = setup(quest, new Promise(r => { resolve = r; }));
  pending.system.cleanupFuncs.forEach(fn => fn()); resolve(true); await settle();
  for (const p of pending.panels.values()) assert.equal(p.get('enter-vr').props.display, 'none');
});
