"""Export the latest avatars without changing the authoring .blend or web assets."""
import bpy, hashlib, json, re
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/avatars/fbx'
SOURCE = ROOT / 'artifacts/avatars/moustache/renaissance-moustache.blend'
OUT.mkdir(parents=True, exist_ok=True)

def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:
        ob.hide_set(False)
        ob.hide_select = False
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]

def stats(objects, rig):
    meshes = [o for o in objects if o.type == 'MESH']
    for ob in meshes: ob.data.calc_loop_triangles()
    coords = [ob.matrix_world @ Vector(c) for ob in meshes for c in ob.bound_box]
    return {'meshes': len(meshes), 'vertices': sum(len(o.data.vertices) for o in meshes),
            'triangles': sum(len(o.data.loop_triangles) for o in meshes),
            'bones': [b.name for b in rig.data.bones],
            'shapeKeys': {o.name: [k.name for k in o.data.shape_keys.key_blocks][1:] for o in meshes if o.data.shape_keys},
            'bounds': {'min': [min(c[i] for c in coords) for i in range(3)], 'max': [max(c[i] for c in coords) for i in range(3)]},
            'skinnedMeshes': sum(any(m.type == 'ARMATURE' for m in o.modifiers) for o in meshes)}

report = {'source': str(SOURCE.relative_to(ROOT)), 'sourceSha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'blender': bpy.app.version_string, 'avatars': {}}
for asset in ['courtMale', 'courtFemale']:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    rig = next(o for o in scene.objects if o.type == 'ARMATURE' and o.name.startswith(asset))
    meshes = [o for o in scene.objects if o.type == 'MESH' and o.parent == rig and not o.particle_systems]
    for ob in list(bpy.data.objects):
        if ob not in [rig] + meshes: bpy.data.objects.remove(ob, do_unlink=True)
    rig.name = asset
    rig.location = (0, 0, 0)
    rig.rotation_euler = (0, 0, 0)
    rig.data.pose_position = 'REST'
    for ob in meshes:
        ob.hide_render = False
        ob.hide_set(False)
        if ob.data.shape_keys:
            for key in ob.data.shape_keys.key_blocks: key.value = 0
    scene.frame_set(0)
    bpy.context.view_layer.update()
    folder = OUT / asset
    textures = folder / 'Textures'
    textures.mkdir(parents=True, exist_ok=True)
    record = {'source': stats(meshes, rig), 'bakedColorMeshes': [], 'materials': []}
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 1
    scene.render.bake.use_pass_direct = False
    scene.render.bake.use_pass_indirect = False
    scene.render.bake.use_pass_color = True
    scene.render.bake.margin = 8
    # Bake vertex colors into ordinary UV textures for Unity's standard materials.
    for index, ob in enumerate(meshes):
        needs_bake = any(m and m.use_nodes and any(n.type == 'VERTEX_COLOR' for n in m.node_tree.nodes) for m in ob.data.materials)
        if not needs_bake: continue
        select([ob])
        if not ob.data.uv_layers:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(angle_limit=1.151917, island_margin=0.015)
            bpy.ops.object.mode_set(mode='OBJECT')
        img = bpy.data.images.new(f'{asset}-color-{index:02d}', width=2048, height=2048, alpha=False)
        img.filepath_raw = str(textures / (img.name + '.png'))
        img.file_format = 'PNG'
        for slot in ob.material_slots:
            slot.material = slot.material.copy()
            node = slot.material.node_tree.nodes.new('ShaderNodeTexImage')
            node.image = img
            slot.material.node_tree.nodes.active = node
        bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'})
        img.save()
        for mat in ob.data.materials:
            shader = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
            node = mat.node_tree.nodes.active
            mat.node_tree.links.new(node.outputs['Color'], shader.inputs['Base Color'])
        record['bakedColorMeshes'].append({'mesh': ob.name, 'texture': img.filepath_raw})
        print('BAKED', asset, ob.name, flush=True)
    # External PNG copies accompany the FBX, including the existing hair normal maps.
    used_mats = set(m for o in meshes for m in o.data.materials if m)
    for mat in sorted(used_mats, key=lambda m: m.name):
        shader = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        item = {'name': mat.name, 'metallic': shader.inputs['Metallic'].default_value,
                'roughness': shader.inputs['Roughness'].default_value, 'textures': []}
        for node in mat.node_tree.nodes:
            if node.type != 'TEX_IMAGE' or not node.image: continue
            img = node.image
            filename = re.sub(r'[^A-Za-z0-9_.-]', '_', img.name)
            if not filename.endswith('.png'): filename += '.png'
            img.filepath_raw = str(textures / filename)
            img.file_format = 'PNG'
            img.save()
            # Prefer the deliverable copy rather than an old packed authoring path.
            if img.packed_file: img.unpack(method='REMOVE')
            item['textures'].append('Textures/' + filename)
        record['materials'].append(item)
    record['clips'] = [t.name for t in rig.animation_data.nla_tracks]
    rig.data.pose_position = 'POSE'
    scene.frame_set(0)
    select([rig] + meshes)
    fbx = folder / (asset + '.fbx')
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={'ARMATURE', 'MESH'},
        use_mesh_modifiers=False, add_leaf_bones=False, use_armature_deform_only=False,
        axis_forward='-Z', axis_up='Y', apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
        use_space_transform=True, bake_space_transform=False, path_mode='COPY', embed_textures=True,
        bake_anim=True, bake_anim_use_nla_strips=True, bake_anim_use_all_actions=False,
        bake_anim_simplify_factor=0.0, use_custom_props=False)
    record['file'] = str(fbx.relative_to(OUT))
    record['bytes'] = fbx.stat().st_size
    record['sha256'] = hashlib.sha256(fbx.read_bytes()).hexdigest()
    report['avatars'][asset] = record
    (OUT / 'export-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('EXPORTED', asset, record['bytes'], flush=True)
print('FBX_EXPORT_COMPLETE', flush=True)
