"""Run with Blender MCP, independently of other authoring scripts.

Replace the flat estate lawn and add an arrival lawn. All visible grass consists
of bent, folded mesh blades; there are no alpha cards or animated shaders.
Existing ground collision remains at y=0; the cut turf relief is only 0..22 mm.
Application coordinates are converted explicitly to Blender Z-up.
"""
import bpy, bmesh, math, json, random
from pathlib import Path

VR_ROOT = Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
VR_OUT = VR_ROOT / 'public/gltf/vegetation'
VR_EVID = VR_ROOT / 'artifacts/vegetation'
VR_OUT.mkdir(parents=True, exist_ok=True)
VR_EVID.mkdir(parents=True, exist_ok=True)
vr_scene = bpy.data.scenes.new('Cut lawns - dimensional grass source')
bpy.context.window.scene = vr_scene
vr_scene.unit_settings.system = 'METRIC'

# Reuse the original packed turf texture, preserving the garden palette.
bpy.ops.import_scene.gltf(filepath=str(VR_ROOT / 'public/gltf/garden/ground.glb'))
vr_imported = list(bpy.context.selected_objects)
vr_turf_mat = next(o.data.materials[0] for o in vr_imported if o.type == 'MESH')
vr_turf_mat.name = 'Living clipped turf - original garden texture'
for obj in vr_imported:
    bpy.data.objects.remove(obj, do_unlink=True)
vr_blade_mat = bpy.data.materials.new('Living grass - opaque folded blades')
vr_blade_mat.use_nodes = True
vr_blade_mat.use_backface_culling = False
vr_nt = vr_blade_mat.node_tree
vr_nt.nodes.clear()
vr_pbr = vr_nt.nodes.new('ShaderNodeBsdfPrincipled')
vr_pbr.inputs['Roughness'].default_value = .94
vr_out_node = vr_nt.nodes.new('ShaderNodeOutputMaterial')
vr_tint = vr_nt.nodes.new('ShaderNodeVertexColor')
vr_tint.layer_name = 'Tint'
vr_nt.links.new(vr_tint.outputs['Color'], vr_pbr.inputs['Base Color'])
vr_nt.links.new(vr_pbr.outputs['BSDF'], vr_out_node.inputs['Surface'])
vr_parts = {}
vr_stats = {}


def vr_mesh(asset, name, vertices, faces, material, colors=None):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(x, -z, y) for x, y, z in vertices], [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    vr_scene.collection.objects.link(obj)
    mesh.materials.append(material)
    if colors:
        attr = mesh.color_attributes.new(name='Tint', type='BYTE_COLOR', domain='POINT')
        for i, color in enumerate(colors):
            attr.data[i].color = (*color, 1)
        for face in mesh.polygons:
            face.use_smooth = True
    else:
        uv = mesh.uv_layers.new(name='UVMap')
        for face in mesh.polygons:
            for li in face.loop_indices:
                v = mesh.vertices[mesh.loops[li].vertex_index].co
                uv.data[li].uv = (v.x * 2, v.y * 2)
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
        for face in mesh.polygons:
            face.use_smooth = True
    vr_parts.setdefault(asset, []).append(obj)
    return obj


def vr_rect_distance(x, z, cx, cz, hx, hz):
    return max(abs(x - cx) - hx, abs(z - cz) - hz)


def vr_estate_clearance(x, z):
    # Negative means hardscape/building/planting bed. Bounds come from the scene
    # transforms, not guessed scatter masks. Keep walls and cypress trunks clear.
    distances = [
        vr_rect_distance(x, z, 0, 0, 3.57, 27.07),
        vr_rect_distance(x, z, 0, 0, 22.57, 3.57),
        vr_rect_distance(x, z, 0, -20, 22.57, 3.07),
        vr_rect_distance(x, z, 0, 24, 22.57, 3.07),
        vr_rect_distance(x, z, 0, -28, 21.3, 7.3),
    ]
    for px in (-12, 12):
        for pz in (-10, 10):
            distances.append(vr_rect_distance(x, z, px, pz, 7.04, 7.04))
    for wx in (-30, 30):
        distances.append(vr_rect_distance(x, z, wx, -5, .39, 35.15))
    for cx in (-23, 23):
        for cz in (-25, -18, -11, -4, 3, 10, 17, 24):
            distances.append(math.hypot(x - cx, z - cz) - .24)
    return min(distances)


def vr_height(x, z, clearance):
    if clearance <= 0:
        return 0
    fade = min(1, clearance / .55)
    return fade * (.011 + .005 * math.sin(x * 1.43 + z * .61)
                   + .004 * math.cos(z * 1.12 - x * .39)
                   + .002 * math.sin(x * 5.1 + z * 4.8))


def vr_blade(vertices, faces, colors, x, z, height, angle, width, length, bend, tint):
    # V-shaped cross section at the base and midrib, bent tip: six triangles
    # with real depth, rather than a flat, camera-facing grass card.
    ca, sa = math.cos(angle), math.sin(angle)
    start = len(vertices)
    points = [(-width / 2, 0, 0), (0, 0, width * .29), (width / 2, 0, 0),
              (-width * .34, length * .56, bend * .30),
              (0, length * .59, bend * .30 + width * .24),
              (width * .34, length * .56, bend * .30), (0, length, bend)]
    for across, up, along in points:
        vertices.append((x + ca * across - sa * along, height + up,
                         z + sa * across + ca * along))
        # Dark roots/light tips help read the cut blade volume at eye level.
        k = .64 + .36 * up / length
        colors.append(tuple(c * k for c in tint))
    faces.extend(tuple(start + i for i in face) for face in
                 [(0, 3, 4), (0, 4, 1), (1, 4, 5), (1, 5, 2), (3, 6, 4), (4, 6, 5)])


def vr_grass(asset, bounds, clearance, seed, step, tile_size):
    rng = random.Random(seed)
    batches = {}
    xmin, xmax, zmin, zmax = bounds
    nx, nz = math.ceil((xmax - xmin) / step), math.ceil((zmax - zmin) / step)
    count = 0
    samples = []
    for iz in range(nz):
        for ix in range(nx):
            x = xmin + (ix + .12 + .76 * rng.random()) * step
            z = zmin + (iz + .12 + .76 * rng.random()) * step
            edge = clearance(x, z)
            if x > xmax or z > zmax or edge < .075:
                continue
            # Dense perimeter blades, lighter interior. Every lawn region keeps
            # physical grass; the turf texture provides the dense distant fill.
            keep = .9 if edge < 1.05 else .53
            if rng.random() > keep:
                continue
            key = (int((x - xmin) / tile_size), int((z - zmin) / tile_size))
            v, f, c = batches.setdefault(key, ([], [], []))
            length = .065 + rng.random() * .063
            width = .012 + rng.random() * .012
            tint = (.105 + rng.random() * .025, .18 + rng.random() * .04, .048 + rng.random() * .018)
            vr_blade(v, f, c, x, z, vr_height(x, z, edge), rng.random() * math.tau,
                     width, length, .015 + rng.random() * .026, tint)
            count += 1
            if len(samples) < 24:
                samples.append([x, z, length, edge])
    for key, (v, f, c) in batches.items():
        vr_mesh(asset, 'Bent grass tile %d %d' % key, v, f, vr_blade_mat, c)
    vr_stats[asset] = {'bladeCount': count, 'bladeTriangles': count * 6,
                       'grassTiles': len(batches), 'bladeHeightMeters': [.065, .128],
                       'terrainReliefMeters': [0, .022], 'samples': samples}


# Domain turf preserves the entire original 70 x 90 metre support footprint.
vr_v, vr_f = [], []
for iz in range(91):
    z = -51 + iz
    for ix in range(71):
        x = -35 + ix
        vr_v.append((x, vr_height(x, z, vr_estate_clearance(x, z)), z))
for iz in range(90):
    for ix in range(70):
        a = iz * 71 + ix
        vr_f.append((a, a + 71, a + 72, a + 1))
# A shallow skirt replaces the old ground box without coplanar surface overlays.
for edge in [[i for i in range(71)], [90 * 71 + i for i in range(71)],
             [i * 71 for i in range(91)], [i * 71 + 70 for i in range(91)]]:
    for i in range(len(edge) - 1):
        a, b = edge[i:i + 2]
        start = len(vr_v)
        vr_v += [(vr_v[a][0], -.60, vr_v[a][2]), (vr_v[b][0], -.60, vr_v[b][2])]
        vr_f.append((a, b, start + 1, start))
vr_mesh('estateLawnRelief', 'Sculpted continuous cut turf', vr_v, vr_f, vr_turf_mat)
vr_grass('estateLawnRelief', (-35, 35, -51, 39), vr_estate_clearance, 204709, .32, 18)

# Arrival has no existing lawn: a separate gently modelled annulus meets the
# terrace edge, leaving the avatar selection space and its collision intact.
def vr_arrival_clearance(x, z):
    radius = math.hypot(x, z)
    return min(radius - 8.03, 20 - radius)

vr_v, vr_f = [], []
vr_segments, vr_rings = 160, 24
for ring in range(vr_rings + 1):
    radius = 8.01 + (20 - 8.01) * ring / vr_rings
    for i in range(vr_segments):
        a = i * math.tau / vr_segments
        x, z = math.cos(a) * radius, math.sin(a) * radius
        vr_v.append((x, vr_height(x, z, vr_arrival_clearance(x, z)), z))
for ring in range(vr_rings):
    for i in range(vr_segments):
        a, b = ring * vr_segments + i, ring * vr_segments + (i + 1) % vr_segments
        vr_f.append((a, b, b + vr_segments, a + vr_segments))
for ring in (0, vr_rings):
    for i in range(vr_segments):
        a, b = ring * vr_segments + i, ring * vr_segments + (i + 1) % vr_segments
        start = len(vr_v)
        vr_v += [(vr_v[a][0], -.3, vr_v[a][2]), (vr_v[b][0], -.3, vr_v[b][2])]
        vr_f.append((a, b, start + 1, start))
vr_mesh('arrivalLawnRelief', 'Arrival landscaped turf annulus', vr_v, vr_f, vr_turf_mat)
vr_grass('arrivalLawnRelief', (-20, 20, -20, 20), vr_arrival_clearance, 204710, .26, 20)

for asset, parts in vr_parts.items():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.export_scene.gltf(filepath=str(VR_OUT / (asset + '.glb')), export_format='GLB',
        use_selection=True, use_active_scene=True, export_animations=False, export_yup=True,
        export_materials='EXPORT', export_image_format='JPEG', export_jpeg_quality=88)
    for obj in parts:
        obj.data.calc_loop_triangles()
    vr_stats[asset].update({'triangles': sum(len(o.data.loop_triangles) for o in parts),
                            'bytes': (VR_OUT / (asset + '.glb')).stat().st_size,
                            'drawCalls': len(parts)})
bpy.ops.wm.save_as_mainfile(filepath=str(VR_EVID / 'dimensional-lawns.blend'), compress=True)
(VR_EVID / 'lawn-stats.json').write_text(json.dumps(vr_stats, indent=2))
print(json.dumps(vr_stats))
