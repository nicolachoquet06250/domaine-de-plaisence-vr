const PEER_ID = /^[a-f0-9-]{36}$/;
export const MAX_VOICE_PACKET = 32768;

/** Only a targeted SDP description or ICE candidate can cross the room relay. */
export function validateVoiceSignal(message) {
  if (message?.type !== 'voice-signal' || !PEER_ID.test(message.to)) return null;
  const description = message.description;
  if (description != null) {
    if ('candidate' in message || !['offer', 'answer'].includes(description.type) ||
      typeof description.sdp !== 'string' || description.sdp.length > 24000 ||
      !description.sdp.startsWith('v=0') || !description.sdp.includes('m=audio')) return null;
    return { to: message.to, description: { type: description.type, sdp: description.sdp } };
  }
  const c = message.candidate;
  if (!c || typeof c.candidate !== 'string' || c.candidate.length > 2048 ||
    (c.sdpMid != null && (typeof c.sdpMid !== 'string' || c.sdpMid.length > 64)) ||
    (c.sdpMLineIndex != null && (!Number.isInteger(c.sdpMLineIndex) || c.sdpMLineIndex < 0 || c.sdpMLineIndex > 8)) ||
    (c.usernameFragment != null && (typeof c.usernameFragment !== 'string' || c.usernameFragment.length > 256))) return null;
  return {
    to: message.to, candidate: {
      candidate: c.candidate, sdpMid: c.sdpMid ?? null,
      sdpMLineIndex: c.sdpMLineIndex ?? null, usernameFragment: c.usernameFragment ?? null
    }
  };
}

export function voiceIceServers(raw = process.env.VOICE_ICE_SERVERS) {
  if (!raw) return [{ urls: 'stun:stun.l.google.com:19302' }];
  const servers = JSON.parse(raw);
  if (!Array.isArray(servers) || servers.length > 8) throw new Error('VOICE_ICE_SERVERS doit etre une liste de serveurs ICE.');
  return servers.map(server => {
    const urls = Array.isArray(server.urls) ? server.urls : [server.urls];
    if (!urls.length || urls.length > 8 || urls.some(url => typeof url !== 'string' || url.length > 512 || !/^(stun|stuns|turn|turns):/.test(url)) ||
      (server.username != null && typeof server.username !== 'string') ||
      (server.credential != null && typeof server.credential !== 'string')) throw new Error('Serveur ICE invalide dans VOICE_ICE_SERVERS.');
    return {
      urls, ...(server.username != null ? { username: server.username } : {}),
      ...(server.credential != null ? { credential: server.credential } : {})
    };
  });
}
