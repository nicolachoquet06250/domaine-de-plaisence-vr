/** Opt-in local runtime verification; remove its index import after review. */
import { Group, LocomotionSystem, Vector3, type World } from '@iwsdk/core';
import { MultiplayerSystem } from '../src/multiplayer.js';
import { RoomConnection, RemoteVisitor } from '../src/multiplayer-components.js';
const delay=(ms:number)=>new Promise<void>(resolve=>setTimeout(resolve,ms));
export async function verifyMirrorVoice(world:World):Promise<void> {
  const diagnostic=world.createTransformEntity(new Group(),{persistent:true}).addComponent(RoomConnection);
  diagnostic.object3D!.name='Verification miroir et voix';
  const system=world.getSystem(MultiplayerSystem)!;
  const fixture=system as unknown as {avatarGender:'male'|'female'|null;setNickname:(s:string,remember:boolean)=>void;loadLocalBody:()=>void};
  fixture.avatarGender='female';fixture.setNickname('Essai miroir',false);fixture.loadLocalBody();
  system.enterLobby();
  for(let i=0;i<300&&!system.isInLobby();i++)await delay(100);
  if(!system.isInLobby())throw Error('Test room did not open');
  await delay(1500);
  world.getSystem(LocomotionSystem)!.setPlayerPosition(new Vector3(-7,5.04,-31.25));
  world.camera.position.set(0,1.7,0);world.camera.rotation.set(0,0,0);
  const sockets:WebSocket[]=[];
  const room=new URL(location.href).searchParams.get('roomId')!;
  let frame=0;
  for(let i=0;i<2;i++) {
    const url=new URL('/rooms',location.href);url.protocol='wss:';
    url.searchParams.set('room',room);url.searchParams.set('nickname',i?'Aigus — essai':'Graves — essai');url.searchParams.set('avatar',i?'female':'male');
    const socket=new WebSocket(url);sockets.push(socket);
  }
  const timer=setInterval(()=>{
    frame++;
    for(let i=0;i<2;i++)if(sockets[i].readyState===WebSocket.OPEN) {
      const active=frame%120<80;
      const voice=active?(i?[.1,.4,.9]:[.9,.4,.1]):[0,0,0];
      sockets[i].send(JSON.stringify({type:'pose',head:{p:[-7+(i?.6:-.6),6.7,-32.35],q:[0,0,0,1]},feet:{p:[-7+(i?.6:-.6),5.04,-32.35],q:[0,0,0,1]},left:null,right:null,voice}));
    }
    const visitors=system.queries.visitors.entities;
    let count=0;for(const e of visitors)if(e.getVectorView(RemoteVisitor,'voiceBands').some(v=>v>.2))count++;
    diagnostic.setValue(RoomConnection,'voicePeers',count);
    diagnostic.setValue(RoomConnection,'status',frame%120<80?'two-speaking':'silence');
    diagnostic.setValue(RoomConnection,'voiceError',JSON.stringify({frame,receivedActiveSpeakers:count}));
  },100);
  setTimeout(()=>{clearInterval(timer);sockets.forEach(s=>s.close());diagnostic.setValue(RoomConnection,'status','ended');},600000);
}
