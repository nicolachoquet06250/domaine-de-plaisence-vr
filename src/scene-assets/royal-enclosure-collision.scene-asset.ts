import { BoxGeometry, Group, Mesh, MeshBasicMaterial } from '@iwsdk/core';
import { createStaticCollision } from './static-collision.js';

// Match the Blender perimeter and open leaves with inexpensive solid envelopes.
const source=new Group(),geometry=new BoxGeometry(1,1,1),material=new MeshBasicMaterial();
function box(x:number,y:number,z:number,w:number,h:number,d:number,yaw=0) {
 const mesh=new Mesh(geometry,material);mesh.position.set(x,y,z);mesh.scale.set(w,h,d);mesh.rotation.y=yaw;source.add(mesh);
}
box(0,2,-40,60.6,4,.6);
box(-30,2,-5,.6,4,70.6);box(30,2,-5,.6,4,70.6);
for(const side of [-1,1]){
 box(side*18.34,2,30,23.92,4,.6);
 box(side*6,2.95,30,1.75,5.9,1.65);
 const angle=78*Math.PI/180,half=2.6;
 box(side*(5.3-half*Math.cos(angle)),2.7,30-half*Math.sin(angle),5.2,4.8,.18,side===-1?angle:Math.PI-angle);
}
// Close the entire opening behind the return portal (local z=29.5).
// The trigger stays reachable from the garden before reaching this invisible wall.
box(0,4.26,30,10.8,8.52,.3);
source.name='Enceinte royale et vantaux ouverts';
export default createStaticCollision(source);
