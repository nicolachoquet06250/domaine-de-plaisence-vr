import { createSystem, Quaternion, Vector3, VisibilityState, type Object3D } from '@iwsdk/core';
import { ArrivalPortalHint, CoachJourney, CoachPortal } from './coach-journey-components.js';

/** Camera-local direction, without reversing left/right for targets behind the viewer. */
export function portalDirectionSide(local:Vector3,previous:number):number {
  const radius=Math.hypot(local.x,local.z);
  if(radius<.65)return 0;
  // A small dead zone prevents jitter while looking directly at the portal.
  const centred=previous===0?.14:.09;
  if(local.z<0&&Math.abs(local.x)<radius*centred)return 0;
  // At exactly 180 degrees either turn is valid; preserve the last direction.
  if(local.z>=0&&Math.abs(local.x)<radius*.06)return previous||1;
  return local.x<0?-1:1;
}

/** Small camera-relative, non-interactive hint shared by desktop, mobile and XR. */
export class PortalDirectionSystem extends createSystem({
  journeys:{required:[CoachJourney]},portals:{required:[CoachPortal]},hints:{required:[ArrivalPortalHint]},
}) {
  private eye=new Vector3();private local=new Vector3();private offset=new Vector3();
  private orientation=new Quaternion();private inverse=new Quaternion();
  private elapsed=0;private side=0;private disposed=false;

  init():void {
    this.cleanupFuncs.push(()=>{this.disposed=true;for(const entity of this.queries.hints.entities)entity.dispose();});
    void this.world.assets.instantiate<Object3D>('portalDirection').then(object=>{
      if(this.disposed)return;
      object.visible=false;
      this.world.createTransformEntity(object,{persistent:true}).addComponent(ArrivalPortalHint);
    }).catch(error=>console.error('[Plaisance] Indication du portail',error));
  }

  update(delta:number):void {
    let available=false;
    for(const journey of this.queries.journeys.entities){
      available=journey.getValue(CoachJourney,'phase')==='arrival'&&!!journey.getValue(CoachJourney,'identityReady');
    }
    const immersive=this.xrManager.isPresenting,viewer=immersive?this.player.head:this.camera;
    viewer.getWorldPosition(this.eye);viewer.getWorldQuaternion(this.orientation);
    available=available&&Math.hypot(this.eye.x,this.eye.z)<8.1&&this.visibilityState.peek()!==VisibilityState.VisibleBlurred;
    let portal:Object3D|undefined;
    if(available)for(const entity of this.queries.portals.entities){
      if(entity.getValue(CoachPortal,'destination')==='castle'&&entity.object3D?.visible){portal=entity.object3D;break;}
    }
    let side=0;
    if(portal){
      portal.getWorldPosition(this.local);this.local.y+=1.17;
      this.inverse.copy(this.orientation).invert();this.local.sub(this.eye).applyQuaternion(this.inverse);
      side=portalDirectionSide(this.local,this.side);
    }
    if(side)this.elapsed=(this.elapsed+Math.min(delta,.05))%100;
    // Keep a comfortable stereo depth; desktop position follows the actual aspect/FOV.
    const depth=1.7,edge=immersive?.52:.78/this.camera.projectionMatrix.elements[0];
    const pulse=Math.sin(this.elapsed*Math.PI*2/1.3);
    this.offset.set(side*depth*(edge+.012*pulse),0,-depth).applyQuaternion(this.orientation).add(this.eye);
    for(const entity of this.queries.hints.entities){
      const object=entity.object3D;if(!object)continue;
      object.visible=side!==0;
      if(side){object.position.copy(this.offset);object.quaternion.copy(this.orientation);if(side<0)object.rotateZ(Math.PI);object.scale.setScalar(.3*(1+.04*pulse));}
      if(entity.getValue(ArrivalPortalHint,'side')!==side)entity.setValue(ArrivalPortalHint,'side',side);
    }
    this.side=side;
  }
}
