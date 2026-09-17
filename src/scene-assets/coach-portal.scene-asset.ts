import { Group, Mesh, MeshStandardMaterial, MeshBasicMaterial, TorusGeometry, CylinderGeometry, CircleGeometry, DoubleSide } from '@iwsdk/core';

const portal=new Group();portal.name='Passage en carrosse';
const gold=new MeshStandardMaterial({color:0xdab765,metalness:.72,roughness:.32});
const glow=new MeshBasicMaterial({color:0x70c6ca,transparent:true,opacity:.21,depthWrite:false,side:DoubleSide});
const rim=new Mesh(new TorusGeometry(.86,.035,8,48),gold);rim.position.y=1.17;rim.scale.y=1.25;portal.add(rim);
const veil=new Mesh(new CircleGeometry(.825,48),glow);veil.position.copy(rim.position);veil.scale.y=rim.scale.y;portal.add(veil);
for(const x of [-.88,.88]){const foot=new Mesh(new CylinderGeometry(.13,.19,.10,12),gold);foot.position.set(x,.05,0);portal.add(foot);}
export default portal;
