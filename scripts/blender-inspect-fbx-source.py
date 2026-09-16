import bpy, json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root / 'artifacts/avatars/moustache/renaissance-moustache.blend'))
report = {'version': bpy.app.version_string, 'objects': [], 'materials': []}
for ob in bpy.context.scene.objects:
    if ob.type not in {'ARMATURE', 'MESH'}: continue
    record = {'name': ob.name, 'type': ob.type, 'parent': ob.parent.name if ob.parent else None, 'location': list(ob.location), 'scale': list(ob.scale)}
    if ob.type == 'ARMATURE':
        record['bones'] = [b.name for b in ob.data.bones]
        record['tracks'] = [t.name for t in ob.animation_data.nla_tracks] if ob.animation_data else []
    else:
        record.update(vertices=len(ob.data.vertices), particles=len(ob.particle_systems), modifiers=[m.type for m in ob.modifiers], materials=[m.name for m in ob.data.materials], uv=[u.name for u in ob.data.uv_layers], colors=[c.name for c in ob.data.color_attributes], keys=[k.name for k in ob.data.shape_keys.key_blocks] if ob.data.shape_keys else [])
    report['objects'].append(record)
for mat in bpy.data.materials:
    if mat.use_nodes:
        report['materials'].append({'name': mat.name, 'nodes': [{'type': n.type, 'image': n.image.name if n.type == 'TEX_IMAGE' and n.image else None} for n in mat.node_tree.nodes], 'links': [(l.from_node.type, l.from_socket.name, l.to_node.type, l.to_socket.name) for l in mat.node_tree.links]})
out = root / 'artifacts/avatars/fbx'
out.mkdir(parents=True, exist_ok=True)
(out / 'source-inspection.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('FBX_SOURCE_INSPECTED', len(report['objects']))
