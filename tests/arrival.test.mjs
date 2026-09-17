import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {webcrypto} from 'node:crypto';
import ts from 'typescript';
import * as nickname from '../server/nickname.mjs';
import * as avatar from '../server/avatar.mjs';

function compile(file) {
  return ts.transpileModule(readFileSync(new URL(file,import.meta.url),'utf8').replaceAll('import.meta.env.BASE_URL',"'/'"),{
    compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022},
  }).outputText;
}
const route={};vm.runInNewContext(compile('../src/room-route.ts'),{exports:route,URL,crypto:webcrypto,Uint8Array});
const id='a'.repeat(32);
test('every path stays solo without an invitation; both invitation formats work; disconnect returns to root',()=>{
  for (const path of ['/', '/visit', '/maps/plaisance/', '/app/maps/plaisance?other=1#garden']) {
    assert.equal(route.initialRoom(new URL(`https://example.test${path}`)),null);
  }
  for(const key of ['room','roomId'])assert.equal(route.initialRoom(new URL(`https://example.test/?${key}=${id}`)),id);
  assert.equal(route.initialRoom(new URL('https://example.test/?roomId=invalid')),null);
  const url=route.roomUrl(new URL(`https://example.test/visit?room=${id}&roomId=${id}#x`),null,'/');
  assert.equal(url.href,'https://example.test/');
});

function fixture(href='https://example.test/', saved=new Map()) {
  const RoomConnection={},RemoteVisitor={},elements=new Map(),sockets=[],timers=new Map(),events=new Map(),loads=[];
  const location={href,protocol:'https:'};let timer=0;
  class Element {
    style={};hidden=false;children=[];textContent='';
    set id(value){this._id=value;elements.set(value,this);}get id(){return this._id;}
    setAttribute(){} append(...els){this.children.push(...els);}remove(){} querySelector(){return null;}
  }
  class Socket {
    static OPEN=1;static CONNECTING=0;readyState=0;bufferedAmount=0;sent=[];closed=false;
    constructor(url){this.url=url;sockets.push(this);}send(packet){this.sent.push(JSON.parse(packet));}close(){this.closed=true;this.readyState=3;}
  }
  class Voice {
    state={microphone:'off',listening:false,roomConnected:false,connectedPeers:0,error:''};disconnections=0;
    constructor(_send,changed){this.changed=changed;}
    connect(){this.state.roomConnected=true;this.changed(this.state);}
    disconnect(){this.disconnections++;this.state.microphone='off';this.state.roomConnected=false;this.changed(this.state);}
    stopListening(){this.state.listening=false;this.changed(this.state);}
    dispose(){} addPeer(){} removePeer(){}
  }
  const values=new Map();const entity={object3D:{position:{set(){}}},addComponent(c,v){values.set(c,v??{});return this;},setValue(c,k,v){values.get(c)[k]=v;},getValue(c,k){return values.get(c)[k];},dispose(){}};
  const core={createSystem:()=>class{cleanupFuncs=[];queries={visitors:{entities:new Set()}};},Vector3:class{},Quaternion:class{}};
  const exports={};
  vm.runInNewContext(compile('../src/multiplayer.ts'),{exports,URL,crypto:webcrypto,Uint8Array,location,history:{replaceState(_a,_b,url){location.href=String(url);}},
    localStorage:{getItem:key=>saved.get(key)??null,setItem:(key,value)=>saved.set(key,value)},
    navigator:{onLine:true},WebSocket:Socket,document:{createElement:()=>new Element(),body:new Element()},
    window:{setInterval:()=>++timer,setTimeout:fn=>{timers.set(++timer,fn);return timer;},addEventListener:(name,fn)=>events.set(name,fn),removeEventListener:name=>events.delete(name)},
    clearTimeout:key=>timers.delete(key),clearInterval(){},console,
    require:name=>name==='@iwsdk/core'?core:name.includes('voice-session')?{VoiceSession:Voice}:name.includes('room-route')?route:name.includes('nickname.mjs')?nickname:name.includes('avatar.mjs')?avatar:name.includes('court-avatar')?{setCourtAvatar:async()=>{},releaseCourtAvatar(){}}:{RoomConnection,RemoteVisitor},
  });
  const system=new exports.MultiplayerSystem();
  const spatialElements=new Map();
  const panel={requireElementById(key){
    if(!spatialElements.has(key))spatialElements.set(key,{props:{},events:new Map(),
      element:{setAttribute(){},addEventListener(){},removeEventListener(){}},
      setProperties(props){Object.assign(this.props,props);},
      addEventListener(name,fn){this.events.set(name,fn);},removeEventListener(name){this.events.delete(name);}});
    return spatialElements.get(key);
  }};
  system.world={createTransformEntity:()=>entity,getSceneObject:key=>key==='arrival-panel'?panel:undefined,activeLevel:{subscribe:fn=>{fn();return ()=>{};}},loadLevel:async url=>{loads.push(url);}};
  system.init();
  const settle=async()=>{for(let i=0;i<15;i++)await Promise.resolve();};
  const choose = (gender='female', name='Louise') => {const input=elements.get('room-nickname');input.value=name;input.oninput();elements.get(`room-avatar-${gender}`).onclick();};
  return {system,sockets,timers,events,loads,elements,location,values,RoomConnection,settle,saved,spatialElements,choose};
}


function welcome(h, mode='observer') {
  const socket=h.sockets.at(-1);socket.readyState=1;
  socket.onmessage({data:JSON.stringify({type:'welcome',id:'local',mode,serverTime:Date.now(),peers:[],iceServers:[]})});
  return socket;
}
async function activate(h) {
  const pending=h.system.activatePresence();const socket=h.sockets.at(-1);
  const request=socket.sent.at(-1);
  socket.onmessage({data:JSON.stringify(request)});
  assert.equal(await pending,true);
}

test('saved identity and either invitation syntax always stay in arrival without loading another scene',async()=>{
  for(const key of ['room','roomId']) {
    const href=`https://example.test/?${key}=${id}`;
    const h=fixture(href,new Map([['plaisance.nickname.v2','Louise'],['plaisance.avatar.v1','female']]));await h.settle();
    assert.equal(h.system.isIdentityReady(),true);assert.equal(h.sockets.length,0);assert.equal(h.loads.length,0);
    assert.equal(h.location.href,href);h.events.get('online')();assert.equal(h.sockets.length,0);
    assert.equal(h.elements.get('room-enter').hidden,true);
    assert.equal(h.spatialElements.get('arrival-connect').props.display,'none');
    assert.match(h.spatialElements.get('arrival-status').props.text,/portillon/);
    assert.equal(h.system.prepareJourney(),true);assert.equal(h.sockets.length,0);
    h.system.connectObserver();const socket=welcome(h);
    assert.equal(new URL(socket.url).searchParams.get('room'),id);
    assert.equal(new URL(socket.url).searchParams.get('mode'),'observer');
    assert.equal(h.system.isConnected(),true);assert.equal(h.system.isParticipant(),false);
    assert.equal(h.system.voice.state.roomConnected,false);
  }
});

test('identity is required, subscribed, persisted and frozen from boarding through return',()=>{
  const h=fixture();let changes=0;const off=h.system.subscribeIdentity(()=>changes++);
  assert.equal(h.system.prepareJourney(),false);h.elements.get('room-avatar-female').onclick();
  assert.equal(h.system.prepareJourney(),false);h.choose('female','Louise du Jardin');
  assert.ok(changes>=3);assert.equal(h.saved.get('plaisance.nickname.v2'),'Louise du Jardin');
  assert.equal(h.system.prepareJourney(),true);assert.equal(h.system.prepareJourney(),false);
  h.choose('male','Wrong');h.system.connectObserver();let socket=welcome(h);
  assert.equal(new URL(socket.url).searchParams.get('nickname'),'Louise du Jardin');
  assert.equal(new URL(socket.url).searchParams.get('avatar'),'female');
  h.system.disconnectJourney();h.choose('male','Wrong again');h.system.finishJourney();
  assert.equal(h.system.prepareJourney(),true);h.system.connectObserver();socket=welcome(h);
  assert.equal(new URL(socket.url).searchParams.get('nickname'),'Louise du Jardin');
  off();const before=changes;h.system.finishJourney();assert.equal(changes,before);
  assert.equal(h.loads.length,0);
});

test('legacy enter/leave actions delegate to journey callbacks and never connect or load directly',async()=>{
  const h=fixture();let departs=0,returns=0;
  const off=h.system.setJourneyHandlers({depart:()=>departs++,return:()=>returns++});
  h.system.enterLobby();assert.equal(departs,0);h.choose();h.system.enterLobby();await h.system.leaveLobby();
  assert.equal(departs,1);assert.equal(returns,1);assert.equal(h.sockets.length,0);assert.equal(h.loads.length,0);
  off();h.system.enterLobby();assert.equal(departs,1);
});

test('observer activation requires matching acknowledgement; hiding clears local presence and voice immediately',async()=>{
  const h=fixture();h.choose();h.system.prepareJourney();h.system.connectObserver();const socket=welcome(h);
  h.system.sendPose();assert.equal(socket.sent.filter(p=>p.type==='pose').length,0);
  h.system.toggleMicrophone();h.system.toggleVoiceListening();assert.equal(h.system.voice.state.roomConnected,false);
  const pending=h.system.activatePresence(),request=socket.sent.at(-1);
  assert.equal(h.system.isParticipant(),false);assert.equal(h.system.voice.state.roomConnected,false);
  socket.onmessage({data:JSON.stringify({...request,requestId:request.requestId+1})});
  assert.equal(h.system.isParticipant(),false);
  socket.onmessage({data:JSON.stringify(request)});assert.equal(await pending,true);
  assert.equal(h.system.isParticipant(),true);assert.equal(h.system.isInLobby(),true);
  assert.equal(h.system.voice.state.roomConnected,true);
  assert.match(h.location.href,/roomId=/);assert.equal(h.elements.get('room-leave').hidden,true);
  h.system.hidePresence();assert.equal(h.system.isParticipant(),false);assert.equal(h.system.isConnected(),true);
  assert.equal(h.system.voice.state.roomConnected,false);assert.equal(socket.sent.at(-1).mode,'observer');
  h.system.sendPose();assert.equal(socket.sent.filter(p=>p.type==='pose').length,0);
  socket.onmessage({data:JSON.stringify(request)});assert.equal(h.system.isParticipant(),false,'late ack cannot revive hidden body');
});

test('return midpoint closes transport without unlocking identity; arrival unlocks and does not reconnect',async()=>{
  const h=fixture(`https://example.test/?roomId=${id}`);h.choose();h.system.prepareJourney();h.system.connectObserver();const socket=welcome(h);await activate(h);
  h.system.hidePresence();const staleClose=socket.onclose;h.system.disconnectJourney();
  assert.equal(socket.closed,true);assert.equal(h.system.isConnected(),false);assert.equal(h.system.prepareJourney(),false);
  h.system.finishJourney();assert.equal(h.location.href,'https://example.test/');
  staleClose({code:1000});h.events.get('online')();for(const fn of [...h.timers.values()])fn();
  assert.equal(h.sockets.length,1);assert.equal(h.loads.length,0);
  assert.equal(h.system.prepareJourney(),true);h.system.connectObserver();
  assert.notEqual(new URL(h.sockets.at(-1).url).searchParams.get('room'),id);
});

test('activation timeout, socket close and disposal resolve false and cannot leave participant mode pending',async()=>{
  for (const failure of ['timeout','close','dispose']) {
    const h=fixture();h.choose();h.system.prepareJourney();h.system.connectObserver();const socket=welcome(h);
    const pending=h.system.activatePresence();
    if(failure==='timeout') for(const fn of [...h.timers.values()])fn();
    else if(failure==='close'){socket.readyState=3;socket.onclose({code:1006});}
    else for(const cleanup of h.system.cleanupFuncs)cleanup();
    assert.equal(await pending,false);assert.equal(h.system.isParticipant(),false);
    if(failure==='timeout')assert.equal(socket.sent.at(-1).mode,'observer');
  }
});

test('reconnection requests observer until confirmed activation, then participant, and observer again after hiding',async()=>{
  const h=fixture();h.choose();h.system.prepareJourney();h.system.connectObserver();let socket=welcome(h);
  const reconnect=()=>{socket.readyState=3;socket.onclose({code:1006});h.events.get('online')();socket=h.sockets.at(-1);return new URL(socket.url).searchParams.get('mode');};
  assert.equal(reconnect(),'observer');welcome(h);await activate(h);
  assert.equal(reconnect(),'participant');welcome(h,'participant');assert.equal(h.system.isParticipant(),true);
  h.system.hidePresence();assert.equal(reconnect(),'observer');welcome(h);assert.equal(h.system.isParticipant(),false);
});

test('room-full and refused states stop retries but explicit observer retry is possible',()=>{
  for(const code of [4004,1008]){
    const h=fixture();h.choose();h.system.prepareJourney();h.system.connectObserver();let socket=h.sockets.at(-1);
    socket.readyState=3;socket.onclose({code});
    assert.equal(h.system.getConnectionStatus(),code===4004?'full':'refused');
    h.events.get('online')();assert.equal(h.sockets.length,1);
    h.system.connectObserver();assert.equal(h.sockets.length,2);
  }
});

test('legacy automatic nicknames and inaccessible storage never bypass personalization',()=>{
  for(const saved of [new Map([['plaisance.nickname.v1','Visiteur-6e32']]),{get(){throw Error('blocked');},set(){throw Error('blocked');}}]){
    const h=fixture(`https://example.test/?roomId=${id}`,saved);
    assert.equal(h.system.isIdentityReady(),false);assert.equal(h.system.prepareJourney(),false);assert.equal(h.sockets.length,0);
    h.choose();assert.equal(h.system.prepareJourney(),true);h.system.connectObserver();
    assert.equal(new URL(h.sockets.at(-1).url).searchParams.get('room'),id);
  }
});
