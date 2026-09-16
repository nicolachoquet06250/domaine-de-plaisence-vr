import bmesh
bpy.context.window.scene=garden_scene
stats={}
for asset,parts in gparts.items():
    # Recalculate manifold shell normals; never change thin leaf/petal normals.
    for obj in parts:
        if len(obj.data.materials)==1 and obj.data.materials[0] not in [leaf_mat,petal_mat]:
            bm=bmesh.new(); bm.from_mesh(obj.data)
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
            bm.to_mesh(obj.data); bm.free()
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts: obj.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]
    if len(parts)>1: bpy.ops.object.join()
    obj=bpy.context.object; obj.name='Garden_'+asset
    garden_scene.cursor.location=(0,0,0); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    gparts[asset]=[obj]
    obj.data.calc_loop_triangles()
    bpy.ops.export_scene.gltf(filepath=str(GOUT/(asset+'.glb')),export_format='GLB',use_selection=True,use_active_scene=True,
        export_animations=False,export_yup=True,export_materials='EXPORT',export_image_format='JPEG',export_jpeg_quality=88)
    stats[asset]={'triangles':len(obj.data.loop_triangles),'bytes':(GOUT/(asset+'.glb')).stat().st_size,'materials':len(set(m.name for m in obj.data.materials))}
bpy.ops.wm.save_as_mainfile(filepath=str(EVIDENCE/'garden-assets.blend'))
(EVIDENCE/'asset-stats.json').write_text(json.dumps(stats,indent=2))
print(json.dumps(stats))
