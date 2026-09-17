// Lightweight collision proxy; visible fountain and water are Blender GLBs.
import { CylinderGeometry, Group, Mesh, MeshStandardMaterial, TorusGeometry } from '@iwsdk/core';
const limestone=new MeshStandardMaterial({color:'#e1d4b8',roughness:.8});
const bronze=new MeshStandardMaterial({color:'#937844',metalness:.6,roughness:.38});
export const basin=new Group(); basin.name='Bassin de la fontaine';
function ring(radius:number,tube:number,y:number) { const m=new Mesh(new TorusGeometry(radius,tube,10,96),limestone);m.rotation.x=-Math.PI/2;m.position.y=y;basin.add(m); }
ring(4.05,.27,.34);ring(4.05,.19,.66);ring(4.05,.32,.08);
const bottom=new Mesh(new CylinderGeometry(3.98,4.16,.16,96),limestone); bottom.position.y=.08;basin.add(bottom);
const pedestal=new Mesh(new CylinderGeometry(.38,.68,.72,24),limestone);pedestal.position.y=.49;basin.add(pedestal);
const crown=new Mesh(new CylinderGeometry(.52,.34,.16,24),bronze);crown.position.y=.9;basin.add(crown);
for(let i=0;i<6;i++){const a=i*Math.PI/3;const n=new Mesh(new CylinderGeometry(.12,.18,.25,12),bronze);n.position.set(3.1*Math.cos(a),.48,3.1*Math.sin(a));basin.add(n);}
