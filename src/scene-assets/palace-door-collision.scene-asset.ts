import { BoxGeometry, Group, Mesh, MeshBasicMaterial } from '@iwsdk/core';
const material=new MeshBasicMaterial(); material.visible=false;
const proxy=new Group(); proxy.name='Collision de porte fermee';
const panel=new Mesh(new BoxGeometry(3.2,3.5,.18),material); panel.position.y=1.75; proxy.add(panel);
export default proxy;
