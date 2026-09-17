import { randomUUID } from 'node:crypto';
import { WebSocketServer, WebSocket } from 'ws';
import { MAX_VOICE_PACKET, validateVoiceSignal, voiceIceServers } from './voice-signaling.mjs';
import { visitorNickname } from './nickname.mjs';
import { visitorAvatar } from './avatar.mjs';

export const ROOM_PATTERN = /^[a-f0-9]{32}$/;
const MAX_BUFFER = 64 * 1024;

function transform(value) {
  if (!value || !Array.isArray(value.p) || value.p.length !== 3 ||
    !Array.isArray(value.q) || value.q.length !== 4) return null;
  if (!value.p.every(n => Number.isFinite(n) && Math.abs(n) <= 1000) ||
    !value.q.every(n => Number.isFinite(n) && Math.abs(n) <= 1)) return null;
  const norm = Math.hypot(...value.q);
  if (norm < 0.9 || norm > 1.1) return null;
  return { p: value.p, q: value.q.map(n => n / norm) };
}

export function validatePose(message) {
  if (message?.type !== 'pose') return null;
  const head = transform(message.head);
  if (!head) return null;
  const left = message.left == null ? null : transform(message.left);
  const right = message.right == null ? null : transform(message.right);
  if ((message.left != null && !left) || (message.right != null && !right)) return null;
  const feet = message.feet == null ? null : transform(message.feet);
  if (message.feet != null && !feet) return null;
  const voice=message.voice;
  if(voice!==undefined&&(!Array.isArray(voice)||voice.length!==3||!voice.every(n=>Number.isFinite(n)&&n>=0&&n<=1)))return null;
  return { head, left, right, ...(feet ? {feet} : {}), ...(voice ? {voice} : {}) };
}

/** Attach rooms to an existing HTTP(S) server, leaving other upgrade paths alone. */
export function attachRooms(server, { maxVisitors = 12, heartbeatMs = 15000, iceServers = voiceIceServers() } = {}) {
  const rooms = new Map();
  const wss = new WebSocketServer({ noServer: true, maxPayload: MAX_VOICE_PACKET, perMessageDeflate: false });
  const send = (socket, packet) => {
    if (socket.readyState !== WebSocket.OPEN) return;
    if (socket.bufferedAmount > MAX_BUFFER) { socket.close(1013, 'Connexion trop lente'); return; }
    socket.send(JSON.stringify(packet));
  };
  const broadcast = (room, packet, except) => {
    for (const peer of room.values()) if (peer !== except) send(peer.socket, packet);
  };
  const upgrade = (request, socket, head) => {
    let url;
    try { url = new URL(request.url, 'http://localhost'); } catch { return; }
    if (url.pathname !== '/rooms') return;
    const reject = (code, text) => socket.end(`HTTP/1.1 ${code} ${text}\r\nConnection: close\r\n\r\n`);
    const code = url.searchParams.get('room') || '';
    if (!ROOM_PATTERN.test(code)) { reject(400, 'Bad Request'); return; }
    if (request.headers.origin) {
      try {
        if (new URL(request.headers.origin).host !== request.headers.host) {
          reject(403, 'Forbidden'); return;
        }
      } catch { reject(403, 'Forbidden'); return; }
    }
    if (wss.clients.size >= 1024 || (!rooms.has(code) && rooms.size >= 512)) {
      reject(503, 'Service Unavailable'); return;
    }
    wss.handleUpgrade(request, socket, head, ws => {
      const room = rooms.get(code) || new Map();
      if (room.size >= maxVisitors) { ws.close(4004, 'Salon complet'); return; }
      rooms.set(code, room);
      const peer = { id: randomUUID(), socket: ws, pose: null, participant: url.searchParams.get('mode') !== 'observer', alive: true, tokens: 30, voiceTokens: 160, lastToken: Date.now() };
      peer.nickname = visitorNickname(url.searchParams.get('nickname'), peer.id);
      peer.avatar = visitorAvatar(url.searchParams.get('avatar'));
      room.set(peer.id, peer);
      send(ws, {
        type: 'welcome', id: peer.id, nickname: peer.nickname, avatar: peer.avatar, mode: peer.participant ? 'participant' : 'observer', serverTime: Date.now(), iceServers, peers: [...room.values()]
          .filter(p => p !== peer && p.participant).map(p => ({ id: p.id, nickname: p.nickname, avatar: p.avatar, pose: p.pose }))
      });
      if (peer.participant) broadcast(room, { type: 'join', id: peer.id, nickname: peer.nickname, avatar: peer.avatar }, peer);
      ws.on('pong', () => { peer.alive = true; });
      ws.on('error', () => { });
      ws.on('message', (data, binary) => {
        const now = Date.now();
        peer.tokens = Math.min(30, peer.tokens + (now - peer.lastToken) * 0.02);
        peer.voiceTokens = Math.min(160, peer.voiceTokens + (now - peer.lastToken) * 0.04);
        peer.lastToken = now;
        if (binary) { ws.close(1008, 'Paquet refuse'); return; }
        let message;
        try { message = JSON.parse(data.toString()); } catch { ws.close(data.length > 2048 ? 1009 : 1008, 'JSON invalide'); return; }
        if (message?.type === 'voice-signal') {
          if (!peer.participant) return;
          if (peer.voiceTokens < 1) { ws.close(1008, 'Signalisation trop rapide'); return; }
          peer.voiceTokens -= 1;
          const signal = validateVoiceSignal(message);
          if (!signal) { ws.close(1008, 'Signal vocal invalide'); return; }
          const recipient = room.get(signal.to);
          // A departed destination is normal during teardown. Never relay across rooms.
          if (recipient && recipient.participant && recipient !== peer) send(recipient.socket, {
            type: 'voice-signal', from: peer.id,
            ...(signal.description ? { description: signal.description } : { candidate: signal.candidate })
          });
          return;
        }
        if (data.length > 2048) { ws.close(1009, 'Paquet trop grand'); return; }
        if (peer.tokens < 1) { ws.close(1008, 'Paquet refuse'); return; }
        peer.tokens -= 1;
        if (message?.type === 'clock' && Number.isFinite(message.sent)) {
          send(ws, { type: 'clock', sent: message.sent, serverTime: now }); return;
        }
        if (message?.type === 'presence' && ['observer', 'participant'].includes(message.mode) &&
          Number.isSafeInteger(message.requestId) && message.requestId >= 0) {
          const participant = message.mode === 'participant';
          if (participant !== peer.participant) {
            peer.participant = participant;
            peer.pose = null;
            broadcast(room, participant ? { type: 'join', id: peer.id, nickname: peer.nickname, avatar: peer.avatar } :
              { type: 'leave', id: peer.id }, peer);
          }
          send(ws, { type: 'presence', mode: message.mode, requestId: message.requestId });
          return;
        }
        const pose = validatePose(message);
        if (!pose) { ws.close(1008, 'Pose invalide'); return; }
        if (!peer.participant) return;
        peer.pose = pose;
        broadcast(room, { type: 'pose', id: peer.id, ...pose }, peer);
      });
      ws.on('close', () => {
        room.delete(peer.id);
        if (peer.participant) broadcast(room, { type: 'leave', id: peer.id });
        if (!room.size) rooms.delete(code);
      });
    });
  };
  server.on('upgrade', upgrade);
  const heartbeat = setInterval(() => {
    for (const room of rooms.values()) for (const peer of room.values()) {
      if (!peer.alive) { peer.socket.terminate(); continue; }
      peer.alive = false;
      if (peer.socket.readyState === WebSocket.OPEN) peer.socket.ping();
    }
  }, heartbeatMs);
  heartbeat.unref();
  let closed = false;
  const close = () => {
    if (closed) return;
    closed = true;
    clearInterval(heartbeat);
    server.off('upgrade', upgrade);
    for (const ws of wss.clients) ws.terminate();
    wss.close();
  };
  server.once('close', close);
  return { rooms, close };
}
