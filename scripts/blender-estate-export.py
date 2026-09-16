"""Export selected assets, preserving baked morph clips and embedded PBR maps."""
stats={}
for group,objects in groups.items():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects: obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    scene.frame_set(scene.frame_start)
    bpy.ops.export_scene.gltf(filepath=str(OUT/(group+'.glb')),export_format='GLB',use_selection=True,use_active_scene=True,
        export_animations=True,export_animation_mode='SCENE',export_frame_range=True,
        export_morph=True,export_morph_normal=True,export_force_sampling=True,
        export_materials='EXPORT',export_yup=True,export_extras=True)
    triangles=0
    for obj in objects:
        obj.data.calc_loop_triangles(); triangles+=len(obj.data.loop_triangles)
    stats[group]={'triangles':triangles,'bytes':(OUT/(group+'.glb')).stat().st_size,
                  'objects':len(objects),'materials':len(set(m.name for o in objects for m in o.data.materials))}
# Keep the editable file outside public so the browser only ships compact GLBs.
scene.frame_set(scene.frame_start)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'artifacts/blender/estate-assets.blend'))
(ROOT/'artifacts/blender/asset-stats.json').write_text(json.dumps(stats,indent=2))
print(json.dumps(stats))
