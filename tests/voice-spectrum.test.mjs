import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
import * as core from '@iwsdk/core';
const api={};
vm.runInNewContext(ts.transpileModule(readFileSync('src/voice-spectrum.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{exports:api});

test('FFT bins distinguish low, mid and high voice frequencies at both common sample rates',()=>{
  for(const rate of [44100,48000])for(const [band,hz] of [200,1000,4000].entries()) {
    const bins=new Uint8Array(512),out=[0,0,0];bins[Math.round(hz*1024/rate)]=255;
    api.voiceBands(bins,rate,1024,out);assert.equal(out[band],1);assert.equal(out.filter(v=>v>0).length,1);
  }
});

test('microphone silence, suspension and disposal zero transmitted activity without audio output',()=>{
  let amplitude=.1,disconnected=false;
  const analyser={fftSize:1024,getFloatTimeDomainData:b=>b.fill(amplitude),getByteFrequencyData:b=>b.fill(150),disconnect:()=>disconnected=true};
  const context={currentTime:1,state:'running',sampleRate:48000,createAnalyser:()=>analyser};
  const source={connect:n=>assert.equal(n,analyser),disconnect:n=>assert.equal(n,analyser)};
  const speech=new api.VoiceSpectrum(context,source);const bands=speech.sample(true);assert.ok(bands.every(v=>v>0));
  amplitude=0;context.currentTime+=.3;assert.ok(speech.sample(true).every(v=>v===0));
  amplitude=.1;assert.ok(speech.sample(true).every(v=>v>0));
  context.state='suspended';assert.ok(speech.sample(true).every(v=>v===0));
  speech.dispose();assert.equal(disconnected,true);assert.equal(speech.bands,bands,'reuse output buffer');
});

test('nametag borders animate independently, fade stale packets and retain the text texture',()=>{
  const tags={};let textureUpdates=0;
  const context={font:'',measureText:()=>({width:200}),beginPath(){},roundRect(){},fill(){},fillText(){}};
  const document={createElement:()=>({getContext:()=>context})};
  vm.runInNewContext(ts.transpileModule(readFileSync('src/avatar-nametag.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{exports:tags,require:()=>core,document});
  const one=tags.createNameTag('Alice'),two=tags.createNameTag('Louis'),shader={uniforms:{},fragmentShader:'#include <map_fragment>'};
  one.material.onBeforeCompile(shader);const version=one.material.map.version;
  const other={uniforms:{},fragmentShader:'#include <map_fragment>'};two.material.onBeforeCompile(other);
  for(let i=0;i<10;i++)tags.animateNameTagVoice(one,[.8,.7,.6],.016);
  assert.ok(shader.uniforms.voiceBorder.value>10);assert.equal(other.uniforms.voiceBorder.value,3);
  for(let i=0;i<90;i++)tags.animateNameTagVoice(one,[1,1,1],.016,false);
  assert.ok(shader.uniforms.voiceBorder.value<3.01);assert.equal(one.material.map.version,version);
  tags.disposeNameTag(one);tags.disposeNameTag(two);
});
