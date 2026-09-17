import { createSystem, LocomotionSystem, Vector3 } from '@iwsdk/core';
import { ArrivalBoundary } from './arrival-boundary-components.js';
import { CoachJourney } from './coach-journey-components.js';

/** Last-resort recovery after a loading fall or a room-scale step beyond the terrace. */
export class ArrivalBoundarySystem extends createSystem({bounds:{required:[ArrivalBoundary]},journeys:{required:[CoachJourney]}}) {
  private eye=new Vector3();private origin=new Vector3();private center=new Vector3();private target=new Vector3();
  private cooldown=0;
  update(delta:number):void {
    for(const e of this.queries.journeys?.entities??[])if(e.getValue(CoachJourney,'phase')!=='arrival')return;
    this.cooldown=Math.max(0,this.cooldown-delta);if(this.cooldown>0)return;
    for(const entity of this.queries.bounds.entities) {
      if(!entity.object3D?.parent)continue;
      entity.object3D.getWorldPosition(this.center);
      this.player.getWorldPosition(this.origin);
      (this.xrManager.isPresenting?this.player.head:this.camera).getWorldPosition(this.eye);
      if(this.origin.y>=this.center.y-.5&&Math.hypot(this.eye.x-this.center.x,this.eye.z-this.center.z)<=(entity.getValue(ArrivalBoundary,'radius')??8.1))continue;
      this.target.fromArray(entity.getVectorView(ArrivalBoundary,'spawn')).add(this.center);
      // Preserve physical head tracking while moving its locomotion origin back inside.
      this.target.x-=this.eye.x-this.origin.x;this.target.z-=this.eye.z-this.origin.z;
      const locomotion=this.world.getSystem(LocomotionSystem);if(!locomotion)continue;
      locomotion.setPlayerPosition(this.target);this.cooldown=.75;
      entity.setValue(ArrivalBoundary,'recoveries',(entity.getValue(ArrivalBoundary,'recoveries')??0)+1);
    }
  }
}
