import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
const code = ts.transpileModule(readFileSync(new URL('../src/voice-session.ts',import.meta.url),'utf8'), {
  compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022},
}).outputText;
const tick = async () => { for(let i=0;i<30;i++) await Promise.resolve(); };

function fixture() {
  const pcs=[], contexts=[], streams=[], sent=[], playback=[];
  const speech=[];
  class SpeechVisemes {weights=new Float32Array(15);constructor(context,source){this.source=source;speech.push(this);}sample(delta,active){this.active=active;return this.weights;}dispose(){this.disposed=true;this.weights.fill(0);}}
  class Track {kind='audio'; stopped=false; stop(){this.stopped=true;} }
  class Stream {constructor(tracks=[new Track()]){this.tracks=tracks;streams.push(this);}getTracks(){return this.tracks;}getAudioTracks(){return this.tracks;} }
  class PeerConnection {
    signalingState='stable';connectionState='new';remoteDescription=null;localDescription=null;ice=[];closed=false;
    sender={track:null,replaceTrack:async track=>{this.sender.track=track;}};
    constructor(config){this.config=config;pcs.push(this);}
    transceivers=[];
    addTransceiver(kind,options){assert.equal(kind,'audio');assert.equal(options.direction,'sendrecv');const t={sender:this.sender,receiver:{track:{kind:'audio'}},direction:options.direction};this.transceivers.push(t);return t;}
    getTransceivers(){return this.transceivers;}
    async createOffer(){return {type:'offer',sdp:'v=0\r\nm=audio'};}
    async createAnswer(){return {type:'answer',sdp:'v=0\r\nm=audio'};}
    async setLocalDescription(d){this.localDescription={...d,toJSON:()=>d};this.signalingState=d.type==='offer'?'have-local-offer':'stable';}
    async setRemoteDescription(d){this.remoteDescription=d;this.signalingState=d.type==='offer'?'have-remote-offer':'stable';if(d.type==='offer')this.transceivers.push({sender:this.sender,receiver:{track:{kind:'audio'}},direction:'recvonly'});}
    async addIceCandidate(c){assert.ok(this.remoteDescription);this.ice.push(c);}
    close(){this.closed=true;this.connectionState='closed';}
  }
  class Param {value=0;setTargetAtTime(v){this.value=v;} }
  class Node {connections=[];disconnected=false;connect(node){this.connections.push(node);return node;}disconnect(){this.disconnected=true;} }
  class Context {
    state='suspended';currentTime=1;destination=new Node();nodes=[];listener={};
    constructor(){for(const key of ['positionX','positionY','positionZ','forwardX','forwardY','forwardZ','upX','upY','upZ'])this.listener[key]=new Param();contexts.push(this);}
    createGain(){const n=new Node();n.gain=new Param();this.nodes.push(n);return n;}
    createDelay(){const n=new Node();n.delayTime=new Param();this.nodes.push(n);return n;}
    createPanner(){const n=new Node();for(const key of ['positionX','positionY','positionZ'])n[key]=new Param();this.nodes.push(n);return n;}
    createMediaStreamSource(stream){const n=new Node();n.stream=stream;this.nodes.push(n);return n;}
    async resume(){this.state='running';}
    async close(){this.state='closed';}
  }
  const exports={};
  let capture=async()=>new Stream();let captures=0;
  class VoiceSpectrum {constructor(context,source){this.source=source;}sample(active){return active?[.4,.7,.2]:[0,0,0];}dispose(){this.disposed=true;}}
  vm.runInNewContext(code,{exports,require:()=>({SpeechVisemes,VoiceSpectrum}),RTCPeerConnection:PeerConnection,AudioContext:Context,MediaStream:Stream,
    document:{createElement:tag=>{assert.equal(tag,'audio');const el={setAttribute(){},async play(){this.played=true;},pause(){this.paused=true;}};playback.push(el);return el;}},
    navigator:{mediaDevices:{getUserMedia:async()=>{captures++;return capture();}}},setTimeout,clearTimeout,console});
  const states=[];
  const session=new exports.VoiceSession(packet=>{sent.push(packet);return true;},state=>states.push({...state}));
  return {session,pcs,contexts,streams,sent,playback,speech,states,Stream,Track,exports,setCapture:fn=>{capture=fn;},captures:()=>captures};
}

test('microphone is never requested automatically; mute stops capture and removes sender tracks',async()=>{
  const h=fixture();h.session.connect('a',[]);h.session.addPeer('b');await tick();
  assert.equal(h.captures(),0);assert.equal(h.contexts.length,0);
  await h.session.toggleMicrophone();await tick();
  assert.equal(h.captures(),1);assert.equal(h.session.state.microphone,'on');
  assert.equal(h.pcs[0].sender.track,h.streams[0].getAudioTracks()[0]);
  const micSource=h.contexts[0].nodes.find(n=>n.stream===h.streams[0]);
  assert.equal(micSource.connections.length,0,'mic analysis branch has no speaker output');
  assert.equal(h.speech[0].source,micSource);
  assert.ok(h.session.localVisemes(.016));
  assert.deepEqual(h.session.localVoiceBands(),[.4,.7,.2]);
  h.session.addPeer('c');await tick();assert.equal(h.pcs[1].sender.track,h.pcs[0].sender.track);
  await h.session.toggleMicrophone();await tick();
  assert.ok(h.streams[0].getTracks().every(t=>t.stopped));
  assert.ok(h.pcs.every(pc=>pc.sender.track===null));
  assert.equal(h.speech[0].disposed,true);assert.equal(h.session.localVisemes(.016),undefined);
  assert.deepEqual(Array.from(h.session.localVoiceBands()),[0,0,0]);
  assert.equal(h.session.state.microphone,'off');h.session.dispose();
});

test('permission denial retains listening and supports a retry',async()=>{
  const h=fixture();h.session.connect('a',[]);
  h.setCapture(async()=>{throw Object.assign(new Error('denied'),{name:'NotAllowedError'});});
  await h.session.toggleMicrophone();assert.equal(h.session.state.microphone,'denied');assert.equal(h.session.state.listening,true);
  h.setCapture(async()=>new h.Stream());await h.session.toggleMicrophone();assert.equal(h.session.state.microphone,'on');h.session.dispose();
});

test('one gesture resumes listening after the browser suspends audio',async()=>{
  const h=fixture();await h.session.toggleListening();
  h.contexts[0].state='suspended';h.contexts[0].onstatechange();
  assert.equal(h.session.state.listeningPaused,true);
  await h.session.toggleListening();
  assert.equal(h.session.state.listening,true);assert.equal(h.session.state.listeningPaused,false);
  assert.equal(h.contexts[0].state,'running');h.session.dispose();
});

for(const end of ['cancel','disconnect','dispose'])test(`pending permission cannot reopen the mic after ${end}`,async()=>{
  const h=fixture();h.session.connect('a',[]);let resolve;h.setCapture(()=>new Promise(r=>{resolve=r;}));
  const pending=h.session.toggleMicrophone();
  if(end==='cancel')await h.session.toggleMicrophone();else h.session[end]();
  const stream=new h.Stream();resolve(stream);await pending;
  assert.ok(stream.getTracks().every(t=>t.stopped));assert.notEqual(h.session.state.microphone,'on');h.session.dispose();
});

test('ICE waits for SDP; only one peer offers, and stale peers cannot send after disconnect',async()=>{
  const h=fixture();h.session.connect('b',[]);h.session.addPeer('a');await tick();assert.equal(h.sent.length,0);
  assert.equal(h.pcs[0].transceivers.length,0,'answerer waits for the negotiated transceiver');
  await h.session.toggleMicrophone();await tick();
  h.session.receive({from:'a',candidate:{candidate:'candidate:x'}});await tick();assert.equal(h.pcs[0].ice.length,0);
  h.session.receive({from:'a',description:{type:'offer',sdp:'v=0\r\nm=audio'}});await tick();
  assert.equal(h.pcs[0].ice.length,1);assert.equal(h.sent[0].description.type,'answer');
  assert.equal(h.pcs[0].transceivers.length,1,'exactly one audio channel in both directions');
  assert.equal(h.pcs[0].transceivers[0].direction,'sendrecv');
  assert.equal(h.pcs[0].transceivers[0].sender.track,h.streams[0].getAudioTracks()[0]);
  h.session.receive({from:'unknown',description:{type:'offer',sdp:'x'}});await tick();assert.equal(h.pcs.length,1);
  h.session.disconnect();assert.ok(h.pcs[0].closed);h.session.connect('c',[]);h.session.addPeer('d');await tick();
  assert.equal(h.sent.at(-1).description.type,'offer');assert.equal(h.session.state.microphone,'off');h.session.dispose();
});

test('remote stream is spatialized once, follows listener/head and becomes silent beyond 25 m',async()=>{
  const h=fixture();h.session.connect('a',[]);h.session.addPeer('b');await tick();
  const track=new h.Track();h.pcs[0].ontrack({track});assert.equal(h.contexts.length,0);
  await h.session.toggleListening();
  assert.equal(h.playback.length,1);assert.equal(h.playback[0].muted,true);assert.equal(h.playback[0].played,true);
  const context=h.contexts[0];const source=context.nodes.find(n=>n.stream);const delay=source.connections[0];const panner=delay.connections[0];
  assert.equal(delay.delayTime.value,.06);
  assert.equal(panner.panningModel,'HRTF');assert.equal(panner.distanceModel,'inverse');
  const p={x:10,y:1.65,z:20};h.session.setListener(p,{x:1,y:0,z:0},{x:0,y:1,z:0});
  assert.equal(context.listener.positionX.value,10);assert.equal(context.listener.forwardX.value,1);
  assert.equal(h.session.setPeerPosition('b',{x:11,y:1.65,z:20},false),0,'hidden avatar is silent');
  const near=h.session.setPeerPosition('b',{x:11,y:1.65,z:20},true);
  const far=h.session.setPeerPosition('b',{x:20,y:1.65,z:20},true);assert.ok(near>far && far>0);
  assert.equal(h.session.setPeerPosition('b',{x:36,y:1.65,z:20},true),0);assert.equal(panner.positionX.value,36);
  assert.equal(panner.connections[0].gain.value,0);
  await h.session.toggleListening();assert.equal(h.session.setPeerPosition('b',{x:11,y:1.65,z:20},true),0);
  h.session.removePeer('b');assert.ok(source.disconnected&&panner.disconnected);assert.ok(track.stopped&&h.pcs[0].closed);
  assert.equal(h.playback[0].paused,true);assert.equal(h.playback[0].srcObject,null);
  h.session.dispose();assert.equal(context.state,'closed');
});

test('distance curve has full near volume and a continuous fade to silence',()=>{
  const {exports:e}=fixture();
  assert.equal(e.voiceDistanceGain(0),1);assert.equal(e.voiceDistanceGain(1),1);assert.equal(e.voiceDistanceGain(10),.1);
  assert.equal(e.voiceDistanceGain(25),0);assert.equal(e.voiceDistanceGain(100),0);
  let last=1;for(let d=0;d<=30;d+=.1){const gain=e.voiceDistanceGain(d);assert.ok(gain<=last+1e-12);last=gain;}
});
