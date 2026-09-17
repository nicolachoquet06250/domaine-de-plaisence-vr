import WebSocket from 'ws';
const room=process.argv[2];const ws=new WebSocket('wss://localhost:8081/rooms?room='+room,{rejectUnauthorized:false});let timer;let received=false;
ws.on('open',()=>{timer=setInterval(()=>ws.send(JSON.stringify({type:'pose',head:{p:[2,1.65,17],q:[0,1,0,0]},left:{p:[1.65,1.2,17],q:[0,0,0,1]},right:{p:[2.35,1.2,17],q:[0,0,0,1]}})),100);});
ws.on('message',raw=>{const p=JSON.parse(raw);if(p.type==='welcome')console.log(JSON.stringify({welcome:p.id,peers:p.peers.length}));if(p.type==='pose'&&!received){received=true;console.log(JSON.stringify({receivedBrowserPose:p.head}));}});
ws.on('error',e=>{console.error(e.message);process.exitCode=1;});ws.on('close',()=>{clearInterval(timer);console.log('peer closed');});setTimeout(()=>{clearInterval(timer);ws.close();},90000);
