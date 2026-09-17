import { CircleGeometry, DoubleSide, Group, Mesh, MeshBasicMaterial, Shape, ShapeGeometry } from '@iwsdk/core';

const indicator=new Group();indicator.name='Direction du portail';
const background=new Mesh(new CircleGeometry(.075,32),new MeshBasicMaterial({color:0x17372c,transparent:true,opacity:.9,depthTest:false,depthWrite:false,side:DoubleSide}));
background.renderOrder=10000;
const shape=new Shape();shape.moveTo(-.028,.037);shape.lineTo(.011,0);shape.lineTo(-.028,-.037);
shape.lineTo(-.014,-.052);shape.lineTo(.04,0);shape.lineTo(-.014,.052);shape.closePath();
const arrow=new Mesh(new ShapeGeometry(shape),new MeshBasicMaterial({color:0xf6d58b,transparent:true,depthTest:false,depthWrite:false,side:DoubleSide}));
arrow.renderOrder=10001;arrow.position.z=.001;
indicator.add(background,arrow);
export default indicator;
