/** Opt-in ECS probe; never registered in the shipped app. */
import { createSystem, Group } from '@iwsdk/core';
import { RoomConnection } from '../src/multiplayer-components.js';
import { animateCourtAvatar, courtHairDiagnostics, setCourtAvatar } from '../src/court-avatar.js';

export class HairBrowserHarness extends createSystem({probes:{required:[RoomConnection]}}) {
  init() {
    for (const gender of ['male','female'] as const) {
      const root=new Group();root.name=`Verification cheveux ${gender}`;
      root.position.set(gender==='male'?-.19:.19,gender==='male'?0:.0825,-.85);
      const entity=this.world.createTransformEntity(root,{persistent:true}).addComponent(RoomConnection,{status:'hair-loading',avatar:gender});
      void setCourtAvatar(root,gender).then(()=>entity.setValue(RoomConnection,'status','hair-ready'));
    }
  }
  update(delta:number) {
    for (const entity of this.queries.probes.entities) {
      if (!entity.object3D?.name.startsWith('Verification cheveux')) continue;
      const root=entity.object3D;
      if (entity.getValue(RoomConnection,'status')!=='hair-ready') continue;
      // 'serverTime' is an externally controllable head turn for pause/step tests.
      root.rotation.y=entity.getValue(RoomConnection,'serverTime')??0;
      animateCourtAvatar(root,delta);
      const hair=courtHairDiagnostics(root);if (!hair?.length) continue;
      let rootError=0,stretch=0,deflection=0,steps=0;
      for (const h of hair) {
        rootError=Math.max(rootError,h.solver.maxRootError);stretch=Math.max(stretch,h.solver.maxLengthError);
        deflection=Math.max(deflection,h.solver.maxDeflection);steps+=h.solver.simulatedSteps;
      }
      entity.setValue(RoomConnection,'leftReachError',rootError);
      entity.setValue(RoomConnection,'rightReachError',stretch);
      entity.setValue(RoomConnection,'leftElbowFlex',deflection);
      entity.setValue(RoomConnection,'visitorCount',steps);
      entity.setValue(RoomConnection,'voicePeers',hair.length);
    }
  }
}
