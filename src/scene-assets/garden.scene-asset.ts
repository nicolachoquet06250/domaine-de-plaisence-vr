import {
  BoxGeometry, BufferGeometry, Color, CylinderGeometry, Group, InstancedMesh,
  LatheGeometry, Matrix4, Mesh, MeshStandardMaterial, Object3D, SphereGeometry,
  TorusGeometry, Vector2,
} from '@iwsdk/core';

// All prototypes are deterministic, parentless and safe in both manifest realms.
const limestone = new MeshStandardMaterial({ color: '#d6c5a6', roughness: 0.9 });
const coping = new MeshStandardMaterial({ color: '#f0dfbd', roughness: 0.78 });
const gravel = new MeshStandardMaterial({ color: '#cbbb9a', roughness: 1 });
const lawn = new MeshStandardMaterial({ color: '#617c43', roughness: 1 });
const boxwood = new MeshStandardMaterial({ color: '#355339', roughness: 0.98 });
const foliage = new MeshStandardMaterial({ color: '#496448', roughness: 1 });
const darkGreen = new MeshStandardMaterial({ color: '#284d3d', roughness: 0.95 });
const bark = new MeshStandardMaterial({ color: '#75614a', roughness: 1 });
const wood = new MeshStandardMaterial({ color: '#82654d', roughness: 0.87 });
const blossoms = new MeshStandardMaterial({ color: '#ffffff', roughness: 0.84 });
const unitBox = new BoxGeometry(1, 1, 1);
const leafGeometry = new SphereGeometry(1, 7, 5);
const flowerGeometry = new SphereGeometry(1, 6, 4);
const cypressGeometry = new SphereGeometry(1, 10, 8);

type Placement = { x: number; y: number; z: number; sx: number; sy: number; sz: number; yaw?: number; color?: string };
function batch(parent: Group, name: string, geometry: BufferGeometry, material: MeshStandardMaterial, placements: Placement[], shadow = false) {
  const mesh = new InstancedMesh(geometry, material, placements.length);
  mesh.name = name;
  const transform = new Object3D();
  const color = new Color();
  placements.forEach((p, i) => {
    transform.position.set(p.x, p.y, p.z);
    transform.scale.set(p.sx, p.sy, p.sz);
    transform.rotation.set(0, p.yaw ?? 0, 0);
    transform.updateMatrix();
    mesh.setMatrixAt(i, transform.matrix);
    if (p.color) mesh.setColorAt(i, color.set(p.color));
  });
  mesh.instanceMatrix.needsUpdate = true;
  if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  mesh.castShadow = shadow;
  mesh.receiveShadow = true;
  mesh.computeBoundingBox();
  mesh.computeBoundingSphere();
  parent.add(mesh);
  return mesh;
}
function box(parent: Group, name: string, material: MeshStandardMaterial, x: number, y: number, z: number, sx: number, sy: number, sz: number) {
  const mesh = new Mesh(unitBox, material);
  mesh.name = name;
  mesh.position.set(x, y, z);
  mesh.scale.set(sx, sy, sz);
  mesh.receiveShadow = true;
  parent.add(mesh);
  return mesh;
}
function roseCluster(leaves: Placement[], flowers: Placement[], x: number, z: number, radius: number, height = 0.36, count = 26) {
  const palette = ['#e7d8ac', '#d7a7a0', '#f3e6c9', '#a89ab5'];
  for (let i = 0; i < count; i++) {
    const angle = i * 2.399963229728653;
    const r = radius * Math.sqrt((i + 0.5) / count);
    const px = x + Math.cos(angle) * r;
    const pz = z + Math.sin(angle) * r;
    const py = height + 0.09 * Math.sin(i * 2.1);
    leaves.push({ x: px, y: py, z: pz, sx: 0.28, sy: 0.22, sz: 0.24, yaw: angle });
    for (let p = 0; p < 5; p++) {
      const a = p * Math.PI * 0.4;
      flowers.push({ x: px + Math.cos(a) * 0.068, y: py + 0.21, z: pz + Math.sin(a) * 0.068,
        sx: 0.079, sy: 0.038, sz: 0.079, color: palette[i % palette.length] });
    }
    flowers.push({ x: px, y: py + 0.237, z: pz, sx: 0.054, sy: 0.043, sz: 0.054, color: '#e4c588' });
  }
}

export const ground = new Group();
ground.name = 'Pelouse du domaine';
box(ground, 'Sol continu', lawn, 0, -0.3, -6, 70, 0.6, 90);

export const path = new Group();
path.name = 'Allee de gravier calcaire';
box(path, 'Gravier', gravel, 0, 0, 0, 1, 0.08, 1);

export const parterre = new Group();
parterre.name = 'Parterre de broderie et roseraie';
box(parterre, 'Sable dore', gravel, 0, 0.027, 0, 14, 0.05, 14);
const curbs: Placement[] = [];
const hedges: Placement[] = [];
const scrolls: Placement[] = [];
const leaves: Placement[] = [];
const flowers: Placement[] = [];
for (const sign of [-1, 1]) {
  curbs.push({ x: sign * 6.93, y: 0.09, z: 0, sx: 0.14, sy: 0.18, sz: 14 });
  curbs.push({ x: 0, y: 0.09, z: sign * 6.93, sx: 13.72, sy: 0.18, sz: 0.14 });
  // Four interruptions leave a small cross-axis access through each parterre.
  for (const half of [-1, 1]) {
    hedges.push({ x: sign * 6.48, y: 0.28, z: half * 3.62, sx: 0.38, sy: 0.48, sz: 5.8 });
    hedges.push({ x: half * 3.62, y: 0.28, z: sign * 6.48, sx: 5.8, sy: 0.48, sz: 0.38 });
  }
}
for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
  const cx = sx * 3.6;
  const cz = sz * 3.6;
  // Diamond scrolls enclose four roses and echo the axial French garden plan.
  for (let side = 0; side < 4; side++) {
    const a = side * Math.PI / 2 + Math.PI / 4;
    hedges.push({ x: cx + Math.cos(a) * 1.34, y: 0.27, z: cz + Math.sin(a) * 1.34,
      sx: 2.8, sy: 0.43, sz: 0.3, yaw: -a + Math.PI / 2 });
  }
  for (let i = 0; i < 64; i++) {
    const a = i * Math.PI / 32;
    const r = 1.02 + 0.17 * Math.cos(a * 4);
    scrolls.push({ x: cx + Math.cos(a) * r, y: 0.26, z: cz + Math.sin(a) * r,
      sx: 0.19, sy: 0.24, sz: 0.19 });
  }
  roseCluster(leaves, flowers, cx, cz, 0.79);
  // Small rounded topiary at the garden corners.
  scrolls.push({ x: sx * 5.7, y: 0.65, z: sz * 5.7, sx: 0.5, sy: 0.58, sz: 0.5 });
}
// A four-lobed centre rosette, clipped low to preserve the view to the fountain.
for (let i = 0; i < 112; i++) {
  const a = i * Math.PI / 56;
  const r = 1.45 + 0.45 * Math.cos(a * 4);
  scrolls.push({ x: Math.cos(a) * r, y: 0.25, z: Math.sin(a) * r, sx: 0.18, sy: 0.22, sz: 0.18 });
}
roseCluster(leaves, flowers, 0, 0, 0.62, 0.32, 18);
batch(parterre, 'Bordures de pierre', unitBox, coping, curbs);
batch(parterre, 'Buis tailles droits', unitBox, boxwood, hedges);
batch(parterre, 'Broderies de buis', leafGeometry, boxwood, scrolls);
batch(parterre, 'Feuillage des rosiers', leafGeometry, foliage, leaves);
batch(parterre, 'Petales et coeurs des roses', flowerGeometry, blossoms, flowers);

export const cypress = new Group();
cypress.name = 'Cypres taille en fuseau';
const trunk = new Mesh(new CylinderGeometry(0.105, 0.18, 1.15, 8), bark);
trunk.position.y = 0.575;
cypress.add(trunk);
batch(cypress, 'Couronne persistante', cypressGeometry, darkGreen, [
  { x: 0, y: 2.08, z: 0, sx: 0.64, sy: 1.75, sz: 0.64 },
  { x: 0, y: 3.12, z: 0, sx: 0.44, sy: 1.5, sz: 0.44 },
  { x: 0, y: 4.05, z: 0, sx: 0.24, sy: 1.0, sz: 0.24 },
], true);

export const bench = new Group();
bench.name = 'Banc de jardin en chene et pierre';
for (const x of [-0.72, 0.72]) {
  box(bench, 'Pied sculpte', limestone, x, 0.25, 0, 0.22, 0.5, 0.57);
  box(bench, 'Socle', coping, x, 0.055, 0, 0.35, 0.11, 0.69);
  box(bench, 'Accoudoir de pierre', coping, x, 0.76, 0, 0.16, 0.12, 0.66);
  box(bench, 'Montant', limestone, x, 0.66, -0.22, 0.15, 0.8, 0.15);
}
const slats: Placement[] = [];
for (let i = 0; i < 4; i++) slats.push({ x: 0, y: 0.52, z: -0.24 + i * 0.16, sx: 2.1, sy: 0.095, sz: 0.12 });
for (let i = 0; i < 3; i++) slats.push({ x: 0, y: 0.72 + i * 0.15, z: -0.265, sx: 2.1, sy: 0.105, sz: 0.075 });
batch(bench, 'Lattes de chene', unitBox, wood, slats);

export const urn = new Group();
urn.name = 'Vase Medicis fleuri';
box(urn, 'Socle du vase', limestone, 0, 0.065, 0, 0.52, 0.13, 0.52);
const profile = [[0, 0.12], [0.24, 0.12], [0.24, 0.19], [0.135, 0.23], [0.12, 0.34], [0.2, 0.41],
  [0.3, 0.45], [0.4, 0.62], [0.43, 0.76], [0.46, 0.78], [0.46, 0.84], [0.38, 0.85],
  [0.34, 0.73], [0, 0.68]].map(([x, y]) => new Vector2(x, y));
const vessel = new Mesh(new LatheGeometry(profile, 20), coping);
vessel.name = 'Coupe evasee en pierre';
vessel.castShadow = true;
vessel.receiveShadow = true;
urn.add(vessel);
const handles = new InstancedMesh(new TorusGeometry(0.14, 0.035, 5, 12), limestone, 2);
handles.setMatrixAt(0, new Matrix4().makeTranslation(-0.41, 0.64, 0));
handles.setMatrixAt(1, new Matrix4().makeTranslation(0.41, 0.64, 0));
handles.instanceMatrix.needsUpdate = true;
handles.name = 'Anses';
urn.add(handles);
const urnLeaves: Placement[] = [];
const urnFlowers: Placement[] = [];
roseCluster(urnLeaves, urnFlowers, 0, 0, 0.32, 0.85, 10);
batch(urn, 'Feuillage retombant', leafGeometry, foliage, urnLeaves);
batch(urn, 'Fleurs du vase', flowerGeometry, blossoms, urnFlowers);

export const gardenBorder = new Group();
gardenBorder.name = 'Muret du jardin';
box(gardenBorder, 'Mur de pierre', limestone, 0, 0.36, 0, 10, 0.72, 0.4);
box(gardenBorder, 'Chaperon', coping, 0, 0.76, 0, 10.1, 0.12, 0.54);
for (const x of [-4.88, 0, 4.88]) {
  box(gardenBorder, 'Pilastre', limestone, x, 0.46, 0, 0.6, 0.92, 0.62);
  box(gardenBorder, 'Chapiteau', coping, x, 0.96, 0, 0.73, 0.1, 0.75);
}
