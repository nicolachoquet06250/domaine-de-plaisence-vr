import { BoxGeometry, CylinderGeometry, ExtrudeGeometry, Group, InstancedMesh, Matrix4, Mesh, MeshStandardMaterial, Object3D, Shape, ShapeGeometry, SphereGeometry } from '@iwsdk/core';

// Architectural details share batches: hundreds of stone courses/window bars,
// a handful of draw calls. Origin is the centre of the palace at ground level.
const stone = new MeshStandardMaterial({ color: '#e6d9bb', roughness: .88 });
const trim = new MeshStandardMaterial({ color: '#f4ead4', roughness: .78 });
const slate = new MeshStandardMaterial({ color: '#344958', roughness: .66, metalness: .15 });
const glass = new MeshStandardMaterial({ color: '#284c58', roughness: .22, metalness: .42 });
const gold = new MeshStandardMaterial({ color: '#b6924b', roughness: .4, metalness: .65 });
const door = new MeshStandardMaterial({ color: '#453c32', roughness: .84 });
const palace = new Group(); palace.name = 'Chateau de Plaisance';
const unit = new BoxGeometry(1, 1, 1);
const batches = new Map<MeshStandardMaterial, Matrix4[]>();
const dummy = new Object3D();
function box(mat: MeshStandardMaterial, x:number,y:number,z:number,w:number,h:number,d:number, rz=0) {
  dummy.position.set(x,y,z); dummy.rotation.set(0,0,rz); dummy.scale.set(w,h,d); dummy.updateMatrix();
  if (!batches.has(mat)) batches.set(mat, []);
  batches.get(mat)!.push(dummy.matrix.clone());
}
function arch(w:number,h:number) {
  const s = new Shape(); const r=w/2;
  s.moveTo(-r,0); s.lineTo(r,0); s.lineTo(r,h-r); s.absarc(0,h-r,r,0,Math.PI,false); s.closePath(); return s;
}
// A real opening in the surround: no full stone polygon behind the glazing.
// The raised surround and inset glass have distinct depths even at close range.
const windowSurround = arch(1.66,2.9);
const windowOpening = arch(1.30,2.56);
const openingPoints = windowOpening.getPoints(24);
for (const point of openingPoints) point.y += .14;
windowSurround.holes.push(new Shape(openingPoints));
const windowOuter = new ExtrudeGeometry(windowSurround,{depth:.065,bevelEnabled:false,curveSegments:12});
const windowInner = new ShapeGeometry(arch(1.30,2.56),12);
function windowAt(x:number,y:number,z:number) {
  const a=new Mesh(windowOuter,trim); a.name='Encadrement ajoure'; a.position.set(x,y,z); palace.add(a);
  const b=new Mesh(windowInner,glass); b.name='Vitrage en retrait'; b.position.set(x,y+.14,z+.025); palace.add(b);
  box(trim,x,y+1.30,z+.10,.055,2.3,.07);
  box(trim,x,y+1.1,z+.10,1.30,.06,.07);
  box(trim,x,y+1.96,z+.10,1.30,.06,.07);
  box(trim,x,y-.08,z+.05,1.95,.19,.38);
  box(trim,x,y+2.96,z-.01,1.95,.17,.28);
}
function roof(x:number,z:number,w:number,d:number,y:number,h:number) {
  const m=new Mesh(new CylinderGeometry(.57,1,h,4,1).rotateY(Math.PI/4),slate);
  m.scale.set(w/Math.SQRT2,1,d/Math.SQRT2); m.position.set(x,y+h/2,z); palace.add(m);
  box(gold,x,y+h+.05,z,w*.57,.1,d*.57);
}
// Main corps de logis, forward side pavilions and central avant-corps.
box(stone,0,5.4,0,29,10.8,10);
for(const x of [-17,17]) {
  box(stone,x,6.15,.6,7,12.3,12);
  roof(x,.6,7.8,12.8,12.3,4.0);
  for(const y of [0.35,4.35,8.25,11.85]) box(trim,x,y,.6,7.45,.30,12.4);
  for(const dx of [-3.25,3.25]) for(let y=1;y<11.8;y+=.52) box(trim,x+dx,y,6.7,.6,.36,.24);
  for(const dx of [-1.7,1.7]) for(const y of [1.0,4.8,8.6]) windowAt(x+dx,y,6.68);
  box(stone,x,15.6,-1.8,.95,2.5,1.15); box(trim,x,16.95,-1.8,1.2,.22,1.4);
}
roof(0,0,29.8,10.7,10.8,3.25);
box(stone,0,6.2,1.25,8.4,12.4,11.6);
roof(0,1.25,9.1,12.4,12.4,4.0);
for(const y of [.35,4.4,8.2,10.7]) box(trim,0,y,0,29.6,.28,10.5);
for(const x of [-11.7,-8.5,-5.3,5.3,8.5,11.7]) for(const y of [1,4.85,8.0]) windowAt(x,y,5.08);
for(const x of [-2.7,0,2.7]) windowAt(x,8.55,7.13);
// Grand entry, engaged columns, projecting entablature, triangular pediment.
const doorway=arch(3.7,5.6);
const doorOpening=arch(3.18,5.20).getPoints(32);
for(const point of doorOpening) point.y+=.15;
doorway.holes.push(new Shape(doorOpening));
const entryFrame=new Mesh(new ExtrudeGeometry(doorway,{depth:.25,bevelEnabled:false,curveSegments:16}),trim); entryFrame.position.set(0,.45,7.10); palace.add(entryFrame);
const entry=new Mesh(new ShapeGeometry(arch(3.18,5.20),16),door); entry.position.set(0,.60,7.31); palace.add(entry);
box(gold,0,2.4,7.34,.06,3.4,.06);
for(const x of [-1.03,1.03]) for(const y of [1.55,3.1]) box(gold,x,y,7.35,.72,1.14,.05);
for(const x of [-3.25,3.25]) {
  const col=new Mesh(new CylinderGeometry(.24,.3,5.5,12),trim); col.position.set(x,3.4,7.65); palace.add(col);
  box(trim,x,.65,7.65,.83,.34,.83); box(trim,x,6.2,7.65,.9,.28,.9);
}
box(trim,0,6.56,7.35,8.6,.48,1.2);
const pedimentShape=new Shape(); pedimentShape.moveTo(-4.5,0);pedimentShape.lineTo(4.5,0);pedimentShape.lineTo(0,2);pedimentShape.closePath();
const pediment=new Mesh(new ExtrudeGeometry(pedimentShape,{depth:.55,bevelEnabled:false}),trim);pediment.position.set(0,6.8,7.2);palace.add(pediment);
const medallion=new Mesh(new SphereGeometry(.49,16,10),gold);medallion.scale.z=.2;medallion.position.set(0,7.54,7.82);palace.add(medallion);
// Terrace steps and balustrade, leaving the centre approach open.
const stepCount=4, stepThickness=.18, stepRise=.16;
for(let i=0;i<stepCount;i++) box(trim,0,stepThickness/2+i*stepRise,7.1-i*.45,42-i*.5,stepThickness,4.7-i*.7);
const topStep=stepCount-1;
const topStepSurface=stepThickness+topStep*stepRise;
const topStepFront=7.1-topStep*.45+(4.7-topStep*.7)/2;
// Rest the plinth on the highest tread; keep the entire railing behind its edge.
const railingBaseY=topStepSurface+.15/2;
const railingZ=topStepFront-.48/2;
for(const side of [-1,1]) {
  box(trim,side*12,railingBaseY,railingZ,14,.15,.43);
  box(trim,side*12,railingBaseY+.8,railingZ,14,.18,.48);
  for(let i=0;i<29;i++) box(trim,side*(5+i*.49),railingBaseY+.38,railingZ,.17,.7,.20);
}
// Roof dormers, chimneys and gold finials.
for(const x of [-11.5,-7.5,7.5,11.5]) {
  box(trim,x,12,3.5,1.65,1.85,.9);
  box(glass,x,12,4.0,1.0,1.3,.1);
  roof(x,3.5,2,1.5,12.95,.75);
  box(stone,x,14,-2.5,.8,2.1,.95);box(trim,x,15.1,-2.5,1.05,.22,1.2);
}
for(const x of [-17,0,17]) {
  const y=x===0?16.4:16.3;
  const orb=new Mesh(new SphereGeometry(.27,12,8),gold);orb.position.set(x,y+.32,.6);palace.add(orb);
  box(gold,x,y+.9,.6,.07,1.1,.07);
}
for(const [mat, matrices] of batches) {
  const mesh=new InstancedMesh(unit,mat,matrices.length);
  matrices.forEach((matrix,i)=>mesh.setMatrixAt(i,matrix)); mesh.instanceMatrix.needsUpdate=true; palace.add(mesh);
}
export default palace;
