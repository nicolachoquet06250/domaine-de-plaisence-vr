// Manual runtime fixture: node tests/nickname-peer.mjs <32-hex-room-id>
// Two synthetic visitors, no microphone or voice transport. Closes after 2 min.
import {WebSocket} from 'ws';
const room=process.argv[2];
if(!/^[a-f0-9]{32}$/.test(room??''))throw Error('Expected a test room id');
const clients=['Élodie du Jardin','Alexandre du Grand Jardin'].map((nickname,index)=>{
  const url=new URL('wss://localhost:8081/rooms');url.searchParams.set('room',room);url.searchParams.set('nickname',nickname);
  // The development server uses its local self-signed certificate.
  const socket=new WebSocket(url,{rejectUnauthorized:false});
  const timer=setInterval(()=>{if(socket.readyState===WebSocket.OPEN)socket.send(JSON.stringify({type:'pose',head:{p:[index?1.15:-1.15,1.7,index?19:20],q:[0,1,0,0]},left:null,right:null}));},100);
  socket.on('message',data=>{const m=JSON.parse(data);if(m.type==='welcome')console.log(JSON.stringify({id:m.id,nickname:m.nickname}));});
  socket.on('error',error=>console.error(error.message));socket.on('close',()=>clearInterval(timer));
  return socket;
});
setTimeout(()=>{for(const socket of clients)socket.close();},120000);
