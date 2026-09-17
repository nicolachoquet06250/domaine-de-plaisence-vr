import { createSystem, Euler, TurnSystem, getRequiredInputProvider, ScreenSpace, UIKitMLAsset } from '@iwsdk/core';
import { ComfortSettings } from './comfort-settings.js';
import { ComfortMenuSystem } from './comfort-menu.js';
import { TouchInputState, attachTouchAxes } from './mobile-input.js';
import { isMobileTouchDevice } from './mobile-device.js';
import { CoachJourney } from './coach-journey-components.js';
import './mobile-controls.css';

export class MobileControlsSystem extends createSystem({ menus: { required: [ComfortSettings] },journeys:{required:[CoachJourney]} }) {
  private syncUI = () => {};

  init(): void {
    const state = new TouchInputState();
    const rotation = new Euler(0, 0, 0, 'YXZ');
    const oldRatio = this.renderer.getPixelRatio();
    const media = matchMedia('(any-pointer: coarse)');
    // Never create virtual controls on desktops or headset browsers, even in 2D.
    if (!isMobileTouchDevice(navigator, media.matches)) return;
    let enabled = false, estateOpen = false, friendsOpen = false;
    let previousBlocked: boolean | undefined, previousComfort: boolean | undefined;
    let centreX = 0, centreY = 0, radius = 1;
    const overlay = document.createElement('div');
    overlay.id = 'mobile-controls'; overlay.hidden = true;
    overlay.innerHTML = `<nav class="mobile-toolbar" aria-label="Visite tactile">
      <button type="button" id="mobile-estate" aria-expanded="false">Domaine</button>
      <button type="button" id="mobile-comfort" aria-expanded="false">Confort</button>
      <button type="button" id="mobile-friends" aria-expanded="false">Amis</button>
    </nav><div class="mobile-pad mobile-stick" id="mobile-stick" aria-label="Joystick de deplacement">
      <span class="mobile-stick-label">Se deplacer</span><span class="mobile-stick-knob"></span>
    </div><div class="mobile-pad mobile-look" id="mobile-look" aria-label="Glisser pour regarder">Glisser pour regarder</div>`;
    document.body.append(overlay);
    const stick = overlay.querySelector<HTMLElement>('#mobile-stick')!;
    const look = overlay.querySelector<HTMLElement>('#mobile-look')!;
    const knob = overlay.querySelector<HTMLElement>('.mobile-stick-knob')!;
    const estateButton = overlay.querySelector<HTMLButtonElement>('#mobile-estate')!;
    const comfortButton = overlay.querySelector<HTMLButtonElement>('#mobile-comfort')!;
    const friendsButton = overlay.querySelector<HTMLButtonElement>('#mobile-friends')!;
    const comfortOpen = () => {
      for (const menu of this.queries.menus.entities) if (menu.getValue(ComfortSettings, 'open')) return true;
      return false;
    };
    const traveling = () => {
      for(const e of this.queries.journeys?.entities??[])if(e.getValue(CoachJourney,'traveling'))return true;
      return false;
    };
    const menusBlocked = () => estateOpen || friendsOpen || comfortOpen();
    const blocked = () => menusBlocked() || traveling();
    let lastPhase='';
    const phase = () => {
      for(const e of this.queries.journeys?.entities??[])return e.getValue(CoachJourney,'phase')??'arrival';
      return this.world.getSceneObject('arrival-panel')?'arrival':'visiting';
    };
    const reset = () => {
      const moveId = state.movePointer, lookId = state.lookPointer;
      state.reset(); knob.style.transform = '';
      if (moveId !== null && stick.hasPointerCapture(moveId)) stick.releasePointerCapture(moveId);
      if (lookId !== null && look.hasPointerCapture(lookId)) look.releasePointerCapture(lookId);
    };
    const estateLayout = () => {
      const arrival = phase()!=='visiting';
      estateButton.hidden = arrival;
      friendsButton.textContent = arrival ? 'Accueil' : 'Amis';
      const panel = this.world.getSceneObject<UIKitMLAsset>('estate-panel');
      const entity = this.world.getSceneEntity('estate-panel');
      if (!panel || !entity) return;
      panel.requireElementById('estate-root').setProperties({ display: arrival || (enabled && !estateOpen) ? 'none' : 'flex' });
      if (entity.hasComponent(ScreenSpace)) {
        entity.setValue(ScreenSpace, 'top', enabled ? 'max(104px, calc(env(safe-area-inset-top) + 60px))' : '18px');
        entity.setValue(ScreenSpace, 'left', enabled ? 'max(12px, calc(50vw - 160px))' : '18px');
        entity.setValue(ScreenSpace, 'width', enabled ? 'min(320px, calc(100vw - 24px))' : '285px');
        entity.setValue(ScreenSpace, 'height', enabled ? 'calc(100dvh - max(125px, calc(env(safe-area-inset-top) + 80px)))' : '285px');
      }
    };
    this.syncUI = () => {
      const current=phase();
      if(current!==lastPhase){lastPhase=current;estateOpen=friendsOpen=false;document.body.classList.remove('mobile-friends-open');estateLayout();}
      const next = blocked();
      if (next !== previousBlocked) {
        reset(); previousBlocked = next;
        overlay.dataset.blocked = String(menusBlocked());
      }
      overlay.dataset.blocked = String(menusBlocked());
      overlay.dataset.traveling = String(traveling());
      const menuOpen = comfortOpen();
      if (menuOpen !== previousComfort) {
        previousComfort = menuOpen; comfortButton.setAttribute('aria-expanded', String(menuOpen));
      }
    };
    const refresh = () => {
      reset();
      enabled = isMobileTouchDevice(navigator, media.matches) && !this.xrManager.isPresenting;
      overlay.hidden = !enabled;
      document.body.classList.toggle('mobile-visit', enabled);
      if (!enabled) {
        estateOpen = friendsOpen = false; document.body.classList.remove('mobile-friends-open');
        estateButton.setAttribute('aria-expanded','false'); friendsButton.setAttribute('aria-expanded','false');
      }
      estateLayout(); this.syncUI();
      if (!this.xrManager.isPresenting) this.renderer.setPixelRatio(enabled ? Math.min(devicePixelRatio,1.5) : oldRatio);
    };
    const showEstate = () => {
      reset(); estateOpen = !estateOpen; friendsOpen = false;
      this.world.getSystem(ComfortMenuSystem)?.closeMenu();
      document.body.classList.remove('mobile-friends-open');
      estateButton.setAttribute('aria-expanded', String(estateOpen)); friendsButton.setAttribute('aria-expanded', 'false');
      estateLayout(); this.syncUI();
    };
    const showFriends = () => {
      reset(); friendsOpen = !friendsOpen; estateOpen = false;
      this.world.getSystem(ComfortMenuSystem)?.closeMenu();
      document.body.classList.toggle('mobile-friends-open', friendsOpen);
      friendsButton.setAttribute('aria-expanded', String(friendsOpen)); estateButton.setAttribute('aria-expanded', 'false');
      estateLayout(); this.syncUI();
    };
    const showComfort = () => {
      reset(); estateOpen = friendsOpen = false;
      document.body.classList.remove('mobile-friends-open');
      friendsButton.setAttribute('aria-expanded', 'false'); estateButton.setAttribute('aria-expanded', 'false');
      estateLayout(); this.world.getSystem(ComfortMenuSystem)?.toggle(); this.syncUI();
    };
    const move = (event: PointerEvent) => {
      if (!enabled || blocked() || !state.move(event.pointerId, event.clientX-centreX, event.clientY-centreY, radius)) return;
      event.preventDefault(); knob.style.transform = `translate(${state.x*radius}px, ${state.y*radius}px)`;
    };
    const down = (event: PointerEvent) => {
      if (!enabled || blocked() || event.button !== 0 || !state.beginMove(event.pointerId)) return;
      const rect = stick.getBoundingClientRect();
      centreX = rect.left+rect.width/2; centreY = rect.top+rect.height/2; radius = rect.width*.32;
      stick.setPointerCapture(event.pointerId); move(event);
    };
    const lookDown = (event: PointerEvent) => {
      if (!enabled || menusBlocked() || event.button !== 0 || !state.beginLook(event.pointerId,event.clientX,event.clientY)) return;
      event.preventDefault(); look.setPointerCapture(event.pointerId);
    };
    const lookMove = (event: PointerEvent) => {
      if (!enabled || menusBlocked() || state.lookPointer !== event.pointerId) return;
      event.preventDefault();
      rotation.setFromQuaternion(this.camera.quaternion, 'YXZ');
      rotation.y -= (event.clientX-state.lookX)*.004;
      rotation.x = Math.max(-1.35,Math.min(1.35,rotation.x-(event.clientY-state.lookY)*.004));
      state.lookX = event.clientX; state.lookY = event.clientY;
      this.camera.quaternion.setFromEuler(rotation);
    };
    const up = (event: PointerEvent) => {
      state.end(event.pointerId);
      if (state.movePointer === null) knob.style.transform = '';
      const target = event.currentTarget as HTMLElement;
      if (target.hasPointerCapture(event.pointerId)) target.releasePointerCapture(event.pointerId);
    };
    const provider = getRequiredInputProvider('MobileControlsSystem', this.world.getSystem(TurnSystem)!.config.inputProvider.peek());
    this.cleanupFuncs.push(attachTouchAxes(provider, state, () => enabled, blocked));
    const listen = (target: EventTarget, name: string, handler: EventListener) => {
      target.addEventListener(name, handler);
      this.cleanupFuncs.push(() => target.removeEventListener(name, handler));
    };
    listen(stick,'pointerdown',down as EventListener); listen(stick,'pointermove',move as EventListener);
    listen(look,'pointerdown',lookDown as EventListener); listen(look,'pointermove',lookMove as EventListener);
    for (const target of [stick,look]) for (const name of ['pointerup','pointercancel','lostpointercapture']) listen(target,name,up as EventListener);
    listen(estateButton,'click',showEstate); listen(comfortButton,'click',showComfort); listen(friendsButton,'click',showFriends);
    listen(window,'blur',reset); listen(document,'visibilitychange',reset); listen(window,'resize',refresh);
    listen(media,'change',refresh);
    this.xrManager.addEventListener('sessionstart',refresh); this.xrManager.addEventListener('sessionend',refresh);
    this.cleanupFuncs.push(this.world.activeLevel.subscribe(() => {
      estateOpen = friendsOpen = false;
      document.body.classList.remove('mobile-friends-open');
      estateButton.setAttribute('aria-expanded', 'false'); friendsButton.setAttribute('aria-expanded', 'false');
      estateLayout(); this.syncUI();
    }), () => {
      reset(); overlay.remove(); document.body.classList.remove('mobile-visit','mobile-friends-open');
      this.xrManager.removeEventListener('sessionstart',refresh); this.xrManager.removeEventListener('sessionend',refresh);
      this.renderer.setPixelRatio(oldRatio);
    });
    refresh();
  }

  update(): void { this.syncUI(); }
}
