import { createSystem, Euler } from '@iwsdk/core';
import { ComfortSettings } from './comfort-settings.js';
/** Camera look is application-owned; movement remains IWSDK locomotion. */
export class BrowserLookSystem extends createSystem({menus:{required:[ComfortSettings]}}) {
  init() {
    const canvas=this.renderer.domElement;const rotation=new Euler(0,0,0,'YXZ');let down=false;
    const start=(event:PointerEvent)=>{if(event.button!==0||this.xrManager.isPresenting||document.body.classList.contains('mobile-visit'))return;for(const menu of this.queries.menus.entities)if(menu.getValue(ComfortSettings,'open'))return;down=true;canvas.setPointerCapture(event.pointerId);};
    const end=()=>{down=false;};
    const move=(event:PointerEvent)=>{if(!down||this.xrManager.isPresenting)return;rotation.setFromQuaternion(this.camera.quaternion,'YXZ');rotation.y-=event.movementX*.003;rotation.x=Math.max(-1.35,Math.min(1.35,rotation.x-event.movementY*.003));this.camera.quaternion.setFromEuler(rotation);};
    canvas.addEventListener('pointerdown',start);canvas.addEventListener('pointermove',move);canvas.addEventListener('pointerup',end);canvas.addEventListener('lostpointercapture',end);window.addEventListener('blur',end);
    this.cleanupFuncs.push(()=>{canvas.removeEventListener('pointerdown',start);canvas.removeEventListener('pointermove',move);canvas.removeEventListener('pointerup',end);canvas.removeEventListener('lostpointercapture',end);window.removeEventListener('blur',end);});
  }
}
