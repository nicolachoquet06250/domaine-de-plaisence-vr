import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { once } from 'node:events';
import { WebSocket } from 'ws';
import { attachRooms, validatePose } from '../server/rooms.mjs';
import {cleanNickname} from '../server/nickname.mjs';

const A = 'a'.repeat(32);
const B = 'b'.repeat(32);
const head = { p: [1, 1.7, 24], q: [0, 0, 0, 1] };
const pose = { type: 'pose', head, left: null, right: null };
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

test('voice bands reject malformed network input and preserve legacy poses',()=>{
  assert.ok(validatePose(pose));
  for(const voice of [[-1,0,0],[0,2,0],[0,NaN,0],[1,2],null,'loud'])assert.equal(validatePose({...pose,voice}),null);
  assert.deepEqual(validatePose({...pose,voice:[.1,.2,.3]}).voice,[.1,.2,.3]);
});

test('simultaneous speakers broadcast independent bands to every participant and return to silence',async t=>{
  const {connect}=await fixture(t),one=await connect(),two=await connect(),listener=await connect();
  const a=await one.next('welcome'),b=await two.next('welcome');await listener.next('welcome');
  one.socket.send(JSON.stringify({...pose,voice:[.8,.3,.1]}));
  two.socket.send(JSON.stringify({...pose,voice:[.1,.4,.9]}));
  const received=[await listener.next('pose'),await listener.next('pose')];
  assert.deepEqual(received.find(p=>p.id===a.id).voice,[.8,.3,.1]);
  assert.deepEqual(received.find(p=>p.id===b.id).voice,[.1,.4,.9]);
  assert.deepEqual((await one.next('pose')).voice,[.1,.4,.9]);
  assert.deepEqual((await two.next('pose')).voice,[.8,.3,.1]);
  await delay(110);one.socket.send(JSON.stringify({...pose,voice:[0,0,0]}));
  assert.deepEqual((await listener.next('pose')).voice,[0,0,0]);
});

async function fixture(t, options) {
  const server = createServer();
  const service = attachRooms(server, options);
  const clients = [];
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  t.after(async () => {
    for (const client of clients) client.terminate();
    service.close();
    await new Promise(resolve => server.close(resolve));
  });
  async function connect(room = A, wsOptions, nickname = '', avatar = '', mode = 'participant') {
    const socket = new WebSocket(`ws://127.0.0.1:${server.address().port}/rooms?room=${room}&nickname=${encodeURIComponent(nickname)}&avatar=${encodeURIComponent(avatar)}&mode=${mode}`, wsOptions);
    clients.push(socket);
    const messages = [];
    socket.on('message', data => messages.push(JSON.parse(data)));
    socket.on('error', () => {});
    await once(socket, 'open');
    const next = async type => {
      for (let i = 0; i < 100; i++) {
        const index = messages.findIndex(m => m.type === type);
        if (index >= 0) return messages.splice(index, 1)[0];
        await delay(10);
      }
      throw new Error(`Timeout waiting for ${type}`);
    };
    return { socket, messages, next };
  }
  return { connect, service, server };
}

test('nicknames are normalized and included in welcome, join and late arrivals',async t=>{
  const {connect}=await fixture(t);
  const one=await connect(A,undefined,'  Élodie   du Jardin  ');const first=await one.next('welcome');
  assert.equal(first.nickname,'Élodie du Jardin');
  const two=await connect(A,undefined,'Alex');const second=await two.next('welcome');
  assert.equal(second.peers[0].nickname,'Élodie du Jardin');
  assert.equal((await one.next('join')).nickname,'Alex');
  const late=await connect();const third=await late.next('welcome');
  assert.deepEqual(third.peers.map(p=>p.nickname),['Élodie du Jardin','Alex']);
  assert.match(third.nickname,/^Visiteur-[a-f0-9]{4}$/);
  const closed=once(two.socket,'close');two.socket.close();await closed;
  const returned=await connect(A,undefined,'Alex');assert.equal((await returned.next('welcome')).nickname,'Alex');
});

test('avatar identity survives join, late arrival and reconnect, with validated floor poses', async t => {
  const {connect} = await fixture(t);
  const one = await connect(A, undefined, 'Louise', 'female');
  const first = await one.next('welcome'); assert.equal(first.avatar, 'female');
  const two = await connect(A, undefined, 'Jean', 'male');
  const second = await two.next('welcome'); assert.equal(second.peers[0].avatar, 'female');
  assert.equal((await one.next('join')).avatar, 'male');
  const feet = {p:[1,5.04,24],q:[0,0,0,1]};
  one.socket.send(JSON.stringify({...pose, head:{...head,p:[1,6.74,24]}, feet}));
  assert.deepEqual((await two.next('pose')).feet, feet);
  const late = await connect(A, undefined, 'Other', '../../arbitrary.glb');
  const third = await late.next('welcome'); assert.equal(third.avatar, 'male');
  assert.deepEqual(third.peers.map(peer => peer.avatar), ['female','male']);
  assert.deepEqual(third.peers[0].pose.feet, feet);
  const closed = once(one.socket,'close'); one.socket.close(); await closed;
  const returned = await connect(A, undefined, 'Louise', 'female');
  assert.equal((await returned.next('welcome')).avatar, 'female');
  const invalid = once(two.socket,'close'); two.socket.send(JSON.stringify({...pose,feet:{...feet,p:[0,Infinity,0]}}));
  assert.equal((await invalid)[0],1008);
});

test('nickname normalization bounds length and removes invisible control characters',()=>{
  assert.equal(cleanNickname(null),'');assert.equal(cleanNickname('  \u202eÉlo\u0000die  '),'Élodie');
  assert.equal(Array.from(cleanNickname('😀'.repeat(40))).length,24);
  assert.equal(cleanNickname('Jean   Luc'),'Jean Luc');
  assert.equal(cleanNickname('<b>Alex</b>'),'<b>Alex</b>','plain text remains text; renderers must never interpret HTML');
});

test('two visitors exchange head and hand poses; another room stays isolated', async t => {
  const { connect } = await fixture(t);
  const one = await connect();
  const welcomeOne = await one.next('welcome');
  assert.equal(welcomeOne.peers.length, 0);
  assert.ok(Math.abs(welcomeOne.serverTime - Date.now()) < 1000);
  const two = await connect();
  const welcomeTwo = await two.next('welcome');
  assert.equal(welcomeTwo.peers[0].id, welcomeOne.id);
  assert.equal((await one.next('join')).id, welcomeTwo.id);
  const other = await connect(B);
  await other.next('welcome');
  one.socket.send(JSON.stringify({ ...pose, left: { p: [0.7, 1.2, 24], q: [0, 0, 0, 1] } }));
  const received = await two.next('pose');
  assert.equal(received.id, welcomeOne.id);
  assert.deepEqual(received.head, head);
  assert.deepEqual(received.left.p, [0.7, 1.2, 24]);
  two.socket.send(JSON.stringify(pose));
  assert.equal((await one.next('pose')).id, welcomeTwo.id);
  await delay(80);
  assert.equal(other.messages.length, 0);
});

test('leave removes membership; reconnect snapshots active peers and last poses', async t => {
  const { connect, service } = await fixture(t);
  const one = await connect();
  const first = await one.next('welcome');
  const two = await connect();
  const second = await two.next('welcome');
  two.socket.send(JSON.stringify(pose));
  await one.next('pose');
  const closed = once(one.socket, 'close');
  one.socket.close();
  await closed;
  assert.equal((await two.next('leave')).id, first.id);
  const returned = await connect();
  const welcome = await returned.next('welcome');
  assert.notEqual(welcome.id, first.id);
  assert.equal(welcome.peers.length, 1);
  assert.equal(welcome.peers[0].id, second.id);
  assert.deepEqual(welcome.peers[0].pose.head, head);
  assert.equal(service.rooms.get(A).size, 2);
});

test('invalid poses and malformed JSON close the sender without broadcasting', async t => {
  const { connect } = await fixture(t);
  const observer = await connect();
  await observer.next('welcome');
  for (const invalid of ['null', '{', JSON.stringify({ ...pose, head: { ...head, p: [99999, 0, 0] } }),
    JSON.stringify({ ...pose, head: { ...head, q: [0, 0, 0, 0] } }),
    JSON.stringify({ ...pose, left: { p: [0, 0, 0], q: [1, 2] } })]) {
    const bad = await connect();
    await bad.next('welcome');
    const closed = once(bad.socket, 'close');
    bad.socket.send(invalid);
    assert.equal((await closed)[0], 1008);
  }
  assert.equal(observer.messages.filter(m => m.type === 'pose').length, 0);
});

test('room capacity returns a specific close reason and frees departed slots', async t => {
  const { connect } = await fixture(t, { maxVisitors: 2 });
  const one = await connect();
  await one.next('welcome');
  const two = await connect();
  await two.next('welcome');
  const full = await connect();
  const [code] = await once(full.socket, 'close');
  assert.equal(code, 4004);
  const closed = once(two.socket, 'close');
  two.socket.close();
  await closed;
  const replacement = await connect();
  assert.equal((await replacement.next('welcome')).peers.length, 1);
});

test('clock replies echo timestamp; oversized packets are rejected', async t => {
  const { connect } = await fixture(t);
  const client = await connect();
  await client.next('welcome');
  const sent = Date.now();
  client.socket.send(JSON.stringify({ type: 'clock', sent }));
  const clock = await client.next('clock');
  assert.equal(clock.sent, sent);
  assert.ok(clock.serverTime >= sent);
  const closed = once(client.socket, 'close');
  client.socket.send('x'.repeat(3000));
  assert.equal((await closed)[0], 1009);
});

test('heartbeat removes unresponsive visitors and empty rooms', async t => {
  const { connect, service } = await fixture(t, { heartbeatMs: 30 });
  const client = await connect(A, { autoPong: false });
  await client.next('welcome');
  await once(client.socket, 'close');
  await delay(20);
  assert.equal(service.rooms.size, 0);
});

test('voice descriptions and ICE are targeted, sender-authenticated and room-isolated', async t => {
  const {connect} = await fixture(t, {iceServers:[{urls:'stun:example.test:3478'}]});
  const one = await connect(), a = await one.next('welcome');
  const two = await connect(), b = await two.next('welcome');
  const three = await connect(), c = await three.next('welcome');
  const other = await connect(B), d = await other.next('welcome');
  assert.deepEqual(a.iceServers, [{urls:'stun:example.test:3478'}]);
  const description = {type:'offer', sdp:'v=0\r\nm=audio 9 UDP/TLS/RTP/SAVPF 111\r\n' + 'a=x\r\n'.repeat(600)};
  one.socket.send(JSON.stringify({type:'voice-signal', to:b.id, from:c.id, description}));
  const received = await two.next('voice-signal');
  assert.equal(received.from, a.id);
  assert.deepEqual(received.description, description);
  assert.equal(received.to, undefined);
  two.socket.send(JSON.stringify({type:'voice-signal', to:a.id, candidate:{candidate:'candidate:1 1 udp 1 127.0.0.1 1234 typ host',sdpMid:'0',sdpMLineIndex:0}}));
  assert.equal((await one.next('voice-signal')).from, b.id);
  one.socket.send(JSON.stringify({type:'voice-signal', to:d.id, description}));
  await delay(60);
  assert.equal(three.messages.filter(m=>m.type==='voice-signal').length, 0);
  assert.equal(other.messages.filter(m=>m.type==='voice-signal').length, 0);
});

test('invalid voice signals never reach peers; voice burst does not consume pose quota', async t => {
  const {connect} = await fixture(t);
  const one = await connect(), a = await one.next('welcome');
  const two = await connect(), b = await two.next('welcome');
  for (let i=0;i<80;i++) one.socket.send(JSON.stringify({type:'voice-signal',to:b.id,candidate:{candidate:'',sdpMid:'0',sdpMLineIndex:0}}));
  one.socket.send(JSON.stringify(pose));
  assert.equal((await two.next('pose')).id,a.id);
  const bad = await connect(); await bad.next('welcome');
  const closed = once(bad.socket,'close');
  bad.socket.send(JSON.stringify({type:'voice-signal',to:b.id,description:{type:'offer',sdp:'x'.repeat(25000)}}));
  assert.equal((await closed)[0],1008);
  assert.equal(two.messages.some(m=>m.description),false);
});


test('observer journey is invisible to two participants and late joiners, but receives all visible poses',async t=>{
  const {connect,service}=await fixture(t);
  const one=await connect(),a=await one.next('welcome');
  const observer=await connect(A,undefined,'Voyageuse','female','observer'),o=await observer.next('welcome');
  assert.equal(o.mode,'observer');assert.deepEqual(o.peers.map(p=>p.id),[a.id]);
  const two=await connect(),b=await two.next('welcome');
  assert.deepEqual(b.peers.map(p=>p.id),[a.id]);
  assert.equal((await observer.next('join')).id,b.id);
  await one.next('join');
  observer.socket.send(JSON.stringify(pose));
  one.socket.send(JSON.stringify(pose));two.socket.send(JSON.stringify({...pose,head:{...head,p:[3,1.7,24]}}));
  const received=[await observer.next('pose'),await observer.next('pose')];
  assert.deepEqual(received.map(p=>p.id).sort(),[a.id,b.id].sort());
  await delay(50);
  for(const client of [one,two])assert.equal(client.messages.some(p=>p.id===o.id),false);
  assert.equal(service.rooms.get(A).get(o.id).pose,null);
  // Participant audio cannot target a traveller; traveller audio cannot target participants.
  observer.socket.send(JSON.stringify({type:'voice-signal',to:a.id,candidate:{candidate:''}}));
  one.socket.send(JSON.stringify({type:'voice-signal',to:o.id,candidate:{candidate:''}}));
  await delay(40);
  assert.equal(one.messages.some(p=>p.type==='voice-signal'),false);
  assert.equal(observer.messages.some(p=>p.type==='voice-signal'),false);
  observer.socket.send(JSON.stringify({type:'presence',mode:'participant',requestId:1}));
  assert.deepEqual(await observer.next('presence'),{type:'presence',mode:'participant',requestId:1});
  assert.equal((await one.next('join')).id,o.id);assert.equal((await two.next('join')).id,o.id);
  observer.socket.send(JSON.stringify(pose));
  assert.equal((await one.next('pose')).id,b.id); // previously queued participant pose
  assert.equal((await one.next('pose')).id,o.id);
  observer.socket.send(JSON.stringify({type:'presence',mode:'observer',requestId:2}));
  await observer.next('presence');assert.equal((await one.next('leave')).id,o.id);
  assert.equal((await two.next('leave')).id,o.id);assert.equal(service.rooms.get(A).get(o.id).pose,null);
  const late=await connect(),l=await late.next('welcome');
  assert.equal(l.peers.some(p=>p.id===o.id),false);
  assert.equal((await observer.next('join')).id,l.id);
  const closed=once(observer.socket,'close');observer.socket.close();await closed;await delay(30);
  assert.equal(one.messages.filter(p=>p.type==='leave'&&p.id===o.id).length,0,'hidden disconnect emits no second leave');
});

test('observer reserves capacity and repeated activation is idempotent with no stale pose on reactivation',async t=>{
  const {connect,service}=await fixture(t,{maxVisitors:2});
  const one=await connect(),a=await one.next('welcome');
  const observer=await connect(A,undefined,'Observer','male','observer'),o=await observer.next('welcome');
  const rejected=await connect(A,undefined,'Third','female','observer');assert.equal((await once(rejected.socket,'close'))[0],4004);
  for(const requestId of [1,2]){
    observer.socket.send(JSON.stringify({type:'presence',mode:'participant',requestId}));await observer.next('presence');
  }
  assert.equal((await one.next('join')).id,o.id);await delay(20);assert.equal(one.messages.some(p=>p.type==='join'),false);
  observer.socket.send(JSON.stringify(pose));await one.next('pose');
  observer.socket.send(JSON.stringify({type:'presence',mode:'observer',requestId:3}));await observer.next('presence');await one.next('leave');
  observer.socket.send(JSON.stringify({type:'presence',mode:'participant',requestId:4}));await observer.next('presence');await one.next('join');
  assert.equal(service.rooms.get(A).get(o.id).pose,null);
});
