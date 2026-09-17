import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
import * as core from '@iwsdk/core';

const compile=p=>ts.transpileModule(fs.readFileSync(p,'utf8').replaceAll('import.meta.env.BASE_URL',"'/'"),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const routes={};vm.runInNewContext(compile('src/coach-route.ts'),{exports:routes,require:()=>core});
const components={CoachJourney:{},CoachVehicle:{},CoachPortal:{}};
const api={},document={hidden:false,body:{classList:{toggle(){},contains(){return false;}}}};
vm.runInNewContext(compile('src/coach-journey.ts'),{exports:api,document,console,require:id=>id==='@iwsdk/core'?{...core,createSystem:()=>class{}}:id.includes('route')?routes:id.includes('components')?components:{}});

function fixture(){
 const system=new api.CoachJourneySystem(),player=new core.Group(),head=new core.Group();player.add(head);player.head=head;
 head.position.set(.25,1.85,-.15);head.rotation.y=.3;
 const values={},events=[],vehicle=new core.Group();
 const locomotors=new Map([core.LocomotionSystem,core.SlideSystem,core.TurnSystem,core.TeleportSystem].map(k=>[k,{isPaused:false,stop(){this.isPaused=true;},play(){this.isPaused=false;},setPlayerPosition(p){player.position.copy(p);}}]));
 let connected=false,ack=true,resolve;
 const multiplayer={isIdentityReady:()=>true,prepareJourney:()=>{events.push('prepare');return true;},connectObserver(){events.push('observer');connected=true;},isConnected:()=>connected,
  activatePresence(){events.push('activate');events.push(head.getWorldPosition(new core.Vector3()).toArray());return ack?Promise.resolve(true):new Promise(r=>resolve=r);},
  hidePresence(){events.push('hide');},disconnectJourney(){events.push('disconnect');connected=false;},finishJourney(){events.push('finish');connected=false;},getConnectionStatus:()=>connected?'observing':'solo'};
 Object.assign(system,{player,camera:head,xrManager:{isPresenting:true},playerEntity:{setValue:(_,k,v)=>values[k]=v},world:{getSceneObject:()=>undefined,getSystem:k=>locomotors.get(k)},queries:{portals:{entities:[]}},visibilityState:{peek:()=>core.VisibilityState.Visible},multiplayer,vehicle,loaded:true,ready:true});
 return {system,player,head,values,events,locomotors,defer:()=>ack=false,ack:ok=>resolve(ok)};
}
function advanceUntil(f,predicate){for(let i=0;i<5000&&!predicate();i++)f.system.update(.05);assert.ok(predicate(),'milestone reached within bounded time');}

test('real route has continuous yaw, aligned parking and a broad turn without jumping',()=>{
 const {outbound,inbound}=routes.createCoachRoutes(),p=new core.Vector3(),q=new core.Vector3();
 assert.ok(outbound.length>110&&outbound.length<130);assert.ok(inbound.length>outbound.length+10);
 outbound.point(outbound.length,p);inbound.point(0,q);assert.ok(p.distanceTo(q)<1e-6);
 assert.ok(Math.abs(outbound.sample(outbound.length,p)-Math.PI/2)<.03);
 assert.ok(Math.abs(inbound.sample(0,p)-Math.PI/2)<.1);
 inbound.point(inbound.length,p);outbound.point(0,q);assert.ok(p.distanceTo(q)<1e-6);
 for(const route of [outbound,inbound]){
  let previous=route.sample(0,p);
  for(let d=.02;d<=route.length;d+=.02){const yaw=route.sample(d,p),angle=Math.abs(Math.atan2(Math.sin(yaw-previous),Math.cos(yaw-previous)));assert.ok(angle<.06,`smooth yaw at ${d}: ${angle}`);previous=yaw;}
 }
 let maxX=0,minZ=0;for(let d=0;d<14;d+=.1){inbound.point(d,p);maxX=Math.max(maxX,p.x);minZ=Math.min(minZ,p.z);}
 assert.ok(maxX>108.5&&minZ<-61.9,'turn spans a nine metre diameter');
});

test('outbound connects only halfway, seats tracked head, locks motion and activates only after gate pose and acknowledgement',async()=>{
 const f=fixture();f.defer();f.system.depart();
 assert.deepEqual(f.events,['prepare']);assert.equal(f.values.effectsEnabled,false);
 assert.ok([...f.locomotors.values()].every(s=>s.isPaused));
 const target=new core.Vector3().fromArray(routes.COACH_SEAT).applyQuaternion(f.system.vehicle.quaternion).add(f.system.vehicle.position);
 assert.ok(f.head.getWorldPosition(new core.Vector3()).distanceTo(target)<1e-6,'head height and room-scale offset place eyes at the seat');
 f.head.position.x+=.1;f.system.update(.05);
 assert.ok(Math.abs(f.head.getWorldPosition(new core.Vector3()).distanceTo(target)-.1)<.003,'physical leaning remains possible');
 advanceUntil(f,()=>f.values.progress>=.499);assert.equal(f.events.includes('observer'),false);
 advanceUntil(f,()=>f.values.progress>=.501);assert.equal(f.events.filter(e=>e==='observer').length,1);
 advanceUntil(f,()=>f.system.getPhase()==='activating');
 assert.equal(f.values.effectsEnabled,false);assert.ok([...f.locomotors.values()].every(s=>s.isPaused));
 const position=f.events.at(-1);assert.ok(Math.abs(position[0]-100)<1e-6&&Math.abs(position[2]+70)<1e-6,'first published pose is in front of the gate');
 f.ack(true);await new Promise(setImmediate);assert.equal(f.system.getPhase(),'visiting');assert.equal(f.values.effectsEnabled,true);
 assert.ok([...f.locomotors.values()].every(s=>!s.isPaused));
});

test('return hides immediately, disables effects, disconnects halfway and restores arrival inside the collider',async()=>{
 const f=fixture();f.system.depart();advanceUntil(f,()=>f.system.getPhase()==='activating');await new Promise(setImmediate);
 f.system.returnToArrival();assert.equal(f.events.at(-1),'hide');assert.equal(f.values.effectsEnabled,false);
 assert.equal(f.system.getPhase(),'returning');assert.ok([...f.locomotors.values()].every(s=>s.isPaused));
 advanceUntil(f,()=>f.values.progress>=.499);assert.equal(f.events.includes('disconnect'),false);
 advanceUntil(f,()=>f.values.progress>=.501);assert.equal(f.events.filter(e=>e==='disconnect').length,1);
 advanceUntil(f,()=>f.system.getPhase()==='arrival');
 assert.equal(f.events.at(-1),'finish');assert.ok([...f.locomotors.values()].every(s=>!s.isPaused));
 const position=f.head.getWorldPosition(new core.Vector3());assert.ok(Math.abs(position.x-5.4)<1e-6&&Math.abs(position.z)<1e-6);
});

test('blur pauses movement and a late activation acknowledgement cannot expose a returning passenger',async()=>{
 const f=fixture();f.defer();f.system.depart();const distance=f.system.distance;
 document.hidden=true;f.system.update(2);document.hidden=false;assert.equal(f.system.distance,distance);
 advanceUntil(f,()=>f.system.getPhase()==='activating');f.system.returnToArrival();f.ack(true);await new Promise(setImmediate);
 assert.equal(f.system.getPhase(),'returning');assert.equal(f.values.effectsEnabled,false);
});

test('failed activation stays seated until explicit retry and preserves already-paused locomotion',async()=>{
 const f=fixture();f.defer();f.locomotors.get(core.TeleportSystem).isPaused=true;f.system.depart();
 advanceUntil(f,()=>f.system.getPhase()==='activating');f.ack(false);await new Promise(setImmediate);
 assert.equal(f.system.getPhase(),'waiting');for(let i=0;i<100;i++)f.system.update(.05);
 assert.equal(f.events.filter(e=>e==='activate').length,1);
 f.system.retryArrival();f.ack(true);await new Promise(setImmediate);assert.equal(f.system.getPhase(),'visiting');
 assert.equal(f.locomotors.get(core.TeleportSystem).isPaused,true);assert.equal(f.locomotors.get(core.SlideSystem).isPaused,false);
});

test('turning court contains only its 96 triangles, without unrelated Blender scenes',()=>{
 const bytes=fs.readFileSync('public/gltf/arrival-coach/turningCourt.glb');const gltf=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)));
 assert.equal(gltf.scenes.length,1);assert.equal(gltf.meshes.length,1);
 assert.equal(gltf.accessors[gltf.meshes[0].primitives[0].indices].count,288);assert.ok(bytes.length<200000);
});

test('switching XR mode recentres from the newly sampled head pose, without locking subsequent lean',()=>{
 const f=fixture();f.system.depart();f.head.position.set(.6,1.2,.4);f.head.rotation.y=-.7;f.system.recaptureSeat=true;
 f.system.update(.05);
 const target=new core.Vector3().fromArray(routes.COACH_SEAT).applyQuaternion(f.system.vehicle.quaternion).add(f.system.vehicle.position);
 assert.ok(f.head.getWorldPosition(new core.Vector3()).distanceTo(target)<1e-6);
 assert.equal(f.system.recaptureSeat,false);
 f.head.position.y+=.2;f.system.update(0);assert.ok(Math.abs(f.head.getWorldPosition(new core.Vector3()).y-target.y-.2)<1e-6);
});

test('merged domain retains the complete castle layout and closed arrival collider without distant duplicates',()=>{
 const scene=JSON.parse(fs.readFileSync('public/scenes/visit.iwsdk.scene.json'));
 const palace=JSON.parse(fs.readFileSync('public/scenes/plaisance.iwsdk.scene.json'));
 const root=scene.nodes.find(n=>n.id==='complete-estate');assert.deepEqual(root.transform.position,[100,0,-95]);
 const expected=palace.nodes.filter(n=>n.id!=='sun');
 const normalize=nodes=>nodes.map(n=>{const copy=structuredClone(n);if(copy.content?.asset==='coachEstateLawn')copy.content.asset='ground';if(copy.children)copy.children=normalize(copy.children);return copy;});
 assert.deepEqual(normalize(root.children),expected);
 assert.ok(!scene.nodes.some(n=>['landscape-estate','landscape-gateway','landscape-royal-fence','landscape-fountain'].includes(n.id)));
 assert.ok(scene.nodes.some(n=>n.content?.asset==='arrivalBoundary'));
});

