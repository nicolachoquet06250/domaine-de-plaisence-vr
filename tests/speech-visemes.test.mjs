import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import ts from 'typescript';
import {readFileSync} from 'node:fs';
const code=ts.transpileModule(readFileSync('src/speech-visemes.ts','utf8').replaceAll('import.meta.env.BASE_URL','"/"'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const binary=readFileSync('public/vendor/headaudio/model-en-mixed.bin');
function fixture(defer=false){
  const api={},nodes=[];let release;
  const gate=defer?new Promise(r=>release=r):Promise.resolve();
  const context={currentTime:1,state:'running',audioWorklet:{addModule:()=>gate}};
  class Worklet{constructor(ctx,name,options){this.options=options;this.sent=[];this.port={postMessage:m=>this.sent.push(m),close:()=>this.closed=true};nodes.push(this);}disconnect(){this.disconnected=true;}}
  vm.runInNewContext(code,{exports:api,AudioWorkletNode:Worklet,fetch:async()=>({ok:true,arrayBuffer:async()=>binary.buffer.slice(binary.byteOffset,binary.byteOffset+binary.byteLength)}),console});
  const source={connections:[],connect(n){this.connections.push(n);},disconnect(n){this.connections=this.connections.filter(x=>x!==n);}};
  return {api,context,source,nodes,release};
}
test('acoustic model contains finite prototypes for the 15 articulations',()=>{
  const {api}=fixture();const model=api.decodeVisemeModel(binary.buffer.slice(binary.byteOffset,binary.byteOffset+binary.byteLength));
  assert.equal(model.length,39);assert.equal(new Set(model.map(p=>p.viseme)).size,15);
  assert.throws(()=>api.decodeVisemeModel(new ArrayBuffer(4)),/size/);
});
test('worklet recognizes viseme zero, blends sounds and closes on silence, stale audio and pause',async()=>{
  const h=fixture(),speech=new h.api.SpeechVisemes(h.context,h.source);await speech.ready;
  const node=h.nodes[0];assert.equal(node.options.numberOfOutputs,0,'microphone cannot feed speaker output');
  assert.equal(speech.status,'ready');assert.equal(node.sent[0].event,'model');
  const emit=viseme=>node.port.onmessage({data:{event:'viseme',viseme}});
  emit(0);for(let i=0;i<8;i++)speech.sample(.016);assert.ok(speech.weights[0]>.7,'aa id=0 must not be treated as false');
  emit(4);speech.sample(.016);assert.ok(speech.weights[0]>0&&speech.weights[4]>0,'coarticulation crossfade');
  node.port.onmessage({data:{event:'ended'}});for(let i=0;i<30;i++)speech.sample(.016);assert.ok(speech.weights.every(n=>n<.001));
  emit(3);speech.sample(.1);h.context.currentTime+=1;for(let i=0;i<30;i++)speech.sample(.016);assert.ok(speech.weights.every(n=>n<.001));
  speech.sample(.016,false);assert.equal(node.sent.at(-1).event,'stop');
  emit(0);speech.sample(.016,false);assert.ok(speech.weights[0]<.001,'ignore events while inactive');
  speech.sample(.016,true);assert.equal(node.sent.at(-1).event,'start');
  speech.dispose();assert.equal(speech.status,'disposed');assert.equal(h.source.connections.length,0);assert.equal(node.closed,true);
});
test('disconnect while loading cannot resurrect a microphone or attach a worklet',async()=>{
  const h=fixture(true),speech=new h.api.SpeechVisemes(h.context,h.source);speech.dispose();h.release();await speech.ready;
  assert.equal(h.nodes.length,0);assert.equal(speech.status,'disposed');assert.equal(h.source.connections.length,0);
});
