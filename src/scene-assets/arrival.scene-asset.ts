import { Group, Mesh, MeshStandardMaterial, CylinderGeometry, BoxGeometry } from '@iwsdk/core';

const arrival = new Group();
arrival.name = 'Terrasse d accueil';
const stone = new MeshStandardMaterial({color:0xd9c9a5,roughness:.88});
const dark = new MeshStandardMaterial({color:0x284d42,roughness:.7});
const gold = new MeshStandardMaterial({color:0xb49759,roughness:.5,metalness:.25});
const slab = new Mesh(new CylinderGeometry(8,8,.3,64),stone); slab.position.y=-.15; arrival.add(slab);
function box(x:number,y:number,z:number,w:number,h:number,d:number,material=stone) {
  const mesh=new Mesh(new BoxGeometry(w,h,d),material);mesh.position.set(x,y,z);arrival.add(mesh);return mesh;
}
// A closed parapet keeps the visitor on the platform, including in VR.
for(let i=0;i<40;i++) {
  const a=i*Math.PI*2/40;
  box(Math.sin(a)*7.65,.5,Math.cos(a)*7.65,1.23,1,.22).rotation.y=a;
  box(Math.sin(a)*7.65,1.045,Math.cos(a)*7.65,1.25,.09,.32,gold).rotation.y=a;
}
for(const x of [-2.6,2.6]) {
  box(x,.12,-4,.85,.24,.85);
  box(x,1.85,-4,.44,3.46,.44);
  box(x,3.68,-4,.8,.2,.8,gold);
}
box(0,3.95,-4,6.1,.35,.8,dark);
box(0,4.16,-4,6.3,.07,.9,gold);
// Separate inset stones have no coplanar overlays.
for(const x of [-3.5,3.5])for(const z of [-2,0,2])box(x,.025,z,1,.05,1,dark);
export default arrival;
