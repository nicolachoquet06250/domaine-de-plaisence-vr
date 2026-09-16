import bpy, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/avatars/fbx'
export = json.loads((OUT / 'export-report.json').read_text(encoding='utf-8'))
results = {}
for asset, source in export['avatars'].items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(OUT / source['file']), use_anim=True)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    rigs = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
    assert len(rigs) == 1, (asset, 'armature count')
    rig = rigs[0]
    rig.data.pose_position = 'REST'
    bpy.context.view_layer.update()
    assert set(b.name for b in rig.data.bones) == set(source['source']['bones']), 'bone loss'
    assert len(meshes) == source['source']['meshes'], 'mesh loss'
    assert sum(len(o.data.vertices) for o in meshes) == source['source']['vertices'], 'vertex loss'
    for ob in meshes: ob.data.calc_loop_triangles()
    assert sum(len(o.data.loop_triangles) for o in meshes) == source['source']['triangles'], 'triangle loss'
    face = next(o for o in meshes if o.data.shape_keys)
    keys = face.data.shape_keys.key_blocks
    expected = next(iter(source['source']['shapeKeys'].values()))
    assert set(k.name for k in keys[1:]) == set(expected), 'viseme loss'
    deltas = {k.name: max((v.co - b.co).length for v, b in zip(k.data, keys[0].data)) for k in keys[1:]}
    assert all(v > 0 for v in deltas.values()), 'empty viseme'
    unweighted = sum(not any(g.weight > 0 for g in v.groups) for o in meshes for v in o.data.vertices)
    assert unweighted == 0, ('unweighted vertices', unweighted)
    actions = [a.name for a in bpy.data.actions]
    assert all(any(clip in a for a in actions) for clip in source['clips']), ('missing clips', actions)
    coords = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
    height = max(v.z for v in coords) - min(v.z for v in coords)
    assert 1.6 < height < 1.9, ('unexpected scale', height)
    images = [i for i in bpy.data.images if i.source == 'FILE']
    # Image loading is lazy after FBX import; access pixels before checking it.
    for img in images:
        assert len(img.pixels) > 0, ('missing texture', img.name, img.filepath)
    assert images and all(i.has_data for i in images), 'missing textures'
    results[asset] = {'passed': True, 'bones': len(rig.data.bones), 'meshes': len(meshes),
        'triangles': sum(len(o.data.loop_triangles) for o in meshes), 'heightMeters': height,
        'visemeMaxDisplacementMeters': deltas, 'unweightedVertices': unweighted, 'animationClips': actions,
        'loadedImages': [i.name for i in images]}
(OUT / 'verification-blender.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print('FBX_ROUNDTRIP_PASSED', json.dumps(results))
