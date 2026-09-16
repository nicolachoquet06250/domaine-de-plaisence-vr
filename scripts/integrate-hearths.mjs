import { readFileSync, writeFileSync } from 'node:fs';
for (const path of ['public/scenes/plaisance.iwsdk.scene.json', 'public/scenes/modules/castle-blender.iwsdk.scene.json']) {
  const doc = JSON.parse(readFileSync(path));
  const nodes = doc.nodes.find(n => n.id === 'castle')?.children ?? doc.nodes;
  for (const side of [-1, 1]) for (const floor of [.64, 5.04]) {
    const id = `hearth-${side < 0 ? 'west' : 'east'}-${floor < 1 ? 'salon' : 'gallery'}`;
    const node = {
      id, name: `Foyer allume ${side < 0 ? 'ouest' : 'est'} ${floor < 1 ? 'salon' : 'etage'}`,
      content: { type: 'group' }, transform: { position: [side * 19.84, floor + .18, 0], rotationDeg: [0, -side * 90, 0] },
      components: { HearthFire: { phase: (side + 1) * 1.7 + floor } },
      children: [
        { id: `${id}-wood`, content: { type: 'asset', asset: 'hearth' } },
        { id: `${id}-flames`, content: { type: 'asset', asset: 'hearthFire' } },
        { id: `${id}-glow`, transform: { position: [0, .42, .27] }, components: { HearthGlow: { phase: (side + 1) * 1.7 + floor }, PointLight: { color: [1, .23, .035, 1], intensity: 3, distance: 3, decay: 2, castShadow: false } } },
      ],
    };
    const index = nodes.findIndex(n => n.id === id);
    if (index < 0) nodes.push(node); else nodes[index] = node;
  }
  doc.authoring ??= {}; doc.authoring.views ??= [];
  const z = path.includes('/modules/') ? 0 : -28;
  const views = [
    { id: 'hearth-detail', role: 'diagnostic', projection: 'perspective', position: [17.05, 1.55, z + 1.0], target: [19.84, 1.35, z], fov: 44 },
    { id: 'hearth-upper', role: 'diagnostic', projection: 'perspective', position: [-17.15, 6.10, z + .85], target: [-19.84, 5.9, z], fov: 44 },
    { id: 'chimney-wall-exterior', role: 'diagnostic', projection: 'perspective', position: [29, 5.4, z + 4], target: [21, 5.4, z], fov: 60 },
    { id: 'chimney-wall-interior', role: 'diagnostic', projection: 'perspective', position: [16.5, 2.7, z + 3], target: [20.6, 2.8, z], fov: 70 },
  ];
  for (const view of views) { const index = doc.authoring.views.findIndex(v => v.id === view.id); if (index < 0) doc.authoring.views.push(view); else doc.authoring.views[index] = view; }
  writeFileSync(path, JSON.stringify(doc, null, 2) + '\n');
}
