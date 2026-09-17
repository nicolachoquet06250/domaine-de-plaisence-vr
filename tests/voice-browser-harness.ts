/** Temporary opt-in browser verification. Never imported by the shipping app.
 * Uses synthetic tones and a silent output sink, never the physical microphone.
 */
import { type World } from '@iwsdk/core';
import { RoomConnection } from '../src/multiplayer-components.js';
import { VoiceSession } from '../src/voice-session.js';

const delay = (ms:number) => new Promise<void>(resolve => setTimeout(resolve, ms));
async function waitFor(predicate:()=>boolean, label:string, timeout = 15000) {
  const end = performance.now() + timeout;
  while (!predicate()) { if (performance.now() > end) throw new Error(label); await delay(50); }
}
type InspectVoice = {
  context:AudioContext; output:GainNode;
  peers:Map<string,{pc:RTCPeerConnection}>;
};

export function installVoiceBrowserHarness(world:World) {
  const diagnostics = world.createTransformEntity(undefined,{persistent:true}).addComponent(RoomConnection);
  diagnostics.object3D!.name = 'Vérification voix WebRTC';
  const set = (status:string, result:unknown = '') => {
    diagnostics.setValue(RoomConnection,'status',status);
    diagnostics.setValue(RoomConnection,'voiceError',typeof result === 'string' ? result : JSON.stringify(result));
  };
  set('waiting-for-xr');
  let started = false;
  const start = () => {
    if (started) return; started = true;
    void run().catch(error => set('failed',String(error)));
  };
  world.renderer.xr.addEventListener('sessionstart',start);
  async function run() {
    set('connecting');
    const contexts:AudioContext[] = [];
    const oscillators:OscillatorNode[] = [];
    const sessions:VoiceSession[] = [];
    const sockets:WebSocket[] = [];
    const room = Array.from(crypto.getRandomValues(new Uint8Array(16)),n=>n.toString(16).padStart(2,'0')).join('');
    try {
      // Create/resume inside the XR activation gesture, before waiting for sockets.
      const generators = [1200,1800].map(frequency => {
        const context = new AudioContext(); contexts.push(context); void context.resume();
        const oscillator = context.createOscillator(); oscillator.frequency.value = frequency;
        const gain = context.createGain(); gain.gain.value = .1;
        const destination = context.createMediaStreamDestination();
        oscillator.connect(gain); gain.connect(destination); oscillator.start(); oscillators.push(oscillator);
        return destination.stream;
      });
      const ready:boolean[] = [false,false];
      for(let i=0;i<2;i++) {
        const endpoint = new URL('/rooms',location.href); endpoint.protocol='wss:';endpoint.searchParams.set('room',room);
        const socket = new WebSocket(endpoint); sockets.push(socket);
        const voice = new VoiceSession(packet => {if(socket.readyState!==WebSocket.OPEN)return false;socket.send(JSON.stringify(packet));return true;},()=>{},async()=>generators[i]);
        sessions.push(voice);
        // Resume its receiver context with the same gesture, and silence only
        // the final hardware sink. The analyser measures before this sink.
        void voice.toggleListening();
        const internals = voice as unknown as InspectVoice;
        const silent = internals.context.createGain(); silent.gain.value = 0;
        internals.output.disconnect(); internals.output.connect(silent); silent.connect(internals.context.destination);
        socket.onmessage = event => {
          const message = JSON.parse(event.data);
          if(message.type==='welcome') {
            voice.connect(message.id,[]); // Host candidates suffice for this local test.
            for(const peer of message.peers)voice.addPeer(peer.id);
            ready[i]=true;
          } else if(message.type==='join')voice.addPeer(message.id);
          else if(message.type==='voice-signal')voice.receive(message);
          else if(message.type==='leave')voice.removePeer(message.id);
        };
      }
      await waitFor(()=>ready.every(Boolean),'room welcome timeout');
      await waitFor(()=>sessions.every(voice=>voice.state.connectedPeers===1),'WebRTC negotiation timeout');
      // Both users grant permission AFTER joining, as on the phone and Quest.
      await Promise.all(sessions.map(voice=>voice.toggleMicrophone()));
      set('measuring');
      const internal = sessions[0] as unknown as InspectVoice;
      const remote = [...internal.peers.keys()][0];
      const analyser = internal.context.createAnalyser(); analyser.fftSize=2048;
      internal.output.connect(analyser);
      const silent = internal.context.createGain();silent.gain.value=0;analyser.connect(silent);silent.connect(internal.context.destination);
      const samples = new Float32Array(analyser.fftSize);
      const pos = {x:0,y:1.65,z:0}; const forward = {x:0,y:0,z:-1}; const up = {x:0,y:1,z:0};
      for(const voice of sessions)voice.setListener(pos,forward,up);
      const other = [...(sessions[1] as unknown as InspectVoice).peers.keys()][0];
      sessions[1].setPeerPosition(other,{x:0,y:1.65,z:-1},true);
      async function level(distance:number) {
        sessions[0].setPeerPosition(remote,{x:0,y:1.65,z:-distance},true);
        await delay(650);
        let sum=0;
        for(let i=0;i<6;i++) {
          analyser.getFloatTimeDomainData(samples);
          sum+=Math.sqrt(samples.reduce((total,n)=>total+n*n,0)/samples.length);
          await delay(40);
        }
        return sum/6;
      }
      await waitFor(()=>contexts.every(c=>c.state==='running')&&internal.context.state==='running','audio context suspended');
      const near=await level(1),far=await level(10),outside=await level(30);
      const detail:unknown[]=[];
      for(const voice of sessions) {
        const v=voice as unknown as InspectVoice;const pc=[...v.peers.values()][0].pc;
        const stats:unknown[]=[];(await pc.getStats()).forEach(r=>{if(['inbound-rtp','outbound-rtp','media-source'].includes(r.type))stats.push(r);});
        detail.push({state:voice.state,context:v.context.state,output:v.output.gain.value,
          transceivers:pc.getTransceivers().map(t=>({direction:t.direction,current:t.currentDirection,sender:t.sender.track?.readyState,receiver:t.receiver.track.readyState,muted:t.receiver.track.muted})),stats});
      }
      if(!(near>.001 && far>0 && far<near*.2 && outside<near*.001))throw new Error(JSON.stringify({near,far,outside,detail,reason:'attenuation failed'}));
      const inbound:number[]=[];
      for(const voice of sessions) {
        const pc=[...(voice as unknown as InspectVoice).peers.values()][0].pc;
        let bytes=0;(await pc.getStats()).forEach(report=>{if(report.type==='inbound-rtp'&&report.kind==='audio')bytes+=report.bytesReceived??0;});
        inbound.push(bytes);
      }
      if(inbound.some(bytes=>bytes<=0))throw new Error('No received RTP audio');
      const reverse = sessions[1] as unknown as InspectVoice;
      const reverseAnalyser = reverse.context.createAnalyser(); reverseAnalyser.fftSize = 2048;
      reverse.output.connect(reverseAnalyser);
      const reverseSink = reverse.context.createGain(); reverseSink.gain.value = 0;
      reverseAnalyser.connect(reverseSink); reverseSink.connect(reverse.context.destination);
      await delay(250);
      reverseAnalyser.getFloatTimeDomainData(samples);
      const reverseNear = Math.sqrt(samples.reduce((total,n)=>total+n*n,0)/samples.length);
      if(reverseNear<=.001)throw new Error('Reverse direction is silent');
      await sessions[1].toggleMicrophone();
      const afterMute=await level(1);
      if(afterMute>near*.02)throw new Error(JSON.stringify({afterMute,near,reason:'mute failed'}));
      // Capture returns a fresh live track after mute, just like getUserMedia.
      const renewedDestination = contexts[1].createMediaStreamDestination();
      oscillators[1].connect(renewedDestination); generators[1] = renewedDestination.stream;
      await sessions[1].toggleMicrophone();
      const afterUnmute = await level(1);
      if(afterUnmute<=.001)throw new Error('Reactivation is silent');
      set('passed',{near,reverseNear,far,ratio:far/near,outside,afterMute,afterUnmute,inboundAudioBytes:inbound,synthetic:true});
    } finally {
      for(const voice of sessions)voice.dispose();
      for(const socket of sockets)socket.close();
      for(const oscillator of oscillators)oscillator.stop();
      for(const context of contexts)await context.close();
      world.renderer.xr.removeEventListener('sessionstart',start);
    }
  }
}
