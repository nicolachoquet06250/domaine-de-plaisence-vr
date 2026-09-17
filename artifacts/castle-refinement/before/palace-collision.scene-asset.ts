import { BufferGeometry, Float32BufferAttribute, Group, Mesh, MeshBasicMaterial } from '@iwsdk/core';
import solids from './castle-collision-data.json';

// Dimensions exported by Blender. Ornament never enters the collision BVH.
const vertices: number[] = [], indices: number[] = [];
function prism(points: number[][]) {
  const offset = vertices.length / 3;
  for (const point of points) vertices.push(...point);
  for (const face of [[0,3,2,1],[4,5,6,7],[0,1,5,4],[3,7,6,2],[0,4,7,3],[1,2,6,5]]) {
    indices.push(offset+face[0],offset+face[1],offset+face[2],offset+face[0],offset+face[2],offset+face[3]);
  }
}
for (const item of solids) {
  if (item.kind === 'box' && item.position && item.size) {
    const [x,y,z]=item.position, [w,h,d]=item.size;
    prism([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]]
      .map(([a,b,c])=>[x+a*w/2,y+b*h/2,z+c*d/2]));
  } else if (item.from && item.to && item.width) {
    const a=item.from[2]<item.to[2]?item.from:item.to;
    const b=item.from[2]<item.to[2]?item.to:item.from;
    const x=a[0], half=item.width/2, rail=item.kind==='rail', height=item.height??0;
    const lowA=rail?a[1]:Math.min(a[1],b[1])-.12, lowB=rail?b[1]:lowA;
    prism([[x-half,lowA,a[2]],[x+half,lowA,a[2]],[x+half,a[1]+height,a[2]],[x-half,a[1]+height,a[2]],
      [x-half,lowB,b[2]],[x+half,lowB,b[2]],[x+half,b[1]+height,b[2]],[x-half,b[1]+height,b[2]]]);
  }
}
const geometry=new BufferGeometry();
geometry.setAttribute('position',new Float32BufferAttribute(vertices,3)); geometry.setIndex(indices);
geometry.computeBoundingBox(); geometry.computeBoundingSphere();
const material=new MeshBasicMaterial(); material.visible=false;
const palaceCollision=new Group(); palaceCollision.name='Enveloppes du chateau et rampes des escaliers';
palaceCollision.add(new Mesh(geometry,material));
export default palaceCollision;
