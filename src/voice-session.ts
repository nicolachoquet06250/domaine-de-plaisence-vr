import { SpeechVisemes } from './speech-visemes.js';
import { VoiceSpectrum } from './voice-spectrum.js';

export const VOICE_RANGE = 25;
export const VOICE_NEAR = 1;
export function voiceRangeGain(distance: number): number {
  return Math.max(0, Math.min(1, (VOICE_RANGE - distance) / 5));
}
export function voiceDistanceGain(distance: number): number {
  return voiceRangeGain(distance) / Math.max(VOICE_NEAR, distance);
}

export type VoiceSignal = {type:'voice-signal'; to:string; description?:RTCSessionDescriptionInit; candidate?:RTCIceCandidateInit};
export type VoiceState = {
  microphone: 'off' | 'requesting' | 'on' | 'denied' | 'unavailable';
  listening: boolean; listeningPaused: boolean; connectedPeers: number; roomConnected: boolean; error: string;
};
type Point = {x:number; y:number; z:number};
type Peer = {
  pc:RTCPeerConnection; sender?:RTCRtpSender; initiator:boolean; queue:Promise<void>;
  candidates:RTCIceCandidateInit[]; stream?:MediaStream; source?:MediaStreamAudioSourceNode; playback?:HTMLAudioElement;
  panner?:PannerNode; gain?:GainNode; delay?:DelayNode; speech?:SpeechVisemes; restartTimer?:ReturnType<typeof setTimeout>; restarts:number;
  x:number; y:number; z:number; posed:boolean; audibleGain:number;
};

/** Audio transport and graph only; avatar ownership remains in the ECS query. */
export class VoiceSession {
  readonly state:VoiceState = {microphone:'off', listening:false, listeningPaused:false, connectedPeers:0, roomConnected:false, error:''};
  private readonly peers = new Map<string, Peer>();
  private id = '';
  private iceServers:RTCIceServer[] = [];
  private context?:AudioContext;
  private output?:GainNode;
  private microphone?:MediaStream;
  private microphoneSource?:MediaStreamAudioSourceNode;
  private localSpeech?:SpeechVisemes;
  private localSpectrum?:VoiceSpectrum;
  private readonly silentBands=[0,0,0];
  private captureVersion = 0;
  private listeningVersion = 0;
  private disposed = false;
  private listenerX = 0;
  private listenerY = 0;
  private listenerZ = 0;

  constructor(private readonly send:(packet:VoiceSignal)=>boolean, private readonly changed:(state:VoiceState)=>void,
    private readonly captureAudio = () => navigator.mediaDevices.getUserMedia({video:false, audio:{
      echoCancellation:true, noiseSuppression:true, autoGainControl:true, channelCount:1,
    }})) {}

  connect(id:string, iceServers:RTCIceServer[]):void {
    this.disconnect();
    this.id = id;
    this.iceServers = iceServers;
    this.state.roomConnected = true;
    this.state.error = '';
    this.publish();
  }

  addPeer(id:string):void {
    if (this.disposed || !this.id || id === this.id || this.peers.has(id) || this.peers.size >= 11) return;
    if (typeof RTCPeerConnection === 'undefined') {
      this.state.error = 'Voix non disponible sur ce navigateur.'; this.publish(); return;
    }
    try {
      const pc = new RTCPeerConnection({iceServers:this.iceServers});
      const initiator = this.id < id;
      // Only the offerer creates a transceiver. The answerer must use the one
      // created by setRemoteDescription, otherwise its sender has no SDP mid.
      const sender = initiator ? pc.addTransceiver('audio', {direction:'sendrecv'}).sender : undefined;
      const peer:Peer = {pc, sender, initiator, queue:Promise.resolve(), candidates:[], restarts:0,
        x:0, y:0, z:0, posed:false, audibleGain:0};
      this.peers.set(id, peer);
      pc.onicecandidate = event => {
        if (event.candidate && this.peers.get(id) === peer) this.send({type:'voice-signal', to:id, candidate:event.candidate.toJSON()});
      };
      pc.ontrack = event => {
        if (event.track.kind !== 'audio' || this.peers.get(id) !== peer) return;
        this.releaseAudio(peer);
        peer.stream = new MediaStream([event.track]);
        this.attachAudio(peer);
      };
      pc.onconnectionstatechange = () => {
        if (this.peers.get(id) !== peer) return;
        if (pc.connectionState === 'connected') {
          clearTimeout(peer.restartTimer); peer.restartTimer = undefined; peer.restarts = 0;
          this.state.error = '';
        } else if (pc.connectionState === 'failed' || pc.connectionState === 'disconnected') {
          if (!peer.restartTimer && peer.initiator && peer.restarts < 2) {
            peer.restartTimer = setTimeout(() => {
              peer.restartTimer = undefined;
              if (this.peers.get(id) === peer && pc.connectionState !== 'connected') {
                peer.restarts++;
                this.enqueue(id, peer, () => this.offer(id, peer, true));
              }
            }, 3000);
          }
          this.state.error = 'Connexion vocale interrompue. Verifiez le reseau.';
        }
        this.publish();
      };
      this.enqueue(id, peer, async () => {
        await peer.sender?.replaceTrack(this.microphone?.getAudioTracks()[0] ?? null);
        if (peer.initiator) await this.offer(id, peer);
      });
    } catch {
      this.removePeer(id);
      this.state.error = 'Connexion vocale indisponible.'; this.publish();
    }
  }

  receive(message:{from:string; description?:RTCSessionDescriptionInit; candidate?:RTCIceCandidateInit}):void {
    const peer = this.peers.get(message.from);
    if (!peer) return;
    this.enqueue(message.from, peer, async () => {
      if (message.description) {
        const description = message.description;
        // A single deterministic offerer avoids simultaneous offers and glare.
        if ((description.type === 'offer') === peer.initiator) return;
        if (description.type === 'answer' && peer.pc.signalingState !== 'have-local-offer') return;
        await peer.pc.setRemoteDescription(description);
        for (const candidate of peer.candidates) await peer.pc.addIceCandidate(candidate);
        peer.candidates.length = 0;
        if (description.type === 'offer') {
          const transceiver = peer.pc.getTransceivers().find(t => t.receiver.track.kind === 'audio');
          if (!transceiver) throw new Error('Missing negotiated audio transceiver');
          transceiver.direction = 'sendrecv';
          peer.sender = transceiver.sender;
          await peer.sender.replaceTrack(this.microphone?.getAudioTracks()[0] ?? null);
          await peer.pc.setLocalDescription(await peer.pc.createAnswer());
          if (this.peers.get(message.from) === peer) this.send({type:'voice-signal', to:message.from,
            description:peer.pc.localDescription!.toJSON()});
        }
      } else if (message.candidate) {
        if (peer.pc.remoteDescription) await peer.pc.addIceCandidate(message.candidate);
        else if (peer.candidates.length < 128) peer.candidates.push(message.candidate);
      }
    });
  }

  private enqueue(id:string, peer:Peer, action:()=>Promise<void>):void {
    peer.queue = peer.queue.then(async () => {
      if (this.peers.get(id) === peer && !this.disposed) await action();
    }).catch(() => {
      if (this.peers.get(id) === peer) { this.state.error = 'La voix de ce visiteur ne se connecte pas.'; this.publish(); }
    });
  }

  private async offer(id:string, peer:Peer, restart = false):Promise<void> {
    if (peer.pc.signalingState !== 'stable') return;
    await peer.pc.setLocalDescription(await peer.pc.createOffer({iceRestart:restart}));
    if (this.peers.get(id) === peer) this.send({type:'voice-signal', to:id, description:peer.pc.localDescription!.toJSON()});
  }

  private ensureAudio():AudioContext {
    if (!this.context) {
      const context = new AudioContext();
      this.context = context;
      this.output = context.createGain();
      this.output.gain.value = 0;
      this.output.connect(context.destination);
      context.onstatechange = () => this.publish();
      for (const peer of this.peers.values()) this.attachAudio(peer);
    }
    return this.context;
  }

  async toggleListening():Promise<void> {
    if (this.disposed) return;
    const version = ++this.listeningVersion;
    if (this.state.listening && this.context?.state === 'running') {
      this.stopListening(); return;
    }
    this.state.listening = true;
    try {
      const context = this.ensureAudio();
      for (const peer of this.peers.values()) if (peer.playback) void this.startPlayback(peer);
      await context.resume();
      if (this.disposed || version !== this.listeningVersion) return;
      this.output!.gain.setTargetAtTime(1, context.currentTime, .02);
      this.state.error = '';
    } catch {
      if (version !== this.listeningVersion || this.disposed) return;
      this.state.listening = false; this.state.error = "L'ecoute n'a pas pu demarrer. Reessayez.";
    }
    this.publish();
  }

  stopListening():void {
    this.listeningVersion++;
    this.state.listening = false;
    this.output?.gain.setTargetAtTime(0, this.context!.currentTime, .02);
    this.publish();
  }

  /** Called only by a user gesture; never requests microphone permission at load. */
  async toggleMicrophone():Promise<void> {
    if (this.disposed) return;
    if (this.state.microphone === 'on' || this.state.microphone === 'requesting') {
      this.stopMicrophone(); return;
    }
    if (!this.state.roomConnected) { this.state.error = "Rejoignez le salon avant d'activer le micro."; this.publish(); return; }
    if (!navigator.mediaDevices?.getUserMedia || typeof RTCPeerConnection === 'undefined') {
      this.state.microphone = 'unavailable'; this.state.error = 'Le micro necessite un navigateur compatible et HTTPS.'; this.publish(); return;
    }
    const version = ++this.captureVersion;
    this.state.microphone = 'requesting'; this.state.error = ''; this.publish();
    // Resume directly inside the gesture, before the permission promise resolves.
    const listening = this.state.listening && this.context?.state === 'running' ? Promise.resolve() : this.toggleListening();
    try {
      const stream = await this.captureAudio();
      if (version !== this.captureVersion || this.disposed || !this.state.roomConnected) {
        stream.getTracks().forEach(track => track.stop()); return;
      }
      const track = stream.getAudioTracks()[0];
      if (!track) { stream.getTracks().forEach(t => t.stop()); throw new Error('No audio track'); }
      this.microphone = stream;
      this.microphoneSource = this.ensureAudio().createMediaStreamSource(stream);
      this.localSpeech = new SpeechVisemes(this.context!, this.microphoneSource);
      this.localSpectrum = new VoiceSpectrum(this.context!, this.microphoneSource);
      track.onended = () => { if (this.microphone === stream) this.stopMicrophone(); };
      for (const [id, peer] of this.peers) this.enqueue(id, peer, async () => {
        await peer.sender?.replaceTrack(this.microphone?.getAudioTracks()[0] ?? null);
      });
      this.state.microphone = 'on';
    } catch (error) {
      if (version !== this.captureVersion || this.disposed) return;
      const name = (error as {name?:string})?.name;
      this.state.microphone = name === 'NotAllowedError' ? 'denied' : 'unavailable';
      this.state.error = name === 'NotAllowedError' ? 'Micro refuse. Autorisez-le dans votre navigateur pour parler.' : 'Micro absent ou deja utilise. Reessayez.';
    }
    await listening;
    this.publish();
  }

  private stopMicrophone():void {
    this.captureVersion++;
    const stream = this.microphone;
    this.microphone = undefined;
    this.localSpeech?.dispose(); this.localSpeech = undefined;
    this.localSpectrum?.dispose(); this.localSpectrum = undefined;
    this.microphoneSource?.disconnect(); this.microphoneSource = undefined;
    stream?.getTracks().forEach(track => { track.onended = null; track.stop(); });
    for (const [id, peer] of this.peers) this.enqueue(id, peer, async () => {
      await peer.sender?.replaceTrack(this.microphone?.getAudioTracks()[0] ?? null);
    });
    this.state.microphone = 'off'; this.publish();
  }

  private attachAudio(peer:Peer):void {
    if (!this.context || !peer.stream || peer.source) return;
    // Chromium needs a playing media element to pull/decode remote RTP audio.
    // Keep it muted: the spatial Web Audio graph is the only audible output.
    const playback = document.createElement('audio');
    playback.autoplay = true; playback.muted = true;
    playback.setAttribute('playsinline', '');
    playback.srcObject = peer.stream;
    peer.playback = playback;
    void this.startPlayback(peer);
    const panner = this.context.createPanner();
    panner.panningModel = 'HRTF'; panner.distanceModel = 'inverse';
    panner.refDistance = VOICE_NEAR; panner.maxDistance = VOICE_RANGE; panner.rolloffFactor = 1;
    panner.coneInnerAngle = 360; panner.coneOuterAngle = 360; panner.coneOuterGain = 1;
    const source = this.context.createMediaStreamSource(peer.stream);
    const gain = this.context.createGain(); gain.gain.value = 0;
    // Match the short acoustic analysis window without buffering network pose packets.
    const delay = this.context.createDelay(.2); delay.delayTime.value = .06;
    source.connect(delay); delay.connect(panner); panner.connect(gain); gain.connect(this.output!);
    peer.delay = delay; peer.speech = new SpeechVisemes(this.context, source);
    peer.source = source; peer.panner = panner; peer.gain = gain;
  }

  setListener(position:Point, forward:Point, up:Point):void {
    this.listenerX = position.x; this.listenerY = position.y; this.listenerZ = position.z;
    const listener = this.context?.listener;
    if (!listener) return;
    listener.positionX.value = position.x; listener.positionY.value = position.y; listener.positionZ.value = position.z;
    listener.forwardX.value = forward.x; listener.forwardY.value = forward.y; listener.forwardZ.value = forward.z;
    listener.upX.value = up.x; listener.upY.value = up.y; listener.upZ.value = up.z;
  }

  setPeerPosition(id:string, position:Point, visible:boolean):number {
    const peer = this.peers.get(id);
    if (!peer) return 0;
    peer.x = position.x; peer.y = position.y; peer.z = position.z; peer.posed = visible;
    const distance = Math.hypot(position.x - this.listenerX, position.y - this.listenerY, position.z - this.listenerZ);
    peer.audibleGain = visible && this.state.listening && this.context?.state === 'running' ? voiceDistanceGain(distance) : 0;
    if (peer.panner && peer.gain) {
      peer.panner.positionX.value = position.x; peer.panner.positionY.value = position.y; peer.panner.positionZ.value = position.z;
      peer.gain.gain.value = visible ? voiceRangeGain(distance) : 0;
    }
    return peer.audibleGain;
  }

  isPeerConnected(id:string):boolean { return this.peers.get(id)?.pc.connectionState === 'connected'; }

  localVisemes(delta:number):Float32Array | undefined { return this.localSpeech?.sample(delta, this.state.microphone === 'on'); }
  localVoiceBands():number[] { return this.localSpectrum?.sample(this.state.microphone==='on') ?? this.silentBands; }
  peerVisemes(id:string, delta:number):Float32Array | undefined {
    const peer = this.peers.get(id);
    return peer?.speech?.sample(delta, peer.posed && Math.hypot(peer.x-this.listenerX,peer.y-this.listenerY,peer.z-this.listenerZ) < VOICE_RANGE);
  }

  private async startPlayback(peer:Peer):Promise<void> {
    const playback = peer.playback;
    try { await playback?.play(); }
    catch {
      if (!this.disposed && peer.playback === playback) {
        this.state.error = "Lecture audio bloquee. Relancez l'ecoute."; this.publish();
      }
    }
  }

  private releaseAudio(peer:Peer):void {
    peer.speech?.dispose(); peer.speech = undefined; peer.delay?.disconnect(); peer.delay = undefined;
    if (peer.playback) { peer.playback.pause(); peer.playback.srcObject = null; peer.playback = undefined; }
    peer.source?.disconnect(); peer.panner?.disconnect(); peer.gain?.disconnect();
    peer.source = undefined; peer.panner = undefined; peer.gain = undefined;
  }

  removePeer(id:string):void {
    const peer = this.peers.get(id);
    if (!peer) return;
    this.peers.delete(id);
    clearTimeout(peer.restartTimer);
    peer.pc.ontrack = null; peer.pc.onicecandidate = null; peer.pc.onconnectionstatechange = null;
    peer.pc.close(); this.releaseAudio(peer);
    peer.stream?.getTracks().forEach(track => track.stop());
    peer.candidates.length = 0;
    this.publish();
  }

  disconnect():void {
    this.id = ''; this.state.roomConnected = false;
    for (const id of this.peers.keys()) this.removePeer(id);
    this.stopMicrophone();
  }

  dispose():void {
    this.disposed = true;
    this.disconnect();
    if (this.context) { this.context.onstatechange = null; void this.context.close().catch(() => {}); }
    this.output?.disconnect();
    this.state.listening = false;
  }

  private publish():void {
    let count = 0;
    for (const peer of this.peers.values()) if (peer.pc.connectionState === 'connected') count++;
    this.state.connectedPeers = count;
    this.state.listeningPaused = this.state.listening && this.context?.state !== 'running';
    if (!this.disposed) this.changed(this.state);
  }
}
