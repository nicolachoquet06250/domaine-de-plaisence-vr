/** Opt-in managed-browser test: two real WebRTC peers, synthetic French speech, no live mic. */
import { Group, Vector3, type World } from '@iwsdk/core';
import { VoiceSession } from '../src/voice-session.js';
import { setCourtAvatar, animateCourtAvatar, animateCourtMouth } from '../src/court-avatar.js';
import { RoomConnection } from '../src/multiplayer-components.js';
import type { SpeechVisemes } from '../src/speech-visemes.js';
import speechURL from '../artifacts/avatars/lipsync/test-fr.wav?url';
const delay=(ms:number)=>new Promise<void>(resolve=>setTimeout(resolve,ms));
async function until(test:()=>boolean,timeout=20000){const end=performance.now()+timeout;while(!test()){if(performance.now()>end)throw Error('Lip sync readiness timeout');await delay(50);}}
type Inspect={context:AudioContext;output:GainNode;localSpeech?:SpeechVisemes;peers:Map<string,{speech?:SpeechVisemes;pc:RTCPeerConnection}>};
export function installLipSyncBrowserHarness(world:World):void {
  const diagnostic=world.createTransformEntity(new Group(),{persistent:true}).addComponent(RoomConnection);
  diagnostic.object3D!.name='Verification synchronisation labiale';
  const status=(state:string,data:unknown='')=>{diagnostic.setValue(RoomConnection,'status',state);diagnostic.setValue(RoomConnection,'voiceError',JSON.stringify(data));};
  status('waiting-for-xr');let started=false;
  const start=()=>{if(started)return;started=true;void run().catch(e=>status('failed',String(e)));};
  world.renderer.xr.addEventListener('sessionstart',start);
  async function run(){
    const contexts:AudioContext[]=[],voices:VoiceSession[]=[],sockets:WebSocket[]=[],sources:AudioBufferSourceNode[]=[];
    let timer:ReturnType<typeof setInterval>|undefined;
    try{
      status('loading');
      const generators:MediaStream[]=[];
      for(let i=0;i<2;i++){
        const context=new AudioContext();contexts.push(context);void context.resume();
        const source=context.createBufferSource();source.loop=true;sources.push(source);
        const destination=context.createMediaStreamDestination();source.connect(destination);generators.push(destination.stream);
      }
      const room=Array.from(crypto.getRandomValues(new Uint8Array(16)),n=>n.toString(16).padStart(2,'0')).join('');
      const joined=[false,false];
      for(let i=0;i<2;i++){
        const url=new URL('/rooms',location.href);url.protocol='wss:';url.searchParams.set('room',room);url.searchParams.set('nickname',`Essai labial ${i}`);url.searchParams.set('avatar',i?'female':'male');
        const socket=new WebSocket(url);sockets.push(socket);
        const voice=new VoiceSession(packet=>{if(socket.readyState!==WebSocket.OPEN)return false;socket.send(JSON.stringify(packet));return true;},()=>{},async()=>generators[i]);voices.push(voice);
        void voice.toggleListening();
        const internal=voice as unknown as Inspect,silent=internal.context.createGain();silent.gain.value=0;
        internal.output.disconnect();internal.output.connect(silent);silent.connect(internal.context.destination);
        socket.onmessage=e=>{const m=JSON.parse(e.data);if(m.type==='welcome'){voice.connect(m.id,[]);m.peers.forEach((p:{id:string})=>voice.addPeer(p.id));joined[i]=true;}else if(m.type==='join')voice.addPeer(m.id);else if(m.type==='voice-signal')voice.receive(m);else if(m.type==='leave')voice.removePeer(m.id);};
      }
      const wave=await (await fetch(speechURL)).arrayBuffer();
      for(let i=0;i<2;i++){sources[i].buffer=await contexts[i].decodeAudioData(wave.slice(0));sources[i].start();}
      const male=new Group(),female=new Group();male.position.set(-.18,0,-.8);female.position.set(.18,.0825,-.8);
      world.createTransformEntity(male,{persistent:true});world.createTransformEntity(female,{persistent:true});
      await Promise.all([setCourtAvatar(male,'male'),setCourtAvatar(female,'female')]);
      await until(()=>joined.every(Boolean)&&voices.every(v=>v.state.connectedPeers===1));
      await Promise.all(voices.map(v=>v.toggleMicrophone()));
      const local=voices[0] as unknown as Inspect, remoteId=[...local.peers.keys()][0];
      const remote=voices[1] as unknown as Inspect, reverseId=[...remote.peers.keys()][0];
      const eye=new Vector3(0,1.65,0),forward=new Vector3(0,0,-1),up=new Vector3(0,1,0);
      voices.forEach(v=>v.setListener(eye,forward,up));
      voices[0].setPeerPosition(remoteId,new Vector3(0,1.65,-1),true);voices[1].setPeerPosition(reverseId,new Vector3(0,1.65,-1),true);
      await until(()=>local.localSpeech?.status==='ready'&&local.peers.get(remoteId)?.speech?.status==='ready'&&remote.localSpeech?.status==='ready');
      const seenLocal=new Set<number>(),seenRemote=new Set<number>();let frames=0,previous=performance.now();
      timer=setInterval(()=>{
        const now=performance.now(),delta=(now-previous)/1000;previous=now;
        const a=voices[0].localVisemes(delta),b=voices[0].peerVisemes(remoteId,delta);
        animateCourtAvatar(male,delta);animateCourtAvatar(female,delta);animateCourtMouth(male,a);animateCourtMouth(female,b);
        if(a)for(let i=0;i<14;i++)if(a[i]>.3)seenLocal.add(i);
        if(b)for(let i=0;i<14;i++)if(b[i]>.3)seenRemote.add(i);
        frames++;if(frames%30===0)status('speaking',{local:[...seenLocal],remote:[...seenRemote],frames});
      },16);
      await delay(20000);
      if(seenLocal.size<4||seenRemote.size<4)throw Error(`Insufficient acoustic variety: ${seenLocal.size}/${seenRemote.size}`);
      await Promise.all(voices.map(v=>v.toggleMicrophone()));
      const muteStart=performance.now();
      // RTP jitter buffers can continue playing queued speech after the sender mutes.
      // Keep rendering until that audio and the mouth crossfade have both ended.
      await delay(300);
      await until(()=>!voices[0].peerVisemes(remoteId,0)?.some(n=>n>.01),3000);
      const muteToClosedMs=Math.round(performance.now()-muteStart);
      clearInterval(timer);timer=undefined;
      animateCourtMouth(male);animateCourtMouth(female);
      status('passed',{localVisemes:[...seenLocal],remoteVisemes:[...seenRemote],frames,mutedMouthClosed:true,muteToClosedMs,syntheticFrench:true,transport:'WebRTC'});
    }finally{if(timer)clearInterval(timer);voices.forEach(v=>v.dispose());sockets.forEach(s=>s.close());sources.forEach(s=>s.stop());for(const c of contexts)await c.close();world.renderer.xr.removeEventListener('sessionstart',start);}
  }
}
