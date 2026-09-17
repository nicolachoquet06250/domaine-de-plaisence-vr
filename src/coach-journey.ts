import {
  createSystem, AnimationMixer, AssetManager, Group, LocomotionSystem, SlideSystem,
  TurnSystem, TeleportSystem, Vector3, Quaternion, RayInteractable, UIKitMLAsset,
  VisibilityState, type Object3D, type AnimationAction,
} from '@iwsdk/core';
import { CoachJourney, CoachVehicle, CoachPortal, type JourneyPhase } from './coach-journey-components.js';
import { createCoachRoutes, ARRIVAL_DROP, CASTLE_DROP, COACH_SEAT, CRUISE_SPEED, WALK_SPEED, type CoachRoute } from './coach-route.js';
import { MultiplayerSystem } from './multiplayer.js';
import { ComfortMenuSystem } from './comfort-menu.js';

type Pausable = { isPaused:boolean; stop():void; play():void };

/** One local carriage, surviving the background upgrade to the complete domain. */
export class CoachJourneySystem extends createSystem({
  vehicles:{required:[CoachVehicle]}, portals:{required:[CoachPortal]},
}) {
  private multiplayer!:MultiplayerSystem;
  private routes=createCoachRoutes();
  private route:CoachRoute=this.routes.outbound;
  private phase:JourneyPhase='arrival';
  private distance=0;private speed=0;private wheelsDistance=0;private halfway=false;
  private loaded=false;private loading=false;private loadFailed=false;private disposed=false;
  private version=0;private lastPercent=-1;private lastNetwork='';private armTime=0;
  private ready=false;private loadingVehicle=false;private activationFailed=false;
  private recaptureSeat=false;
  private position=new Vector3();private eye=new Vector3();private forward=new Vector3();
  private seat=new Vector3();private headOffset=new Vector3();private rotation=new Quaternion();
  private inverse=new Quaternion();private axis=new Vector3(0,1,0);private seatYaw=-Math.PI/2;
  private vehicle?:Object3D;private hud?:UIKitMLAsset;
  private mixer?:AnimationMixer;private idle?:AnimationAction;private walk?:AnimationAction;
  private wheels:{object:Object3D;radius:number}[]=[];
  private suspended:{system:Pausable;wasPaused:boolean}[]=[];
  private phaseListeners=new Set<()=>void>();

  getPhase():JourneyPhase{return this.phase;}
  subscribePhase(listener:()=>void):()=>void{this.phaseListeners.add(listener);listener();return()=>{this.phaseListeners.delete(listener);};}

  init():void {
    this.multiplayer=this.world.getSystem(MultiplayerSystem)!;
    this.playerEntity.addComponent(CoachJourney);
    this.cleanupFuncs.push(this.multiplayer.setJourneyHandlers({depart:()=>this.depart(),return:()=>this.returnToArrival()}));
    this.cleanupFuncs.push(this.multiplayer.subscribeIdentity(()=>{
      this.playerEntity.setValue(CoachJourney,'identityReady',this.multiplayer.isIdentityReady());this.syncScene();
    }));
    this.cleanupFuncs.push(this.world.activeLevel.subscribe(()=>{
      this.loaded=!!this.world.getSceneObject('complete-estate');
      this.playerEntity.setValue(CoachJourney,'domainLoaded',this.loaded);this.syncScene();
    }));
    const bind=(object?:Object3D)=>{
      if(!object)return;
      const click=()=>{
        object.getWorldPosition(this.position);(this.xrManager.isPresenting?this.player.head:this.camera).getWorldPosition(this.eye);
        if(this.eye.distanceToSquared(this.position)>12)return;
        if(this.phase==='arrival')this.depart();else if(this.phase==='visiting')this.returnToArrival();
      };
      object.addEventListener('click',click);this.cleanupFuncs.push(()=>object.removeEventListener('click',click));
    };
    this.cleanupFuncs.push(this.queries.portals.subscribe('qualify',e=>{bind(e.object3D);this.syncScene();}));
    for(const e of this.queries.portals.entities)bind(e.object3D);
    // InputSystem samples the new XR pose before our next update.
    const recenter=()=>{this.recaptureSeat=this.isSeated();};
    this.xrManager.addEventListener('sessionstart',recenter);this.xrManager.addEventListener('sessionend',recenter);
    this.cleanupFuncs.push(()=>{
      this.disposed=true;this.version++;this.restoreLocomotion();this.mixer?.stopAllAction();
      if(this.vehicle)this.mixer?.uncacheRoot(this.vehicle);
      for(const e of this.queries.vehicles.entities)e.dispose();
      this.phaseListeners.clear();this.xrManager.removeEventListener('sessionstart',recenter);this.xrManager.removeEventListener('sessionend',recenter);
    });
    void this.createVehicle();
  }

  private async createVehicle():Promise<void>{
    if(this.loadingVehicle)return;this.loadingVehicle=true;
    try {
      await AssetManager.loadGLTFById('royalCoachAnimated');
      if(this.disposed)return;
      const gltf=AssetManager.getGLTF('royalCoachAnimated');if(!gltf)throw Error('Carrosse indisponible');
      const root=new Group();root.name='Votre carrosse local';root.add(gltf.scene);
      const entity=this.world.createTransformEntity(root,{persistent:true}).addComponent(CoachVehicle);
      this.vehicle=root;this.mixer=new AnimationMixer(root);
      const idle=gltf.animations.find(c=>c.name==='HorseIdle'),walk=gltf.animations.find(c=>c.name==='HorseWalk');
      if(!idle||!walk)throw Error('Animations des chevaux indisponibles');
      this.idle=this.mixer.clipAction(idle).play();this.walk=this.mixer.clipAction(walk).play();this.walk.setEffectiveWeight(0);
      for(const name of ['WheelFrontL','WheelFrontR','WheelRearL','WheelRearR']){
        const object=root.getObjectByName(name);if(object)this.wheels.push({object,radius:name.includes('Front')?.59:.76});
      }
      const yaw=this.route.sample(0,this.position);root.position.copy(this.position);root.rotation.y=yaw;
      const hud=await this.world.assets.instantiate<UIKitMLAsset>('coach-panel');
      if(this.disposed){hud.dispose();return;}
      hud.position.set(.28,1.79,0);hud.rotation.y=-Math.PI/2;hud.scale.setScalar(.6);hud.visible=false;
      this.world.createTransformEntity(hud,{persistent:true,parent:entity}).addComponent(RayInteractable);
      this.hud=hud;
      const retry=()=>this.retryArrival(),back=()=>this.returnToArrival();
      hud.requireElementById('coach-retry').addEventListener('click',retry);
      hud.requireElementById('coach-return').addEventListener('click',back);
      this.cleanupFuncs.push(()=>{hud.requireElementById('coach-retry').removeEventListener('click',retry);hud.requireElementById('coach-return').removeEventListener('click',back);});
      this.ready=true;this.syncScene();
    }catch(error){console.error('[Plaisance] Carrosse',error);this.playerEntity.setValue(CoachJourney,'error','Le carrosse ne se charge pas. Rechargez la page pour reessayer.');}
    finally{this.loadingVehicle=false;}
  }

  private setPhase(phase:JourneyPhase):void {
    this.phase=phase;this.playerEntity.setValue(CoachJourney,'phase',phase);
    this.playerEntity.setValue(CoachJourney,'traveling',phase!=='arrival'&&phase!=='visiting');
    this.playerEntity.setValue(CoachJourney,'effectsEnabled',phase==='visiting');
    this.world.getSystem(ComfortMenuSystem)?.closeMenu();this.armTime=0;
    this.lastPercent=-1;this.lastNetwork='';this.syncScene();
    for(const listener of this.phaseListeners)listener();
  }

  private syncScene():void {
    const oldCoach=this.world.getSceneObject('arrival-coach');if(oldCoach)oldCoach.visible=!this.ready;
    for(const e of this.queries.portals.entities){
      if(!e.object3D)continue;
      const active=e.getValue(CoachPortal,'destination')==='castle'
        ? this.phase==='arrival'&&this.multiplayer?.isIdentityReady()&&this.ready : this.phase==='visiting';
      e.object3D.visible=!!active;
      if(active&&!e.hasComponent(RayInteractable))e.addComponent(RayInteractable);
      else if(!active&&e.hasComponent(RayInteractable))e.removeComponent(RayInteractable);
    }
    const arrival=this.world.getSceneObject<UIKitMLAsset>('arrival-panel');
    arrival?.requireElementById('arrival-root').setProperties({display:this.phase==='arrival'?'flex':'none'});
    const estate=this.world.getSceneObject<UIKitMLAsset>('estate-panel');
    estate?.requireElementById('estate-root').setProperties({display:this.phase==='visiting'&&!document.body.classList.contains('mobile-visit')?'flex':'none'});
    if(this.hud)this.hud.visible=this.isSeated()||this.phase==='activating';
    document.body.classList.toggle('coach-travel',this.phase!=='arrival'&&this.phase!=='visiting');
    if(this.hud){
      this.hud.requireElementById('coach-title').setProperties({text:this.phase==='returning'?'Retour vers l accueil':'En route vers le chateau'});
      this.hud.requireElementById('coach-actions').setProperties({display:this.phase==='waiting'?'flex':'none'});
    }
  }

  private isSeated():boolean{return this.phase==='outbound'||this.phase==='returning'||this.phase==='waiting';}
  private suspendLocomotion():void {
    if(this.suspended.length)return;
    for(const system of [this.world.getSystem(LocomotionSystem),this.world.getSystem(SlideSystem),this.world.getSystem(TurnSystem),this.world.getSystem(TeleportSystem)]){
      if(system){this.suspended.push({system,wasPaused:system.isPaused});system.stop();}
    }
  }
  private restoreLocomotion():void {
    for(const entry of this.suspended)if(!entry.wasPaused)entry.system.play();this.suspended.length=0;
  }
  private captureSeat():void {
    const viewer=this.xrManager.isPresenting?this.player.head:this.camera;
    viewer.getWorldPosition(this.eye);this.player.getWorldPosition(this.position);
    this.inverse.copy(this.player.quaternion).invert();this.headOffset.subVectors(this.eye,this.position).applyQuaternion(this.inverse);
    viewer.getWorldQuaternion(this.rotation);this.rotation.premultiply(this.inverse);
    this.forward.set(0,0,-1).applyQuaternion(this.rotation);
    const localYaw=Math.atan2(-this.forward.x,-this.forward.z);
    this.seatYaw=-Math.PI/2-localYaw;
  }
  private moveSeat():void {
    if(!this.vehicle)return;
    this.rotation.setFromAxisAngle(this.axis,this.vehicle.rotation.y+this.seatYaw);
    this.seat.fromArray(COACH_SEAT).applyQuaternion(this.vehicle.quaternion).add(this.vehicle.position);
    this.position.copy(this.headOffset).applyQuaternion(this.rotation);
    this.player.quaternion.copy(this.rotation);this.player.position.copy(this.seat).sub(this.position);this.player.updateMatrixWorld(true);
  }
  private drop(position:readonly number[],yaw:number):void {
    const viewer=this.xrManager.isPresenting?this.player.head:this.camera;
    viewer.getWorldPosition(this.eye);this.player.getWorldPosition(this.position);
    this.inverse.copy(this.player.quaternion).invert();this.headOffset.subVectors(this.eye,this.position).applyQuaternion(this.inverse);
    viewer.getWorldQuaternion(this.rotation);this.rotation.premultiply(this.inverse);this.forward.set(0,0,-1).applyQuaternion(this.rotation);
    const localYaw=Math.atan2(-this.forward.x,-this.forward.z);
    this.player.quaternion.setFromAxisAngle(this.axis,yaw-localYaw);
    this.headOffset.applyQuaternion(this.player.quaternion);
    this.position.fromArray(position);this.position.x-=this.headOffset.x;this.position.z-=this.headOffset.z;
    this.world.getSystem(LocomotionSystem)?.setPlayerPosition(this.position);this.player.updateMatrixWorld(true);
  }

  depart():void {
    if(this.phase!=='arrival'||!this.ready||!this.multiplayer.prepareJourney())return;
    this.version++;this.distance=0;this.speed=0;this.halfway=false;this.activationFailed=false;this.route=this.routes.outbound;
    this.playerEntity.setValue(CoachJourney,'progress',0);this.playerEntity.setValue(CoachJourney,'distance',0);
    this.playerEntity.setValue(CoachJourney,'error','');this.playerEntity.setValue(CoachJourney,'connectedHalfway',false);
    if(this.vehicle){this.vehicle.rotation.y=this.route.sample(0,this.position);this.vehicle.position.copy(this.position);}
    this.captureSeat();this.suspendLocomotion();this.setPhase('outbound');this.moveSeat();void this.loadDomain();
  }
  private async loadDomain():Promise<void> {
    if(this.loaded||this.loading)return;this.loading=true;this.loadFailed=false;
    try {
      await this.world.loadLevel(`${import.meta.env.BASE_URL}scenes/visit.iwsdk.scene.json`);
      if(this.disposed)return;this.loaded=true;this.playerEntity.setValue(CoachJourney,'domainLoaded',true);this.syncScene();
    }catch(error){this.loadFailed=true;console.error('[Plaisance] Chargement du domaine',error);}
    finally{this.loading=false;this.lastPercent=-1;}
  }

  private async finishOutbound():Promise<void> {
    if(this.phase!=='waiting'||!this.loaded||!this.multiplayer.isConnected())return;
    const generation=this.version;this.setPhase('activating');
    // Put the authoritative pose at the gate BEFORE the server can acknowledge it.
    this.drop(CASTLE_DROP,0);
    const active=await this.multiplayer.activatePresence();
    if(this.disposed||generation!==this.version)return;
    if(active){this.setPhase('visiting');this.restoreLocomotion();}
    else{this.activationFailed=true;this.setPhase('waiting');this.captureSeat();this.moveSeat();}
  }
  private retryArrival():void {
    if(this.phase!=='waiting')return;
    this.activationFailed=false;
    if(!this.loaded&&!this.loading)void this.loadDomain();
    this.multiplayer.connectObserver();void this.finishOutbound();
  }
  returnToArrival():void {
    if(this.phase!=='visiting'&&this.phase!=='waiting'&&this.phase!=='activating')return;
    this.version++;this.multiplayer.hidePresence();
    this.route=this.routes.inbound;this.distance=0;this.speed=0;this.halfway=false;
    this.playerEntity.setValue(CoachJourney,'progress',0);this.playerEntity.setValue(CoachJourney,'distance',0);
    this.playerEntity.setValue(CoachJourney,'connectedHalfway',false);
    this.captureSeat();this.suspendLocomotion();this.setPhase('returning');this.moveSeat();
  }
  private finishReturn():void {
    this.speed=0;this.multiplayer.finishJourney();this.drop(ARRIVAL_DROP,Math.PI/2);
    this.setPhase('arrival');this.restoreLocomotion();
    // Reposition locally while the passenger faces the arrival circle.
    this.route=this.routes.outbound;this.distance=0;
    this.playerEntity.setValue(CoachJourney,'progress',0);this.playerEntity.setValue(CoachJourney,'distance',0);
    if(this.vehicle){this.vehicle.rotation.y=this.route.sample(0,this.position);this.vehicle.position.copy(this.position);}
  }

  update(delta:number):void {
    if(this.disposed)return;
    const active=this.visibilityState.peek()!==VisibilityState.VisibleBlurred&&!document.hidden;
    const dt=active?Math.min(delta,.05):0;
    this.armTime+=dt;
    if(this.phase==='outbound'||this.phase==='returning'){
      const remaining=this.route.length-this.distance;
      const target=Math.min(CRUISE_SPEED,Math.sqrt(Math.max(0,2*.45*remaining)));
      this.speed=Math.min(target,this.speed+.45*dt);
      const step=Math.min(remaining,this.speed*dt);this.distance+=step;this.wheelsDistance+=step;
      if(this.vehicle){this.vehicle.rotation.y=this.route.sample(this.distance,this.position);this.vehicle.position.copy(this.position);}
      const progress=this.distance/this.route.length;
      this.playerEntity.setValue(CoachJourney,'progress',progress);this.playerEntity.setValue(CoachJourney,'distance',this.distance);
      if(!this.halfway&&progress>=.5){
        this.halfway=true;this.playerEntity.setValue(CoachJourney,'connectedHalfway',true);
        if(this.phase==='outbound')this.multiplayer.connectObserver();else this.multiplayer.disconnectJourney();
      }
      if(remaining<.015){this.speed=0;if(this.phase==='outbound'){this.setPhase('waiting');void this.finishOutbound();}else this.finishReturn();}
    }
    if(this.recaptureSeat){this.recaptureSeat=false;if(this.isSeated())this.captureSeat();}
    if(this.isSeated())this.moveSeat();
    if(this.phase==='waiting'&&!this.activationFailed&&this.loaded&&this.multiplayer.isConnected())void this.finishOutbound();
    this.playerEntity.setValue(CoachJourney,'speed',this.speed);
    const moving=this.speed>.01?Math.min(1,this.speed/.35):0;
    this.idle?.setEffectiveWeight(1-moving);this.walk?.setEffectiveWeight(moving);this.walk?.setEffectiveTimeScale(Math.max(.05,this.speed/WALK_SPEED));
    this.mixer?.update(dt);
    for(const wheel of this.wheels)wheel.object.rotation.z=-this.wheelsDistance/wheel.radius;
    const percent=Math.round(this.distance/this.route.length*100),network=this.multiplayer.getConnectionStatus();
    if(this.hud&&(percent!==this.lastPercent||network!==this.lastNetwork)){
      this.lastPercent=percent;this.lastNetwork=network;
      this.hud.requireElementById('coach-progress').setProperties({text:`Trajet : ${percent} %`});
      const status=this.phase==='waiting'?(this.activationFailed?'Arrivee non confirmee. Reessayez ou revenez a l accueil.':this.loadFailed?'Le domaine ne se charge pas. Reessayez ou revenez a l accueil.':!this.loaded?'Preparation du domaine...':this.multiplayer.isConnected()?'Arrivee au domaine...':'Connexion indisponible. Reessayez ou revenez a l accueil.'):
        this.phase==='returning'?'Retour au cercle d accueil.':this.halfway?'Vous pouvez apercevoir les visiteurs du domaine.':'Installez-vous. Vous pouvez regarder autour de vous.';
      this.hud.requireElementById('coach-status').setProperties({text:status});
    }
    if(this.armTime<1||!this.ready)return;
    (this.xrManager.isPresenting?this.player.head:this.camera).getWorldPosition(this.eye);
    if(this.phase==='arrival'&&this.multiplayer.isIdentityReady()&&this.eye.x>6.3&&this.eye.x<8.2&&Math.abs(this.eye.z)<.95&&this.eye.y<3.4)this.depart();
    else if(this.phase==='visiting'&&Math.abs(this.eye.x-100)<2.3&&this.eye.z>-67&&this.eye.z<-63&&this.eye.y<3.4)this.returnToArrival();
  }
}
