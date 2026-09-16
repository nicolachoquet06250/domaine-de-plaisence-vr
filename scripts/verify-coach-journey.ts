// Opt-in managed-runtime diagnostic. Temporarily call after registering systems;
// never imported by the production entry point. Uses real UI, portal and socket.
import { LocomotionSystem, Vector3, type World } from '@iwsdk/core';
import { CoachJourney } from '../src/coach-journey-components.js';
import { CoachJourneySystem } from '../src/coach-journey.js';
import { MultiplayerSystem } from '../src/multiplayer.js';

export function verifyCoachJourney(world:World):void {
  const journey=world.getSystem(CoachJourneySystem)!,network=world.getSystem(MultiplayerSystem)!;
  const saved=new Map(['plaisance.nickname.v2','plaisance.avatar.v1'].map(k=>[k,localStorage.getItem(k)]));
  let started=false,visited=false,last='',returnAt=0;
  const began=performance.now(),point=new Vector3();
  const timer=window.setInterval(()=>{
    const phase=journey.getPhase(),progress=world.playerEntity.getValue(CoachJourney,'progress')??0;
    const key=`${phase}:${progress>=.5}:${network.getConnectionStatus()}`;
    if(key!==last){last=key;console.info('COACH_QA',JSON.stringify({phase,progress,connected:network.isConnected(),participant:network.isParticipant(),effects:world.playerEntity.getValue(CoachJourney,'effectsEnabled'),domain:world.playerEntity.getValue(CoachJourney,'domainLoaded'),eye:world.camera.getWorldPosition(point).toArray()}));}
    if(!started&&performance.now()-began>12000){
      const field=document.getElementById('room-nickname') as HTMLInputElement;
      if(!field)return;field.value='Verification carrosse';field.dispatchEvent(new Event('input',{bubbles:true}));
      document.getElementById('room-avatar-female')?.click();
      world.getSystem(LocomotionSystem)?.setPlayerPosition(new Vector3(6.8,0,0));started=true;
    }
    if(phase==='visiting'&&!visited){visited=true;returnAt=performance.now()+20000;}
    if(visited&&phase==='visiting'&&performance.now()>=returnAt)world.getSystem(LocomotionSystem)?.setPlayerPosition(new Vector3(100,.12,-66));
    if(visited&&phase==='arrival'||performance.now()-began>300000){
      window.clearInterval(timer);
      for(const [k,v] of saved){if(v===null)localStorage.removeItem(k);else localStorage.setItem(k,v);}
      console.info('COACH_QA_DONE',JSON.stringify({success:visited&&phase==='arrival',elapsed:performance.now()-began}));
    }
  },250);
}
