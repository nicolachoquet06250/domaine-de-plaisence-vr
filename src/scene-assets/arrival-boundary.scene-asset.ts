import { BoxGeometry, Group, Mesh, MeshBasicMaterial } from '@iwsdk/core';
import { createStaticCollision } from './static-collision.js';

// Overlapping segments close all seams; the wall also extends beneath the slab.
const source=new Group(),box=new BoxGeometry(1,1,1),material=new MeshBasicMaterial();
for(let i=0;i<96;i++) {
  const angle=i*Math.PI*2/96,mesh=new Mesh(box,material);
  mesh.position.set(Math.sin(angle)*7.91,1.8,Math.cos(angle)*7.91);
  mesh.rotation.y=angle;mesh.scale.set(.55,4.4,.3);source.add(mesh);
}
source.name='Limite fermee de la place';
export default createStaticCollision(source);
