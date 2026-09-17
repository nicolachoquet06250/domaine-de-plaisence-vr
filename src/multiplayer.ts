import {
  createSystem, Group,
  Vector3, Quaternion, UIKitMLAsset, type Entity, type Object3D, type UIKit, type Sprite,
} from '@iwsdk/core';
import { RemoteVisitor, RoomConnection } from './multiplayer-components.js';
import { VoiceSession, type VoiceState } from './voice-session.js';
import { initialRoom, newRoomId, roomUrl } from './room-route.js';
import { cleanNickname, visitorNickname } from '../server/nickname.mjs';
import { createNameTag, disposeNameTag, animateNameTagVoice } from './avatar-nametag.js';
import { cleanAvatar, visitorAvatar, type AvatarGender } from '../server/avatar.mjs';
import { setCourtAvatar, setCourtAvatarView, animateCourtAvatar, animateCourtMouth, releaseCourtAvatar, courtAvatarDiagnostics, type AvatarMotion } from './court-avatar.js';

type PosePart = { p: number[]; q: number[] };
type Pose = { head: PosePart; feet?: PosePart; left: PosePart | null; right: PosePart | null; voice?:number[] };
function createAvatarMotion(): AvatarMotion {
  return { velocity: new Vector3(), left: { position: new Vector3(), quaternion: new Quaternion(), tracked: false }, right: { position: new Vector3(), quaternion: new Quaternion(), tracked: false } };
}
let clockOffset = 0;
/** Seconds on the room server clock, shared by the fountain animation. */
export function sharedRoomTime(): number { return (Date.now() + clockOffset) / 1000; }

export class MultiplayerSystem extends createSystem({ visitors: { required: [RemoteVisitor] } }) {
  private socket?: WebSocket;
  private stopped = false;
  private room = '';
  private pendingInvitation:string | null = null;
  private retry = 0;
  private retryTimer?: number;
  private connectTimer?: number;
  private status!: HTMLSpanElement;
  private panel!: HTMLDivElement;
  private copy!: HTMLButtonElement;
  private copyFeedback!: HTMLSpanElement;
  private journeyHint!: HTMLSpanElement;
  private position = new Vector3();
  private rotation = new Quaternion();
  private welcomed = false;
  private clockTick = 0;
  private reconnectBlocked = false;
  private connection!: Entity;
  private voice!: VoiceSession;
  private microphoneButton!: HTMLButtonElement;
  private listeningButton!: HTMLButtonElement;
  private voiceStatus!: HTMLSpanElement;
  private voiceSubscribers = new Set<(state:VoiceState)=>void>();
  private forward = new Vector3();
  private up = new Vector3();
  private transition = false;
  private participant = false;
  private desiredPresence: 'observer' | 'participant' = 'observer';
  private presenceRequest = 0;
  private activation?: { id:number; resolve:(ok:boolean)=>void; timer:number };
  private selfId = '';
  private iceServers: RTCIceServer[] = [];
  private journeyHandlers?: { depart:()=>void; return:()=>void };
  private identitySubscribers = new Set<()=>void>();
  private enterButton!: HTMLButtonElement;
  private leaveButton!: HTMLButtonElement;
  private nickname = '';
  private nicknameField!: HTMLInputElement;
  private nicknameLabel!: HTMLLabelElement;
  private arrivalNickname?:UIKit.Input;
  private avatarGender: AvatarGender | null = null;
  private avatarChoices!: HTMLDivElement;
  private maleButton!: HTMLButtonElement;
  private femaleButton!: HTMLButtonElement;
  private nameTags = new WeakMap<Object3D, Sprite>();
  private bodyRotation = new Quaternion();
  private verticalAxis = new Vector3(0, 1, 0);
  private localBody!: Entity;
  private localMotion = createAvatarMotion();
  private remoteMotion = new WeakMap<Object3D, AvatarMotion>();
  private oldPosition = new Vector3();
  private headPosition = new Vector3();
  private gripPosition = new Vector3();
  private gripRotation = new Quaternion();
  private bodyWasVisible = false;
  private bodyWasImmersive = false;

  private setAvatar(gender: AvatarGender): void {
    if (this.transition || this.room) return;
    this.avatarGender = gender;
    this.connection.setValue(RoomConnection, 'avatar', gender);
    try { localStorage.setItem('plaisance.avatar.v1', gender); } catch { /* Optional persistence. */ }
    this.refreshAvatarChoices();
    this.showAvatarPreview();
    this.loadLocalBody();
    this.identityChanged();
  }

  private loadLocalBody(): void {
    if (!this.avatarGender || !this.localBody?.object3D) return;
    this.bodyWasVisible = false;
    void setCourtAvatar(this.localBody.object3D, this.avatarGender, true).catch(error => console.error('Local court avatar could not load', error));
  }

  private refreshAvatarChoices(): void {
    const arrival = this.world.getSceneObject<UIKitMLAsset>('arrival-panel');
    for (const gender of ['male', 'female'] as const) {
      const selected = this.avatarGender === gender;
      const label = gender === 'male' ? 'Homme' : 'Femme';
      const button = gender === 'male' ? this.maleButton : this.femaleButton;
      button.setAttribute('aria-pressed', String(selected));
      button.style.background = selected ? '#233e34' : '#eee4cc';
      button.style.color = selected ? '#f5efe0' : '#20382b';
      arrival?.requireElementById(`arrival-avatar-${gender}`).setProperties({
        text: selected ? `${label} (choisi)` : label,
        backgroundColor: selected ? '#233e34' : '#e8dfca', color: selected ? '#f5efe0' : '#233e34',
      });
    }
  }

  private showAvatarPreview(): void {
    const root = this.connection.object3D;
    if (!root || !this.avatarGender || this.transition || this.room || !this.world.getSceneObject('arrival-panel')) return;
    root.position.set(-2, 0, -3);
    root.visible = true;
    void setCourtAvatar(root, this.avatarGender).catch(error => {
      console.error('Court avatar preview could not load', error);
      this.setStatus('error', 'Le personnage ne se charge pas. Choisissez-le de nouveau pour reessayer.');
    });
  }

  private setNickname(value:string, remember = true):void {
    if (this.transition) { this.nicknameField.value = this.nickname; this.arrivalNickname?.setProperties({value:this.nickname}); return; }
    this.nickname = Array.from(value).slice(0,24).join('');
    this.nicknameField.value = this.nickname;
    this.arrivalNickname?.setProperties({value:this.nickname});
    this.connection.setValue(RoomConnection, 'nickname', cleanNickname(this.nickname));
    if (remember) {
      try { localStorage.setItem('plaisance.nickname.v2',cleanNickname(this.nickname)); } catch { /* Visit works without storage. */ }
    }
    this.identityChanged();
  }
  isIdentityReady():boolean { return !!cleanNickname(this.nickname) && !!this.avatarGender; }
  isInLobby():boolean { return this.participant; }
  isConnected():boolean { return this.welcomed && this.socket?.readyState === WebSocket.OPEN; }
  isParticipant():boolean { return this.participant; }
  getConnectionStatus():string { return this.connection.getValue(RoomConnection, 'status') ?? 'solo'; }
  getEntryLabel():string { return this.pendingInvitation ? 'Rejoindre mes amis par le portillon' : 'Partir en carrosse'; }
  subscribeIdentity(listener:()=>void):()=>void {
    this.identitySubscribers.add(listener); listener();
    return () => { this.identitySubscribers.delete(listener); };
  }
  private identityChanged():void {
    this.refreshNavigation();
    for (const listener of this.identitySubscribers) listener();
  }
  setJourneyHandlers(handlers:{depart:()=>void;return:()=>void}):()=>void {
    this.journeyHandlers = handlers;
    return () => { if (this.journeyHandlers === handlers) this.journeyHandlers = undefined; };
  }
  enterLobby():void { if (!this.transition && this.isIdentityReady()) this.journeyHandlers?.depart(); }
  async leaveLobby():Promise<void> { this.journeyHandlers?.return(); }

  prepareJourney():boolean {
    if (this.stopped || this.transition || !this.isIdentityReady()) return false;
    this.setNickname(cleanNickname(this.nickname), false);
    this.room = this.pendingInvitation ?? newRoomId();
    this.transition = true;
    this.desiredPresence = 'observer';
    this.reconnectBlocked = true;
    this.connection.setValue(RoomConnection, 'roomId', this.room);
    this.setStatus('boarding', 'Installez-vous dans le carrosse.');
    this.identityChanged();
    return true;
  }
  connectObserver():void {
    if (!this.transition || !this.room || this.stopped || this.participant) return;
    this.desiredPresence = 'observer';
    this.reconnectBlocked = false;
    this.connect();
  }
  activatePresence():Promise<boolean> {
    if (this.participant) return Promise.resolve(true);
    if (!this.isConnected() || this.stopped || this.activation) return Promise.resolve(false);
    const id = ++this.presenceRequest;
    this.desiredPresence = 'participant';
    return new Promise(resolve => {
      const timer = window.setTimeout(() => {
        if (this.activation?.id !== id) return;
        this.hidePresence();
        this.setStatus('unavailable', 'Arrivee non confirmee. Reessayez ou retournez a l accueil.');
      }, 8000);
      this.activation = { id, resolve, timer };
      this.socket!.send(JSON.stringify({type:'presence', mode:'participant', requestId:id}));
    });
  }
  private settleActivation(ok:boolean):void {
    const activation = this.activation;
    this.activation = undefined;
    if (activation) { clearTimeout(activation.timer); activation.resolve(ok); }
  }
  hidePresence():void {
    this.desiredPresence = 'observer';
    this.participant = false;
    this.settleActivation(false);
    this.voice.disconnect(); this.voice.stopListening();
    if (this.localBody.object3D) this.localBody.object3D.visible = false;
    if (this.isConnected()) {
      this.socket!.send(JSON.stringify({type:'presence', mode:'observer', requestId:++this.presenceRequest}));
      this.updateStatus();
    }
    this.refreshNavigation();
  }
  disconnectJourney():void {
    this.stopRoom();
    history.replaceState(null, '', roomUrl(new URL(location.href), null, import.meta.env.BASE_URL));
    this.setStatus('solo', 'Retour vers le cercle d accueil.');
    this.refreshNavigation();
  }
  finishJourney():void {
    this.disconnectJourney();
    this.transition = false;
    this.setStatus('solo', 'Accueil solo · dirigez-vous vers le portillon pour partir.');
    this.identityChanged();
    this.showAvatarPreview();
  }
  private stopRoom():void {
    this.settleActivation(false);
    this.pendingInvitation = null;
    this.room = ''; this.welcomed = false; this.participant = false;
    this.desiredPresence = 'observer'; this.reconnectBlocked = true;
    clearTimeout(this.retryTimer); clearTimeout(this.connectTimer);
    const socket = this.socket; this.socket = undefined;
    if (socket) { socket.onmessage = null; socket.onclose = null; socket.onerror = null; socket.close(); }
    this.voice.disconnect(); this.voice.stopListening();
    this.clearVisitors(); clockOffset = 0;
    this.connection.setValue(RoomConnection, 'roomId', '');
    this.connection.setValue(RoomConnection, 'serverTime', 0);
  }

  private refreshNavigation():void {
    const inRoom = this.participant;
    this.enterButton.textContent = this.getEntryLabel();
    this.enterButton.hidden = true; this.enterButton.disabled = this.transition;
    this.nicknameLabel.hidden = this.transition;
    this.avatarChoices.hidden = this.transition;
    this.maleButton.disabled = this.femaleButton.disabled = this.transition || inRoom;
    this.nicknameField.disabled = this.transition || inRoom;
    this.leaveButton.hidden = true;
    this.leaveButton.disabled = this.transition;
    this.copy.hidden = !inRoom; this.copyFeedback.hidden = !inRoom;
    this.copyFeedback.style.display = inRoom ? 'block' : 'none';
    this.microphoneButton.hidden = !inRoom; this.listeningButton.hidden = !inRoom; this.voiceStatus.hidden = !inRoom;
    this.voiceStatus.style.display = inRoom ? 'block' : 'none';
    const arrival = this.world.getSceneObject<UIKitMLAsset>('arrival-panel');
    arrival?.requireElementById('arrival-connect').setProperties({display:'none'});
    const text = this.participant ? 'Pour revenir a l accueil, rejoignez le grand portail.' : this.transition ? 'Voyage en cours. Restez assis dans le carrosse.' : this.isIdentityReady() ? 'Traversez le portail dore au portillon pour embarquer.' : 'Choisissez votre pseudo et votre personnage pour ouvrir le portail.';
    arrival?.requireElementById('arrival-status').setProperties({text});
    this.journeyHint.textContent = text;
    const copiedLink = this.panel.querySelector<HTMLInputElement>('#room-copy-link');
    if (copiedLink) copiedLink.hidden = !inRoom;
    if (this.connection.object3D) this.connection.object3D.visible = !this.transition && !!this.avatarGender && !!arrival;
    this.refreshAvatarChoices();
    for (const listener of this.voiceSubscribers) listener(this.voice.state);
  }

  toggleMicrophone():void { if (!this.participant) return; void this.voice.toggleMicrophone(); }
  toggleVoiceListening():void { if (!this.participant) return; void this.voice.toggleListening(); }
  subscribeVoice(listener:(state:VoiceState)=>void):()=>void {
    this.voiceSubscribers.add(listener);
    listener(this.voice.state);
    return () => { this.voiceSubscribers.delete(listener); };
  }

  init(): void {
    const requestedRoom = initialRoom(new URL(location.href));
    try {
      const chosen = localStorage.getItem('plaisance.nickname.v2');
      const legacy = cleanNickname(localStorage.getItem('plaisance.nickname.v1'));
      // Older versions saved automatic Visiteur-xxxx names as if the user chose them.
      this.nickname = chosen !== null ? cleanNickname(chosen) : /^Visiteur-[a-f0-9]{4}$/i.test(legacy) ? '' : legacy;
      this.avatarGender = cleanAvatar(localStorage.getItem('plaisance.avatar.v1'));
    } catch { /* Optional persistence. */ }
    this.pendingInvitation = requestedRoom;
    this.connection = this.world.createTransformEntity(undefined, { persistent: true })
      .addComponent(RoomConnection, { roomId: this.room, nickname:this.nickname, avatar: this.avatarGender ?? '' });
    this.connection.object3D!.name = 'Salon de visite';
    this.localBody = this.world.createTransformEntity(undefined, { persistent: true });
    this.localBody.object3D!.name = 'Votre personnage de cour';
    this.localBody.object3D!.visible = false;
    this.loadLocalBody();
    this.createInvitePanel();
    this.voice = new VoiceSession(packet => {
      if (!this.participant || !this.welcomed || this.socket?.readyState !== WebSocket.OPEN || this.socket.bufferedAmount > 65536) return false;
      this.socket.send(JSON.stringify(packet)); return true;
    }, state => this.refreshVoice(state));
    this.setStatus('solo', 'Accueil solo · deconnecte du salon');
    if (this.pendingInvitation) this.setStatus('solo', 'Choisissez votre pseudo et votre personnage avant d’entrer.');
    const invalidInvitation = !requestedRoom && (new URL(location.href).searchParams.has('roomId') || new URL(location.href).searchParams.has('room'));
    if (invalidInvitation) this.setStatus('solo', 'Lien de salon invalide · accueil solo');
    this.refreshNavigation();
    let unbindArrival = () => {};
    this.cleanupFuncs.push(this.world.activeLevel.subscribe(() => {
      unbindArrival();
      this.arrivalNickname = undefined;
      if (this.connection.object3D) releaseCourtAvatar(this.connection.object3D);
      const panel = this.world.getSceneObject<UIKitMLAsset>('arrival-panel');
      if (!panel) return;
      if (invalidInvitation) panel.requireElementById('arrival-status').setProperties({text:'Lien de salon invalide. Creez un salon ou ouvrez une invitation valide.'});
      const button = panel.requireElementById('arrival-connect'); button.name = 'arrival-connect';
      const input = panel.requireElementById<UIKit.Input>('arrival-nickname');
      this.arrivalNickname = input; input.name = 'arrival-nickname';
      input.element.maxLength = 48; input.element.setAttribute('aria-label', 'Votre pseudo');
      const stopKey = (event:Event) => event.stopPropagation();
      input.element.addEventListener('keydown',stopKey);input.element.addEventListener('keyup',stopKey);
      input.setProperties({value:this.nickname,onValueChange:(value:string)=>this.setNickname(value)});
      const click = () => this.enterLobby(); button.addEventListener('click', click);
      const male = panel.requireElementById('arrival-avatar-male');
      const female = panel.requireElementById('arrival-avatar-female');
      male.name = 'arrival-avatar-male'; female.name = 'arrival-avatar-female';
      const chooseMale = () => this.setAvatar('male');
      const chooseFemale = () => this.setAvatar('female');
      male.addEventListener('click', chooseMale); female.addEventListener('click', chooseFemale);
      this.refreshNavigation();
      this.showAvatarPreview();
      unbindArrival = () => {
        button.removeEventListener('click', click);
        male.removeEventListener('click', chooseMale); female.removeEventListener('click', chooseFemale);
        input.element.removeEventListener('keydown',stopKey);input.element.removeEventListener('keyup',stopKey);
        input.setProperties({onValueChange:undefined});
      };
    }), () => unbindArrival());
    const sendTimer = window.setInterval(() => this.sendPose(), 100);
    const online = () => { if (this.room && !this.welcomed && !this.reconnectBlocked) this.connect(); };
    window.addEventListener('online', online);
    const pageHide = () => this.voice.disconnect();
    window.addEventListener('pagehide', pageHide);
    this.cleanupFuncs.push(() => {
      this.stopped = true;
      this.settleActivation(false); this.identitySubscribers.clear();
      clearInterval(sendTimer);
      clearTimeout(this.retryTimer);
      clearTimeout(this.connectTimer);
      window.removeEventListener('online', online);
      window.removeEventListener('pagehide', pageHide);
      this.voice.dispose();
      this.voiceSubscribers.clear();
      this.socket?.close();
      this.clearVisitors();
      if (this.connection.object3D) releaseCourtAvatar(this.connection.object3D);
      this.connection.dispose();
      if (this.localBody.object3D) releaseCourtAvatar(this.localBody.object3D);
      this.localBody.dispose();
      this.panel.remove();
    });
  }

  private createInvitePanel(): void {
    const panel = document.createElement('div');
    panel.id = 'friends-room';
    panel.style.cssText = 'position:fixed;right:22px;bottom:22px;z-index:30;padding:14px 18px;background:rgba(24,48,39,.94);color:#f5edda;border:1px solid #a8996b;border-radius:8px;font:12px/1.5 system-ui;box-shadow:0 6px 24px #0003;max-width:calc(100vw - 44px)';
    const title = document.createElement('div');
    title.textContent = 'UNE PROMENADE ENTRE AMIS';
    title.style.cssText = 'font-size:10px;letter-spacing:2px;margin-bottom:5px;color:#dcc78f';
    this.status = document.createElement('span');
    this.status.setAttribute('role', 'status');
    this.status.style.display = 'block';
    this.copy = document.createElement('button');
    this.copy.type = 'button';
    this.copy.textContent = 'Copier le lien du salon';
    this.copy.style.cssText = 'margin-top:9px;padding:7px 13px;border:1px solid #d6c591;border-radius:4px;background:#eee4cc;color:#20382b;font:inherit;cursor:pointer';
    this.copyFeedback = document.createElement('span');
    this.copyFeedback.setAttribute('role', 'status');
    this.copyFeedback.style.cssText = 'display:block;font-size:11px;margin-top:4px;max-width:240px';
    this.copy.onclick = async () => {
      if (!this.participant) return;
      const url = new URL(location.href);
      url.searchParams.delete('room'); url.searchParams.set('roomId', this.room);
      try {
        await navigator.clipboard.writeText(url.href);
        this.copyFeedback.textContent = 'Lien copie · envoyez-le a vos amis';
      } catch {
        let input = panel.querySelector<HTMLInputElement>('#room-copy-link');
        if (!input) {
          input = document.createElement('input');
          input.id = 'room-copy-link';
          input.readOnly = true;
          input.setAttribute('aria-label', 'Lien du salon a copier');
          input.style.cssText = 'display:block;width:230px;max-width:100%;margin-top:8px;padding:5px';
          panel.append(input);
        }
        input.value = url.href;
        input.focus();
        input.select();
        this.copyFeedback.textContent = 'Copiez ce lien avec Ctrl+C ou un appui long.';
      }
    };
    this.journeyHint = document.createElement('span');
    this.journeyHint.id = 'room-journey-hint';
    this.journeyHint.style.cssText = 'display:block;max-width:285px;margin-top:6px';
    panel.append(title, this.status, this.journeyHint, this.copy, this.copyFeedback);
    this.nicknameLabel = document.createElement('label');
    this.nicknameLabel.textContent = 'Votre pseudo';
    this.nicknameLabel.style.cssText = 'margin-top:10px';
    this.nicknameField = document.createElement('input');
    this.nicknameField.id = 'room-nickname';this.nicknameField.type = 'text';
    this.nicknameField.value = this.nickname;this.nicknameField.placeholder = 'Votre pseudo';
    this.nicknameField.maxLength = 48;this.nicknameField.setAttribute('autocomplete', 'nickname');
    this.nicknameField.style.cssText = 'display:block;box-sizing:border-box;width:100%;min-height:44px;margin:5px 0;padding:8px;border:1px solid #b49759;border-radius:4px;background:#fffaf0;color:#233e34;font:16px system-ui';
    this.nicknameField.oninput = () => this.setNickname(this.nicknameField.value);
    this.nicknameField.onkeydown = event => event.stopPropagation();
    this.nicknameField.onkeyup = event => event.stopPropagation();
    this.nicknameLabel.append(this.nicknameField);panel.append(this.nicknameLabel);
    this.avatarChoices = document.createElement('div');
    const choiceLabel = document.createElement('div'); choiceLabel.textContent = 'Votre personnage de cour';
    this.maleButton = document.createElement('button'); this.maleButton.id = 'room-avatar-male'; this.maleButton.textContent = 'Homme';
    this.femaleButton = document.createElement('button'); this.femaleButton.id = 'room-avatar-female'; this.femaleButton.textContent = 'Femme';
    this.maleButton.onclick = () => this.setAvatar('male'); this.femaleButton.onclick = () => this.setAvatar('female');
    for (const button of [this.maleButton, this.femaleButton]) {
      button.type = 'button'; button.style.cssText = this.copy.style.cssText + ';min-height:44px;margin-right:8px';
    }
    this.avatarChoices.append(choiceLabel, this.maleButton, this.femaleButton); panel.append(this.avatarChoices);
    this.enterButton = document.createElement('button');
    this.enterButton.id = 'room-enter'; this.enterButton.textContent = 'Creer un salon et entrer';
    this.enterButton.onclick = () => this.enterLobby();
    this.leaveButton = document.createElement('button');
    this.leaveButton.id = 'room-leave'; this.leaveButton.textContent = 'Se deconnecter';
    this.leaveButton.onclick = () => { void this.leaveLobby(); };
    for (const button of [this.enterButton,this.leaveButton]) {
      button.type = 'button';button.style.cssText = this.copy.style.cssText + ';min-height:44px';panel.append(button);
    }
    const controls = document.createElement('div');
    controls.style.cssText = 'display:flex;gap:8px;flex-wrap:wrap;margin-top:10px';
    this.microphoneButton = document.createElement('button');
    this.microphoneButton.id = 'voice-microphone';
    this.microphoneButton.textContent = 'Activer le micro';
    this.microphoneButton.onclick = () => this.toggleMicrophone();
    this.listeningButton = document.createElement('button');
    this.listeningButton.id = 'voice-listening';
    this.listeningButton.textContent = 'Ecouter les voix';
    this.listeningButton.onclick = () => this.toggleVoiceListening();
    for (const button of [this.microphoneButton, this.listeningButton]) {
      button.type = 'button';
      button.style.cssText = 'min-height:44px;padding:8px 11px;border:1px solid #b9ae85;border-radius:4px;background:#eee4cc;color:#20382b;font:inherit;cursor:pointer';
      button.setAttribute('aria-pressed', 'false');
      controls.append(button);
    }
    this.voiceStatus = document.createElement('span');
    this.voiceStatus.id = 'voice-status';
    this.voiceStatus.setAttribute('role', 'status');
    this.voiceStatus.style.cssText = 'display:block;max-width:285px;margin-top:6px;font-size:11px';
    this.voiceStatus.textContent = 'Voix de proximite · micro coupe';
    panel.append(controls, this.voiceStatus);
    document.body.append(panel);
    this.panel = panel;
  }

  private refreshVoice(state:VoiceState):void {
    this.microphoneButton.textContent = state.microphone === 'on' ? 'Couper le micro' : state.microphone === 'requesting' ? 'Annuler le micro' : 'Activer le micro';
    this.microphoneButton.setAttribute('aria-pressed', String(state.microphone === 'on'));
    this.microphoneButton.disabled = !state.roomConnected;
    this.listeningButton.textContent = state.listeningPaused ? "Reprendre l'ecoute" : state.listening ? "Couper l'ecoute" : 'Ecouter les voix';
    this.listeningButton.setAttribute('aria-pressed', String(state.listening));
    this.voiceStatus.textContent = state.error || (state.microphone === 'requesting' ? 'Autorisez le micro dans votre navigateur.' :
      `Voix de proximite · ${state.microphone === 'on' ? 'micro actif' : 'micro coupe'} · ${state.connectedPeers} liaison${state.connectedPeers > 1 ? 's' : ''}`);
    this.connection.setValue(RoomConnection, 'microphone', state.microphone);
    this.connection.setValue(RoomConnection, 'listening', state.listening);
    this.connection.setValue(RoomConnection, 'voicePeers', state.connectedPeers);
    this.connection.setValue(RoomConnection, 'voiceError', state.error);
    for (const listener of this.voiceSubscribers) listener(state);
  }

  private connect(): void {
    if (this.stopped || !this.room || this.reconnectBlocked || this.socket?.readyState === WebSocket.OPEN || this.socket?.readyState === WebSocket.CONNECTING) return;
    clearTimeout(this.retryTimer);
    this.setStatus(navigator.onLine ? 'connecting' : 'offline', navigator.onLine ? 'Connexion au salon…' : 'Hors ligne · visite libre disponible');
    const endpoint = new URL('/rooms', location.href);
    endpoint.protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    endpoint.searchParams.set('room', this.room);
    endpoint.searchParams.set('nickname', cleanNickname(this.nickname));
    endpoint.searchParams.set('avatar', this.avatarGender ?? 'male');
    endpoint.searchParams.set('mode', this.desiredPresence);
    const socket = new WebSocket(endpoint);
    this.socket = socket;
    this.connectTimer = window.setTimeout(() => socket.close(), 12000);
    socket.onmessage = event => {
      if (socket !== this.socket || typeof event.data !== 'string' || event.data.length > 65536) return;
      let message;
      try { message = JSON.parse(event.data); } catch { return; }
      if (message.type === 'welcome') {
        clearTimeout(this.connectTimer);
        this.clearVisitors();
        this.welcomed = true;
        this.selfId = message.id;
        this.iceServers = Array.isArray(message.iceServers) ? message.iceServers : [];
        this.participant = message.mode === 'participant' && this.desiredPresence === 'participant';
        if (this.participant) this.startVoice();
        this.retry = 0;
        clockOffset = message.serverTime - Date.now();
        this.connection.setValue(RoomConnection, 'serverTime', message.serverTime / 1000);
        for (const peer of message.peers) {
          this.addVisitor(peer.id, peer.nickname, peer.avatar);
          if (peer.pose) this.receivePose(peer.id, peer.pose);
        }
        this.updateStatus();
        socket.send(JSON.stringify({ type: 'clock', sent: Date.now() }));
        this.refreshNavigation();
      } else if (message.type === 'presence') {
        if (message.mode === 'participant' && this.activation?.id === message.requestId && this.desiredPresence === 'participant') {
          this.participant = true;
          this.startVoice();
          history.replaceState(null, '', roomUrl(new URL(location.href), this.room, import.meta.env.BASE_URL));
          this.settleActivation(true);
          this.updateStatus(); this.refreshNavigation();
        }
      } else if (message.type === 'clock' && Number.isFinite(message.serverTime) && Number.isFinite(message.sent)) {
        const rtt = Date.now() - message.sent;
        if (rtt >= 0 && rtt < 2000) {
          clockOffset = message.serverTime + rtt / 2 - Date.now();
          this.connection.setValue(RoomConnection, 'serverTime', sharedRoomTime());
        }
      } else if (message.type === 'join') {
        this.addVisitor(message.id, message.nickname, message.avatar);
        this.updateStatus();
      } else if (message.type === 'pose') this.receivePose(message.id, message);
      else if (message.type === 'voice-signal' && this.participant) this.voice.receive(message);
      else if (message.type === 'leave') {
        this.voice.removePeer(message.id);
        const visitor = this.findVisitor(message.id);
        if (visitor) this.disposeVisitor(visitor);
        this.updateStatus();
      }
    };
    socket.onerror = () => {
      if (!this.stopped && socket === this.socket) this.setStatus('unavailable', 'Salon indisponible · nouvelle tentative…');
    };
    socket.onclose = event => {
      if (socket !== this.socket || this.stopped) return;
      clearTimeout(this.connectTimer);
      this.welcomed = false;
      this.participant = false;
      if (this.activation) this.desiredPresence = 'observer';
      this.settleActivation(false);
      this.voice.disconnect();
      this.refreshNavigation();
      this.clearVisitors();
      if (event.code === 4004 || event.code === 1008) {
        this.reconnectBlocked = true;
        this.setStatus(event.code === 4004 ? 'full' : 'refused', event.code === 4004 ? 'Salon complet · 12 visiteurs maximum' : 'Connexion refusee · rechargez la page');
        return;
      }
      this.setStatus(navigator.onLine ? 'reconnecting' : 'offline', navigator.onLine ? 'Connexion perdue · reconnexion…' : 'Hors ligne · visite libre disponible');
      this.retryTimer = window.setTimeout(() => this.connect(), Math.min(15000, 1000 * 2 ** this.retry++) + Math.random() * 500);
    };
  }

  private startVoice():void {
    this.voice.connect(this.selfId, this.iceServers);
    for (const visitor of this.queries.visitors.entities) this.voice.addPeer(visitor.getValue(RemoteVisitor, 'peerId') ?? '');
  }
  private updateStatus(): void {
    const count = this.queries.visitors.entities.size + (this.participant ? 1 : 0);
    if (!this.participant) { this.setStatus('observing', `${count} visiteurs dans le domaine · voyage invisible`); return; }
    this.setStatus('connected', `${count} ${count > 1 ? 'visiteurs' : 'visiteur'} dans ce jardin · salon prive`);
  }

  private setStatus(state: string, label: string): void {
    this.status.textContent = label;
    this.connection.setValue(RoomConnection, 'status', state);
    this.connection.setValue(RoomConnection, 'visitorCount', state === 'connected' ? this.queries.visitors.entities.size + 1 : 0);
  }

  private clearVisitors(): void {
    for (const entity of this.queries.visitors.entities) this.disposeVisitor(entity);
  }

  private disposeVisitor(entity:Entity):void {
    const root = entity.object3D;
    const tag = root && this.nameTags.get(root);
    if (tag) disposeNameTag(tag);
    if (root) { releaseCourtAvatar(root); this.nameTags.delete(root); this.remoteMotion.delete(root); }
    entity.dispose();
  }

  private findVisitor(id: string): Entity | undefined {
    for (const entity of this.queries.visitors.entities) if (entity.getValue(RemoteVisitor, 'peerId') === id) return entity;
    return undefined;
  }

  private addVisitor(id: string, name?:unknown, appearance?:unknown): void {
    if (this.findVisitor(id)) return;
    const avatar = new Group();
    const nickname = visitorNickname(name,id);
    const gender = visitorAvatar(appearance);
    avatar.name = `Visiteur ${id.slice(0, 4)}`;
    avatar.visible = false;
    this.remoteMotion.set(avatar, createAvatarMotion());
    const tag = createNameTag(nickname); tag.position.y = gender === 'female' ? 2.02 : 2.12;
    avatar.add(tag); this.nameTags.set(avatar, tag);
    this.world.createTransformEntity(avatar, { persistent: true }).addComponent(RemoteVisitor, { peerId: id, nickname, avatar: gender });
    void setCourtAvatar(avatar, gender).catch(error => console.error('Visitor avatar could not load', error));
    if (this.participant) this.voice.addPeer(id);
  }

  private receivePose(id: string, pose: Pose): void {
    const entity = this.findVisitor(id);
    if (!entity || !pose.head) return;
    const bands=entity.getVectorView(RemoteVisitor,'voiceBands');
    for(let i=0;i<3;i++)bands[i]=pose.voice?.[i]??0;
    entity.setValue(RemoteVisitor,'voiceReceivedAt',performance.now());
    entity.getVectorView(RemoteVisitor, 'headPosition').set(pose.head.p);
    entity.getVectorView(RemoteVisitor, 'headRotation').set(pose.head.q);
    const feet = entity.getVectorView(RemoteVisitor, 'feetPosition');
    if (pose.feet) feet.set(pose.feet.p);
    else { feet[0] = pose.head.p[0]; feet[1] = pose.head.p[1] - 1.7; feet[2] = pose.head.p[2]; }
    if (pose.left) {
      entity.getVectorView(RemoteVisitor, 'leftPosition').set(pose.left.p);
      entity.getVectorView(RemoteVisitor, 'leftRotation').set(pose.left.q);
    }
    if (pose.right) {
      entity.getVectorView(RemoteVisitor, 'rightPosition').set(pose.right.p);
      entity.getVectorView(RemoteVisitor, 'rightRotation').set(pose.right.q);
    }
    entity.setValue(RemoteVisitor, 'leftVisible', !!pose.left);
    entity.setValue(RemoteVisitor, 'rightVisible', !!pose.right);
    if (entity.object3D && !entity.object3D.visible) {
      entity.object3D.position.fromArray(feet);
      entity.object3D.visible = true;
    }
  }

  private sample(object: Object3D): PosePart {
    object.getWorldPosition(this.position);
    object.getWorldQuaternion(this.rotation);
    return { p: this.position.toArray(), q: this.rotation.toArray() };
  }

  /** Network serialization runs at 10 Hz, outside the render update. */
  private sendPose(): void {
    const socket = this.socket;
    if (!this.participant || !this.welcomed || socket?.readyState !== WebSocket.OPEN || socket.bufferedAmount > 16384) return;
    let left: PosePart | null = null;
    let right: PosePart | null = null;
    const session = this.world.xrSession;
    if (session) for (const source of session.inputSources) {
      if (!source.gripSpace) continue;
      if (source.handedness === 'left') left = this.sample(this.player.gripSpaces.left);
      if (source.handedness === 'right') right = this.sample(this.player.gripSpaces.right);
    }
    const head = this.sample(session ? this.player.head : this.camera);
    this.player.getWorldPosition(this.position);
    const feet: PosePart = { p: [head.p[0], this.position.y, head.p[2]], q: head.q };
    socket.send(JSON.stringify({ type: 'pose', head, feet, left, right, voice:this.voice.localVoiceBands() }));
    if (++this.clockTick % 100 === 0) socket.send(JSON.stringify({ type: 'clock', sent: Date.now() }));
  }

  private updateLocalBody(delta: number): void {
    const body = this.localBody.object3D!;
    const immersive = this.xrManager.isPresenting;
    body.visible = this.participant && !!this.avatarGender;
    setCourtAvatarView(body, immersive ? 'first-person' : 'reflection-only');
    if (immersive !== this.bodyWasImmersive) this.bodyWasVisible = false;
    this.bodyWasImmersive = immersive;
    this.connection.setValue(RoomConnection, 'bodyVisible', body.visible);
    if (!body.visible) { this.bodyWasVisible = false; return; }
    this.oldPosition.copy(this.headPosition);
    const viewer = immersive ? this.player.head : this.camera;
    viewer.getWorldPosition(this.headPosition);
    this.player.getWorldPosition(this.position);
    // Calibrate on entry and when switching screen/XR; crouching must not shrink the skeleton.
    // rfhead in blender-royal-figures.py: eye centre = 1.625 + .024,
    // pupil depth = .071 + .010. Female geometry is uniformly scaled by .95.
    const modelFactor = this.avatarGender === 'female' ? .95 : 1;
    if (!this.bodyWasVisible) body.scale.setScalar(Math.max(.5, Math.min(1.4, (this.headPosition.y - this.position.y) / (1.649 * modelFactor))));
    viewer.getWorldQuaternion(this.rotation);
    this.forward.set(0, 0, -1).applyQuaternion(this.rotation);
    if (Math.hypot(this.forward.x, this.forward.z) > .01) body.quaternion.setFromAxisAngle(this.verticalAxis, Math.atan2(this.forward.x, this.forward.z));
    // Put the viewer at the face, ahead of the torso, even when looking down.
    this.forward.set(0, 0, .081 * modelFactor * body.scale.x).applyQuaternion(body.quaternion);
    body.position.set(this.headPosition.x - this.forward.x, this.position.y, this.headPosition.z - this.forward.z);
    this.localMotion.velocity.subVectors(this.headPosition, this.oldPosition).multiplyScalar(1 / Math.max(delta, .001));
    this.localMotion.velocity.y = 0;
    if (!this.bodyWasVisible || this.headPosition.distanceTo(this.oldPosition) > 3) this.localMotion.velocity.set(0, 0, 0);
    this.bodyWasVisible = true;
    this.localMotion.left.tracked = this.localMotion.right.tracked = false;
    const session = this.world.xrSession;
    if (session) for (const source of session.inputSources) {
      if (!source.gripSpace || (source.handedness !== 'left' && source.handedness !== 'right')) continue;
      const target = this.localMotion[source.handedness];
      this.player.gripSpaces[source.handedness].getWorldPosition(target.position);
      this.player.gripSpaces[source.handedness].getWorldQuaternion(target.quaternion);
      target.tracked = true;
    }
    animateCourtAvatar(body, delta, 0, this.localMotion);
    animateCourtMouth(body, this.voice.localVisemes(delta));
    const diagnostics = courtAvatarDiagnostics(body);
    if (!diagnostics) return;
    this.connection.setValue(RoomConnection, 'animation', diagnostics.mode);
    this.connection.setValue(RoomConnection, 'leftTracked', diagnostics.leftTracked);
    this.connection.setValue(RoomConnection, 'rightTracked', diagnostics.rightTracked);
    this.connection.setValue(RoomConnection, 'leftReachError', diagnostics.leftError);
    this.connection.setValue(RoomConnection, 'rightReachError', diagnostics.rightError);
    this.connection.setValue(RoomConnection, 'leftElbowFlex', diagnostics.leftFlex);
    this.connection.setValue(RoomConnection, 'rightElbowFlex', diagnostics.rightFlex);
    diagnostics.leftWrist.toArray(this.connection.getVectorView(RoomConnection, 'leftWrist'));
    diagnostics.rightWrist.toArray(this.connection.getVectorView(RoomConnection, 'rightWrist'));
    this.localMotion.left.position.toArray(this.connection.getVectorView(RoomConnection, 'leftTarget'));
    this.localMotion.right.position.toArray(this.connection.getVectorView(RoomConnection, 'rightTarget'));
  }

  update(delta: number): void {
    const listener = this.xrManager.isPresenting ? this.player.head : this.camera;
    listener.getWorldPosition(this.position);
    listener.getWorldQuaternion(this.rotation);
    this.forward.set(0, 0, -1).applyQuaternion(this.rotation);
    this.up.set(0, 1, 0).applyQuaternion(this.rotation);
    this.voice.setListener(this.position, this.forward, this.up);
    if (this.connection.object3D?.visible) animateCourtAvatar(this.connection.object3D, delta);
    this.updateLocalBody(delta);
    const alpha = 1 - Math.exp(-14 * Math.min(delta, 0.1));
    for (const entity of this.queries.visitors.entities) {
      const avatar = entity.object3D;
      if (!avatar?.visible) continue;
      const tag=this.nameTags.get(avatar);
      if(tag)animateNameTagVoice(tag,entity.getVectorView(RemoteVisitor,'voiceBands'),delta,
        performance.now()-(entity.getValue(RemoteVisitor,'voiceReceivedAt')??0)<750);
      const motion = this.remoteMotion.get(avatar)!;
      this.oldPosition.copy(avatar.position);
      this.position.fromArray(entity.getVectorView(RemoteVisitor, 'feetPosition'));
      const dx = this.position.x - avatar.position.x, dz = this.position.z - avatar.position.z;
      // Large teleports snap rather than sliding and playing the walking cycle across the garden.
      if (Math.hypot(dx, dz) > 3) avatar.position.copy(this.position);
      else avatar.position.lerp(this.position, alpha);
      this.rotation.fromArray(entity.getVectorView(RemoteVisitor, 'headRotation'));
      this.forward.set(0, 0, -1).applyQuaternion(this.rotation);
      if (Math.hypot(this.forward.x, this.forward.z) > .01) {
        this.bodyRotation.setFromAxisAngle(this.verticalAxis, Math.atan2(this.forward.x, this.forward.z));
        avatar.quaternion.slerp(this.bodyRotation, alpha);
      }
      motion.velocity.subVectors(avatar.position, this.oldPosition).multiplyScalar(1 / Math.max(delta, .001));
      if (Math.hypot(dx, dz) > 3) motion.velocity.set(0, 0, 0);
      this.gripPosition.fromArray(entity.getVectorView(RemoteVisitor, 'leftPosition'));
      this.gripRotation.fromArray(entity.getVectorView(RemoteVisitor, 'leftRotation'));
      if (!motion.left.tracked) { motion.left.position.copy(this.gripPosition); motion.left.quaternion.copy(this.gripRotation); }
      else { motion.left.position.lerp(this.gripPosition, alpha); motion.left.quaternion.slerp(this.gripRotation, alpha); }
      motion.left.tracked = !!entity.getValue(RemoteVisitor, 'leftVisible');
      this.gripPosition.fromArray(entity.getVectorView(RemoteVisitor, 'rightPosition'));
      this.gripRotation.fromArray(entity.getVectorView(RemoteVisitor, 'rightRotation'));
      if (!motion.right.tracked) { motion.right.position.copy(this.gripPosition); motion.right.quaternion.copy(this.gripRotation); }
      else { motion.right.position.lerp(this.gripPosition, alpha); motion.right.quaternion.slerp(this.gripRotation, alpha); }
      motion.right.tracked = !!entity.getValue(RemoteVisitor, 'rightVisible');
      animateCourtAvatar(avatar, delta, 0, motion);
      const diagnostics = courtAvatarDiagnostics(avatar);
      if (diagnostics) {
        entity.setValue(RemoteVisitor, 'animation', diagnostics.mode);
        entity.setValue(RemoteVisitor, 'leftReachError', diagnostics.leftError);
        entity.setValue(RemoteVisitor, 'rightReachError', diagnostics.rightError);
      }
      const peerId = entity.getValue(RemoteVisitor, 'peerId') ?? '';
      this.position.fromArray(entity.getVectorView(RemoteVisitor, 'headPosition'));
      entity.setValue(RemoteVisitor, 'voiceGain', this.voice.setPeerPosition(peerId, this.position, true));
      animateCourtMouth(avatar, this.voice.peerVisemes(peerId, delta));
      entity.setValue(RemoteVisitor, 'voiceConnected', this.voice.isPeerConnected(peerId));
    }
  }
}
