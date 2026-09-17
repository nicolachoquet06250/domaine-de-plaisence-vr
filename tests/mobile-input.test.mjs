import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';

const exports = {};
vm.runInNewContext(ts.transpileModule(readFileSync(new URL('../src/mobile-input.ts',import.meta.url),'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText, { exports });
const { TouchInputState, attachTouchAxes } = exports;

test('two fingers can move and look independently without stealing contacts', () => {
  const state = new TouchInputState();
  assert.equal(state.beginMove(11), true);
  assert.equal(state.beginLook(22, 200, 300), true);
  assert.equal(state.beginMove(33), false);
  assert.equal(state.beginLook(11, 0, 0), false);
  assert.equal(state.move(22, 0, -50, 50), false);
  state.move(11, 0, -50, 50);
  assert.equal(state.y, -1);
  state.end(22);
  assert.equal(state.y, -1);
  assert.equal(state.lookPointer, null);
  state.end(11);
  assert.equal(state.y, 0);
  assert.equal(state.movePointer, null);
});

test('radial dead zone ignores jitter and diagonal speed cannot exceed straight speed', () => {
  const state = new TouchInputState(); state.beginMove(1);
  state.move(1, 2, 2, 50);
  assert.equal(state.x, 0); assert.equal(state.y, 0);
  state.move(1, 50, -50, 50);
  assert.ok(Math.abs(Math.hypot(state.x,state.y)-1)<1e-12);
  state.move(1, 25, 0, 50);
  assert.ok(state.x > 0 && state.x < .5);
  state.reset();
  assert.equal(state.x,0); assert.equal(state.y,0);
});

test('SDK adapter preserves native controls and XR, blocks menus, and restores on disposal', () => {
  const state = new TouchInputState(); state.beginMove(1); state.move(1,50,0,50);
  const original = function (out) { out.x=0; out.y=-1; return out; };
  const provider = { getMoveAxis: original };
  let mobile = true, menu = false;
  const remove = attachTouchAxes(provider,state,()=>mobile,()=>menu);
  const out = {x:0,y:0};
  assert.equal(provider.getMoveAxis(out),out);
  assert.ok(out.x>0 && out.y<0 && Math.hypot(out.x,out.y)<=1);
  menu=true; provider.getMoveAxis(out);
  assert.deepEqual(out,{x:0,y:0});
  mobile=false; provider.getMoveAxis(out);
  assert.deepEqual(out,{x:0,y:-1});
  remove(); assert.equal(provider.getMoveAxis,original);
});
