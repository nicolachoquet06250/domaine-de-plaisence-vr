import { createSystem, UIKitMLAsset, type UIKit } from '@iwsdk/core';
import { installVRViewHeight } from './vr-view-height.js';
import { isVRHeadsetBrowser } from './vr-device.js';

/** Explicit entry remains available without the browser's optional offerSession UI. */
export class VREntrySystem extends createSystem({}) {
  init(): void {
    this.cleanupFuncs.push(installVRViewHeight(this.xrManager));
    let unbind = () => {};
    const bind = () => {
      unbind();
      const cleanups: (() => void)[] = [];
      unbind = () => { for (const cleanup of cleanups) cleanup(); };
      for (const id of ['estate-panel', 'arrival-panel']) {
      const panel = this.world.getSceneObject<UIKitMLAsset>(id);
      if (!panel) continue;
      let active = true;
      let available = false;
      const button = panel.requireElementById('enter-vr');
      button.name = 'enter-vr';
      const label = panel.requireElementById<UIKit.Text>('enter-vr-label');
      const status = panel.requireElementById<UIKit.Text>('vr-status');
      button.setProperties({ display: 'none' });
      status.setProperties({ display: 'none' });
      if (!isVRHeadsetBrowser(navigator)) continue;
      status.setProperties({ display: 'flex' });
      let checkId = 0;
      const report = (text: string) => { if (active) status.setProperties({ text }); };
      const check = async () => {
        const request = ++checkId;
        available = false;
        button.setProperties({ display: 'none' });
        if (!isSecureContext) {
          report('Ouvrez le domaine en HTTPS pour utiliser la VR.');
          return;
        }
        if (!navigator.xr) {
          report('Ouvrez ce lien dans le navigateur du casque pour la VR.');
          return;
        }
        try {
          const supported = await navigator.xr.isSessionSupported('immersive-vr');
          if (!active || request !== checkId) return;
          available = supported;
          button.setProperties({ display: available ? 'flex' : 'none' });
          report(available ? 'Casque compatible. Cliquez pour commencer.' : 'Aucun casque VR disponible dans ce navigateur.');
        } catch {
          if (!active || request !== checkId) return;
          report('Acces VR indisponible. Verifiez les autorisations du navigateur.');
        }
      };
      const click = () => {
        if (this.xrManager.isPresenting) return;
        if (!available) { void check(); return; }
        // Keep requestSession in the user gesture, with the project's XR options.
        report('Confirmez la demande du navigateur. Vous pouvez reessayer ici.');
        this.world.launchXR();
      };
      const refresh = () => {
        const presenting = this.xrManager.isPresenting;
        label.setProperties({ text: presenting ? 'VR active' : 'Entrer en VR' });
        if (!presenting) void check();
      };
      button.addEventListener('click', click);
      this.xrManager.addEventListener('sessionstart', refresh);
      this.xrManager.addEventListener('sessionend', refresh);
      navigator.xr?.addEventListener('devicechange', refresh);
      cleanups.push(() => {
        active = false;
        button.removeEventListener('click', click);
        this.xrManager.removeEventListener('sessionstart', refresh);
        this.xrManager.removeEventListener('sessionend', refresh);
        navigator.xr?.removeEventListener('devicechange', refresh);
      });
      refresh();
      }
    };
    this.cleanupFuncs.push(this.world.activeLevel.subscribe(bind), () => unbind());
  }
}
