import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
import { EventDispatcher } from '@iwsdk/core';
import { XRRigidTransform } from 'iwer/lib/primitives/XRRigidTransform.js';
import { XRReferenceSpace } from 'iwer/lib/spaces/XRReferenceSpace.js';
import { XRSpaceUtils } from 'iwer/lib/spaces/XRSpace.js';

const api = {};
vm.runInNewContext(ts.transpileModule(readFileSync(new URL('../src/vr-view-height.ts', import.meta.url), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText, { exports: api, XRRigidTransform: class { constructor(position) { this.position = position; } } });

function space(offset = 0) {
  return { offset, getOffsetReferenceSpace: transform => space(offset + transform.position.y) };
}
class XR extends EventDispatcher {
  isPresenting = false;
  reference = null;
  getReferenceSpace() { return this.reference; }
  setReferenceSpace(value) { this.reference = value; }
  start() { this.reference = space(); this.isPresenting = true; this.dispatchEvent({ type: 'sessionstart' }); }
  end() { this.reference = null; this.isPresenting = false; this.dispatchEvent({ type: 'sessionend' }); }
}

test('VR raises headset and hands by 20 cm without changing their relative pose', () => {
  const xr = new XR(); const dispose = api.installVRViewHeight(xr);
  assert.equal(xr.reference, null, 'desktop reference space is untouched');
  xr.start();
  const head = 1.6 - xr.reference.offset, hand = 1.2 - xr.reference.offset;
  assert.ok(Math.abs(head - 1.8) < 1e-10);
  assert.ok(Math.abs(hand - 1.4) < 1e-10);
  assert.ok(Math.abs((head - hand) - .4) < 1e-10);
  const raised = xr.reference;
  xr.dispatchEvent({ type: 'sessionstart' });
  assert.equal(xr.reference, raised, 'repeated start never stacks the height offset');
  xr.end(); xr.start();
  assert.equal(xr.reference.offset, -.2, 'second VR session starts from a fresh origin');
  dispose(); assert.equal(xr.reference.offset, 0, 'teardown restores original tracking');
  xr.end(); xr.start(); assert.equal(xr.reference.offset, 0, 'listeners are removed');
});

test('initialization in an active session raises it once and respects a later reference-space owner', () => {
  const xr = new XR(); xr.start(); const dispose = api.installVRViewHeight(xr);
  assert.equal(xr.reference.offset, -.2);
  const replacement = space(-.6); xr.setReferenceSpace(replacement);
  dispose(); assert.equal(xr.reference, replacement);
});

test('installed IWER evaluates a finite translated reference matrix, matching native WebXR', () => {
  const previous = globalThis.DOMPointReadOnly;
  globalThis.DOMPointReadOnly = class { constructor(x, y, z, w) { Object.assign(this, { x, y, z, w }); } };
  try {
    const emulatorApi = {};
    vm.runInNewContext(ts.transpileModule(readFileSync(new URL('../src/vr-view-height.ts', import.meta.url), 'utf8'), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
    }).outputText, { exports: emulatorApi, XRRigidTransform });
    const xr = new XR(); xr.isPresenting = true;
    xr.reference = new XRReferenceSpace('local-floor');
    const dispose = emulatorApi.installVRViewHeight(xr);
    const matrix = XRSpaceUtils.calculateGlobalOffsetMatrix(xr.reference);
    assert.ok([...matrix].every(Number.isFinite));
    assert.ok(Math.abs(matrix[13] + .2) < 1e-7);
    assert.deepEqual([matrix[12], matrix[14]], [0, 0]);
    dispose();
  } finally {
    if (previous === undefined) delete globalThis.DOMPointReadOnly;
    else globalThis.DOMPointReadOnly = previous;
  }
});
