"""Add properly rooted visible stems to the existing Blender garden GLBs.

The original flower head shapes, hedges, urn and scene transforms are retained.
Flower cups are lifted modestly above their foliage so the upper stems remain
visible, rather than being entirely swallowed by the existing leaf clusters.
Run after garden export, or directly against the already generated assets.
Reruns start from an immutable baseline and cannot accumulate duplicate stems.
"""
import bpy, bmesh, math, json, shutil
from pathlib import Path
from mathutils import Vector

VF_ROOT = Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
VF_OUT = VF_ROOT / 'public/gltf/garden'
VF_EVID = VF_ROOT / 'artifacts/vegetation'
VF_EVID.mkdir(parents=True, exist_ok=True)
vf_stats = {}
vf_scene = bpy.data.scenes.new('Roses - visible stems and botanical details')
bpy.context.window.scene = vf_scene
vf_scene.unit_settings.system = 'METRIC'
vf_stem_mat = bpy.data.materials.new('Rose stems and sepals - living green')
vf_stem_mat.use_nodes = True
vf_bsdf = next(n for n in vf_stem_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
vf_bsdf.inputs['Base Color'].default_value = (.075, .19, .033, 1)
vf_bsdf.inputs['Roughness'].default_value = .83
vf_stem_mat.use_backface_culling = False


def vf_stem(v, f, x, y, soil, top, seed, scale):
    # Blender Z-up coordinates are the same as the original garden source.
    start = len(v)
    sides, rings = 5, 4
    direction = seed * 2.39996
    bendx, bendy = math.cos(direction) * .035 * scale, math.sin(direction) * .035 * scale
    for ring in range(rings):
        t = ring / (rings - 1)
        radius = (.0065 - .0035 * t) * scale
        for i in range(sides):
            a = i * math.tau / sides
            v.append((x + bendx * (1 - t) + math.cos(a) * radius,
                      y + bendy * (1 - t) + math.sin(a) * radius,
                      soil + (top - soil) * t))
    for ring in range(rings - 1):
        for i in range(sides):
            a, b = start + ring * sides + i, start + ring * sides + (i + 1) % sides
            f.append((a, b, b + sides, a + sides))
    f.append(tuple(start + i for i in range(sides - 1, -1, -1)))
    f.append(tuple(start + (rings - 1) * sides + i for i in range(sides)))
    # Five pointed sepals visibly join the stem to the cup of petals.
    for i in range(5):
        a = i * math.tau / 5 + direction
        along = Vector((math.cos(a), math.sin(a), 0))
        across = Vector((-math.sin(a), math.cos(a), 0))
        center = Vector((x, y, top - .012 * scale))
        k = len(v)
        v += [tuple(center), tuple(center + along * .045 * scale + across * .013 * scale),
              tuple(center + along * .085 * scale + Vector((0, 0, -.021 * scale))),
              tuple(center + along * .045 * scale - across * .013 * scale),
              tuple(center + along * .039 * scale + Vector((0, 0, .008 * scale)))]
        f += [(k, k + 1, k + 4), (k + 1, k + 2, k + 4),
              (k + 2, k + 3, k + 4), (k + 3, k, k + 4)]
    # A pair of slender petioles exposes the lower stem, with folded serrate
    # leaves rather than the former floating corolla silhouette.
    for index in range(2):
        t = .28 + index * .24
        a = direction + index * 2.4
        along = Vector((math.cos(a), math.sin(a), .38)).normalized()
        across = Vector((-math.sin(a), math.cos(a), 0))
        center = Vector((x + bendx * (1 - t), y + bendy * (1 - t), soil + (top - soil) * t))
        k = len(v)
        v += [tuple(center), tuple(center + along * .08 * scale + across * .027 * scale),
              tuple(center + along * .155 * scale),
              tuple(center + along * .08 * scale - across * .027 * scale),
              tuple(center + along * .08 * scale + Vector((0, 0, .012 * scale)))]
        f += [(k, k + 1, k + 4), (k + 1, k + 2, k + 4),
              (k + 2, k + 3, k + 4), (k + 3, k, k + 4)]


for vf_asset in ('parterre', 'urn'):
    vf_baseline = VF_EVID / (vf_asset + '-before-stems.glb')
    if not vf_baseline.exists():
        shutil.copy2(VF_OUT / (vf_asset + '.glb'), vf_baseline)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.gltf(filepath=str(vf_baseline))
    vf_parts = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    vf_lift = .15 if vf_asset == 'parterre' else .14
    vf_lifted_vertex_count = 0
    for obj in vf_parts:
        petal_slots = {i for i, mat in enumerate(obj.data.materials) if mat and 'Rose petals' in mat.name}
        petal_vertices = {vi for face in obj.data.polygons if face.material_index in petal_slots for vi in face.vertices}
        vf_lifted_vertex_count += len(petal_vertices)
        for vi in petal_vertices:
            obj.data.vertices[vi].co.z += vf_lift
        obj.data.update()
    assert vf_lifted_vertex_count, 'Expected original rose petal material to preserve flower heads'
    vf_v, vf_f, vf_roses = [], [], []
    if vf_asset == 'parterre':
        for sx in (-1, 1):
            for sy in (-1, 1):
                for i in range(14):
                    a, r = i * 2.39996, .68 * math.sqrt((i + .5) / 14)
                    vf_roses.append((sx * 3.6 + r * math.cos(a), sy * 3.6 + r * math.sin(a),
                                     .052, .56 + vf_lift + .075 * math.sin(i * 2.3),
                                     i + int((sx + 1) * 8 + (sy + 1) * 4), 1.1))
        for i in range(14):
            a, r = i * 2.39996, .51 * math.sqrt((i + .5) / 14)
            vf_roses.append((r * math.cos(a), r * math.sin(a), .052,
                             .51 + vf_lift + .07 * math.sin(i * 2), 40 + i, 1.1))
    else:
        for i in range(12):
            a, r = i * 2.39996, .23 * math.sqrt((i + .5) / 12)
            vf_roses.append((r * math.cos(a), r * math.sin(a), .746,
                             .98 + vf_lift + .07 * math.sin(i * 2), 100 + i, .9))
    for args in vf_roses:
        vf_stem(vf_v, vf_f, *args)
    vf_mesh = bpy.data.meshes.new(vf_asset + ' rooted rose stems')
    vf_mesh.from_pydata(vf_v, [], vf_f)
    vf_mesh.update()
    vf_obj = bpy.data.objects.new(vf_asset + ' visible rose stems sepals and leaves', vf_mesh)
    vf_scene.collection.objects.link(vf_obj)
    vf_mesh.materials.append(vf_stem_mat)
    vf_uv = vf_mesh.uv_layers.new(name='UVMap')
    for face in vf_mesh.polygons:
        face.use_smooth = True
        for li in face.loop_indices:
            vertex = vf_mesh.vertices[vf_mesh.loops[li].vertex_index].co
            vf_uv.data[li].uv = (vertex.x * 3, vertex.z * 3)
    # Merge the single new material into the reusable, one-object garden asset.
    bpy.ops.object.select_all(action='DESELECT')
    for obj in vf_parts + [vf_obj]:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = vf_parts[0]
    bpy.ops.object.join()
    vf_result = bpy.context.object
    vf_result.name = 'Garden_' + vf_asset
    vf_scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.export_scene.gltf(filepath=str(VF_OUT / (vf_asset + '.glb')), export_format='GLB',
        use_selection=True, use_active_scene=True, export_animations=False, export_yup=True,
        export_materials='EXPORT', export_image_format='JPEG', export_jpeg_quality=88)
    vf_result.data.calc_loop_triangles()
    vf_stats[vf_asset] = {'flowersWithRootedStems': len(vf_roses),
                         'stemHeightMeters': [min(a[3] - a[2] for a in vf_roses), max(a[3] - a[2] for a in vf_roses)],
                         'triangles': len(vf_result.data.loop_triangles),
                         'bytes': (VF_OUT / (vf_asset + '.glb')).stat().st_size,
                         'flowerCenters': [list(a[:4]) for a in vf_roses]}
bpy.ops.wm.save_as_mainfile(filepath=str(VF_EVID / 'rooted-garden-flowers.blend'), compress=True)
(VF_EVID / 'flower-stats.json').write_text(json.dumps(vf_stats, indent=2))
print(json.dumps(vf_stats))
