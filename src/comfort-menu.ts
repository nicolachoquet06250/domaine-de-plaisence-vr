import {
  createSystem, InputComponent, LocomotionSystem, RayInteractable,
  ScreenSpace, UIKitMLAsset, Vector3, Quaternion, VisibilityState,
  type Entity, type UIKit,
} from '@iwsdk/core';
import { ComfortSettings } from './comfort-settings.js';
import { MultiplayerSystem } from './multiplayer.js';
import { CoachJourney } from './coach-journey-components.js';

const STORAGE_KEY = 'plaisance.comfort.v1';
const LEVELS = [0, 25, 50, 75, 100] as const;

export class ComfortMenuSystem extends createSystem({ menus: { required: [ComfortSettings] }, journeys:{required:[CoachJourney]} }) {
  private panel?: UIKitMLAsset;
  private menu?: Entity;
  private disposed = false;
  private open = false;
  private strength = .5;
  private position = new Vector3();
  private orientation = new Quaternion();
  private forward = new Vector3();
  private locomotion!: LocomotionSystem;
  private voiceConnected = false;

  private lastArrival = true;
  private isArrival(): boolean {
    for(const e of this.queries?.journeys?.entities??[])return e.getValue(CoachJourney,'phase')!=='visiting';
    return !!this.world.getSceneObject('arrival-panel');
  }

  private refreshScope(): void {
    const arrival = this.isArrival();
    this.panel?.requireElementById('comfort-session').setProperties({ display: arrival ? 'none' : 'flex' });
    this.panel?.requireElementById('comfort-voice').setProperties({ display: !arrival && this.voiceConnected ? 'flex' : 'none' });
  }

  init(): void {
    this.locomotion = this.world.getSystem(LocomotionSystem)!;
    // Missing, malformed or inaccessible storage preserves IWSDK's default.
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw !== null) {
        const value: unknown = JSON.parse(raw);
        if (typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1) this.strength = value;
      }
    } catch { /* The menu still works when browser storage is unavailable. */ }
    this.locomotion.config.comfortAssist.value = this.strength;

    const onKey = (event: KeyboardEvent) => {
      const target = event.target;
      if (event.repeat || event.ctrlKey || event.metaKey || event.altKey ||
          (target instanceof HTMLElement && (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName)))) return;
      if (event.code === 'KeyM') { event.preventDefault(); this.toggle(); }
      if (event.code === 'Escape' && this.open) { event.preventDefault(); this.setOpen(false); }
      // Also usable without a mouse: press 0…4 to select the five levels.
      if (this.open && /^Digit[0-4]$/.test(event.code)) {
        event.preventDefault(); this.choose(Number(event.code.slice(-1)) / 4);
      }
    };
    window.addEventListener('keydown', onKey);
    this.cleanupFuncs.push(
      () => { this.disposed = true; window.removeEventListener('keydown', onKey); this.menu?.dispose(); },
      this.world.visibilityState.subscribe(() => { if (this.open) this.setOpen(false); }),
      this.world.activeLevel.subscribe(() => { this.closeMenu(); this.refreshScope(); }),
    );
    this.world.assets.instantiate<UIKitMLAsset>('comfort-menu').then(panel => {
      if (this.disposed) { panel.dispose(); return; }
      this.panel = panel;
      panel.name = 'Menu de confort';
      this.menu = this.world.createTransformEntity(panel, { persistent: true })
        .addComponent(ComfortSettings, { strength: this.strength, appliedStrength: this.locomotion.config.comfortAssist.peek() });
      panel.visible = false;
      for (const percent of LEVELS) {
        const button = panel.requireElementById(`comfort-${percent}`);
        button.name = `comfort-${percent}`;
        const click = () => { if (this.open) this.choose(percent / 100); };
        button.addEventListener('click', click);
        this.cleanupFuncs.push(() => button.removeEventListener('click', click));
      }
      const close = panel.requireElementById('comfort-close');
      close.name = 'comfort-close';
      const onClose = () => this.setOpen(false);
      close.addEventListener('click', onClose);
      this.cleanupFuncs.push(() => close.removeEventListener('click', onClose));
      const multiplayer = this.world.getSystem(MultiplayerSystem);
      if (multiplayer?.subscribeVoice) {
        const session = panel.requireElementById('comfort-session'); session.name = 'comfort-session';
        const onSession = () => {
          if (!this.open || this.isArrival()) return;
          this.closeMenu();
          if (multiplayer.isInLobby()) void multiplayer.leaveLobby(); else multiplayer.enterLobby();
        };
        session.addEventListener('click', onSession);
        this.cleanupFuncs.push(() => session.removeEventListener('click', onSession));
        const mic = panel.requireElementById('comfort-microphone');
        const listen = panel.requireElementById('comfort-listening');
        mic.name = 'comfort-microphone'; listen.name = 'comfort-listening';
        const onMic = () => { if (this.open && !this.isArrival()) multiplayer.toggleMicrophone(); };
        const onListen = () => { if (this.open && !this.isArrival()) multiplayer.toggleVoiceListening(); };
        mic.addEventListener('click', onMic); listen.addEventListener('click', onListen);
        this.cleanupFuncs.push(() => mic.removeEventListener('click', onMic), () => listen.removeEventListener('click', onListen),
          multiplayer.subscribeVoice(state => {
            const inLobby = multiplayer.isInLobby?.() ?? state.roomConnected;
            session.setProperties({text:inLobby ? 'Se deconnecter' : multiplayer.getEntryLabel().normalize('NFD').replace(/\p{Diacritic}/gu, '')});
            this.voiceConnected = inLobby;
            this.refreshScope();
            mic.setProperties({text:state.microphone === 'on' ? 'Couper le micro' : state.microphone === 'requesting' ? 'Annuler le micro' : 'Activer le micro'});
            listen.setProperties({text:state.listeningPaused ? "Reprendre l'ecoute" : state.listening ? "Couper l'ecoute" : 'Ecouter les voix'});
            const status = state.error || (state.microphone === 'requesting' ? 'Autorisez le micro dans le navigateur.' :
              `Micro ${state.microphone === 'on' ? 'actif' : 'coupe'} - ${state.connectedPeers} voix connectees`);
            // The bundled bitmap font does not contain accented French glyphs.
            panel.requireElementById<UIKit.Text>('comfort-voice-status').setProperties({text:status.normalize('NFD').replace(/\p{Diacritic}/gu, '')});
          }));
      }
      this.refresh();
      this.refreshScope();
    }).catch(error => console.error('[Plaisance] Impossible de charger le menu de confort', error));
  }

  toggle(): void { this.setOpen(!this.open); }
  closeMenu(): void { this.setOpen(false); }

  private setOpen(open: boolean): void {
    if (!this.panel || !this.menu || this.open === open) return;
    this.open = open;
    this.menu.setValue(ComfortSettings, 'open', open);
    if (open) {
      this.refreshScope();
      const isVR = this.visibilityState.peek() !== VisibilityState.NonImmersive;
      if (isVR) {
        if (this.menu.hasComponent(ScreenSpace)) this.menu.removeComponent(ScreenSpace);
        // Anchor once, facing the head. It remains still while the user points.
        this.camera.getWorldPosition(this.position);
        this.camera.getWorldQuaternion(this.orientation);
        this.forward.set(0, 0, -1).applyQuaternion(this.orientation);
        this.panel.position.copy(this.position).addScaledVector(this.forward, 1.25);
        this.panel.quaternion.copy(this.orientation);
      } else {
        const mobile = document.body.classList.contains('mobile-visit');
        this.menu.addComponent(ScreenSpace, {
          left: 'max(16px, calc(50vw - 200px))',
          top: mobile ? 'max(104px, calc(env(safe-area-inset-top) + 60px))' : '10vh',
          width: 'min(400px, calc(100vw - 32px))',
          height: mobile ? 'calc(100dvh - max(125px, calc(env(safe-area-inset-top) + 80px)))' : '80vh',
        });
      }
      this.menu.addComponent(RayInteractable);
    } else {
      // Hidden panels must not intercept world rays or pointer clicks.
      this.menu.removeComponent(RayInteractable);
      if (this.menu.hasComponent(ScreenSpace)) this.menu.removeComponent(ScreenSpace);
      // ScreenSpace reparents the document to the camera. Removing the component
      // alone does not undo that: restore it before the next browser/VR opening.
      this.panel.add(this.panel.document);
      this.panel.document.clearTargetDimensions();
      this.panel.document.position.set(0, 0, 0);
      this.panel.document.quaternion.identity();
    }
    this.panel.visible = open;
    this.panel.requireElementById('comfort-root').setProperties({ display: open ? 'flex' : 'none' });
  }

  private choose(strength: number): void {
    this.strength = Math.max(0, Math.min(1, strength));
    this.locomotion.config.comfortAssist.value = this.strength;
    this.menu?.setValue(ComfortSettings, 'strength', this.strength);
    this.menu?.setValue(ComfortSettings, 'appliedStrength', this.locomotion.config.comfortAssist.peek());
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.strength));
      this.panel?.requireElementById<UIKit.Text>('comfort-saved').setProperties({ text: 'Choix conserve sur cet appareil.' });
    } catch {
      this.panel?.requireElementById<UIKit.Text>('comfort-saved').setProperties({ text: 'Choix actif pour cette visite.' });
    }
    this.refresh();
  }

  private refresh(): void {
    if (!this.panel) return;
    const value = Math.round(this.strength * 100);
    this.panel.requireElementById<UIKit.Text>('comfort-value').setProperties({ text: `Intensite : ${value} %` });
    for (const percent of LEVELS) this.panel.requireElementById(`comfort-${percent}`).setProperties({
      backgroundColor: percent === value ? '#233e34' : '#e3dac5',
      color: percent === value ? '#f5efe0' : '#233e34',
    });
  }

  update(): void {
    const arrival=this.isArrival();
    if(arrival!==this.lastArrival){this.lastArrival=arrival;this.closeMenu();this.refreshScope();}
    if (this.xrManager.isPresenting && this.input.xr.gamepads.right?.getButtonDown(InputComponent.B_Button)) this.toggle();
  }
}
