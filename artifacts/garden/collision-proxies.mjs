import { BoxGeometry, BufferGeometry, Float32BufferAttribute, Group, Mesh, MeshBasicMaterial, CylinderGeometry, SphereGeometry } from '@iwsdk/core';
// Only solid envelopes are baked for locomotion. Blender leaves, petals and stone
// bevels never become collision triangles or duplicate hidden render resources.
const material = new MeshBasicMaterial();
const cube = new BoxGeometry(1, 1, 1);
function box(group, x, y, z, sx, sy, sz) {
    const mesh = new Mesh(cube, material);
    mesh.position.set(x, y, z);
    mesh.scale.set(sx, sy, sz);
    group.add(mesh);
}
function strip(group, points, width, height, closed = false) {
    const positions = [], indices = [];
    const count = points.length;
    for (let i = 0; i < count; i++) {
        const before = points[closed ? (i + count - 1) % count : Math.max(0, i - 1)];
        const after = points[closed ? (i + 1) % count : Math.min(count - 1, i + 1)];
        const dx = after[0] - before[0], dz = after[1] - before[1];
        const distance = Math.hypot(dx, dz);
        const nx = -dz / distance * width / 2, nz = dx / distance * width / 2;
        const [x, z] = points[i];
        positions.push(x - nx, .04, z - nz, x + nx, .04, z + nz, x + nx, height, z + nz, x - nx, height, z - nz);
    }
    for (let i = 0; i < (closed ? count : count - 1); i++) {
        for (let side = 0; side < 4; side++) {
            const a = i * 4 + side, b = i * 4 + (side + 1) % 4;
            const c = ((i + 1) % count) * 4 + (side + 1) % 4, d = ((i + 1) % count) * 4 + side;
            indices.push(a, c, b, a, d, c);
        }
    }
    if (!closed) {
        indices.push(0, 1, 2, 0, 2, 3);
        const end = (count - 1) * 4;
        indices.push(end, end + 2, end + 1, end, end + 3, end + 2);
    }
    const geometry = new BufferGeometry();
    geometry.setAttribute('position', new Float32BufferAttribute(positions, 3));
    geometry.setIndex(indices);
    group.add(new Mesh(geometry, material));
}
export const ground = new Group();
ground.name = 'Solid lawn';
box(ground, 0, -.3, -6, 70, .6, 90);
export const path = new Group();
path.name = 'Solid gravel';
box(path, 0, 0, 0, 1, .08, 1);
export const parterre = new Group();
parterre.name = 'Solid parterre envelopes';
box(parterre, 0, .027, 0, 14, .05, 14);
const sphere = new SphereGeometry(1, 10, 7);
for (const sign of [-1, 1]) {
    box(parterre, sign * 6.93, .09, 0, .14, .18, 14);
    box(parterre, 0, .09, sign * 6.93, 14, .18, .14);
    for (const half of [-1, 1]) {
        box(parterre, sign * 6.48, .26, half * 3.62, .36, .45, 5.8);
        box(parterre, half * 3.62, .26, sign * 6.48, 5.8, .45, .36);
    }
}
for (const sx of [-1, 1])
    for (const sz of [-1, 1]) {
        const x = sx * 3.6, z = sz * 3.6;
        strip(parterre, [[x + 1.92, z], [x, z + 1.92], [x - 1.92, z], [x, z - 1.92]], .31, .47, true);
        const points = [];
        for (let i = 0; i < 32; i++) {
            const angle = i * Math.PI / 16, radius = 1.02 + .17 * Math.cos(angle * 4);
            points.push([x + radius * Math.cos(angle), z + radius * Math.sin(angle)]);
        }
        strip(parterre, points, .30, .41, true);
        const topiary = new Mesh(sphere, material);
        topiary.position.set(sx * 5.7, .65, sz * 5.7);
        topiary.scale.set(.49, .56, .49);
        parterre.add(topiary);
    }
const centre = [];
for (let i = 0; i < 48; i++) {
    const angle = i * Math.PI / 24, radius = 1.45 + .45 * Math.cos(angle * 4);
    centre.push([radius * Math.cos(angle), radius * Math.sin(angle)]);
}
strip(parterre, centre, .29, .41, true);
export const cypress = new Group();
cypress.name = 'Solid cypress';
const trunk = new Mesh(new CylinderGeometry(.10, .17, 1.4, 8), material);
trunk.position.y = .7;
cypress.add(trunk);
const crown = new Mesh(sphere, material);
crown.position.y = 2.71;
crown.scale.set(.64, 2.29, .64);
cypress.add(crown);
export const urn = new Group();
urn.name = 'Solid stone urn';
box(urn, 0, .065, 0, .52, .13, .52);
const vessel = new Mesh(new CylinderGeometry(.44, .15, .69, 12), material);
vessel.position.y = .495;
urn.add(vessel);
export const gardenBorder = new Group();
gardenBorder.name = 'Solid garden wall';
box(gardenBorder, 0, .35, 0, 10, .70, .405);
box(gardenBorder, 0, .77, 0, 10, .13, .53);
for (const x of [-4.88, 0, 4.88])
    box(gardenBorder, x, .50, 0, .73, 1, .73);
export const bench = new Group();
bench.name = 'Solid oak bench';
box(bench, 0, .515, 0, 2.1, .065, .59);
box(bench, 0, .855, -.32, 2.1, .42, .075);
for (const x of [-.76, .76]) {
    box(bench, x, .26, 0, .10, .52, .60);
    box(bench, x, .755, 0, .09, .1, .56);
}
