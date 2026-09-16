# Keep the actual exported meshes editable, each with its own inspection scene.
review_scenes=[]
for asset, distance in [('parterre',19),('cypress',8),('urn',2),('gardenBorder',13),('ground',110),('pathLong',2)]:
    review=bpy.data.scenes.new('REVIEW - Garden '+asset)
    review.unit_settings.system='METRIC'
    obj=gparts[asset][0]
    review.collection.objects.link(obj)
    centre=Vector((0,0,2.3 if asset=='cypress' else .4 if asset=='urn' else 0))
    camera_data=bpy.data.cameras.new('Review '+asset)
    camera=bpy.data.objects.new('Camera '+asset,camera_data); review.collection.objects.link(camera)
    camera.location=centre+Vector((distance*.65,-distance*.8,distance*.72))
    camera.rotation_euler=(centre-camera.location).to_track_quat('-Z','Y').to_euler()
    camera_data.lens=48; camera_data.clip_end=500; review.camera=camera
    world=bpy.data.worlds.new('Soft daylight '+asset); world.use_nodes=True
    background=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
    background.inputs[0].default_value=(.63,.72,.82,1)
    background.inputs[1].default_value=.7; review.world=world
    light_data=bpy.data.lights.new('Sun '+asset,'SUN'); light_data.energy=2; light_data.angle=.15
    light=bpy.data.objects.new('Sun '+asset,light_data); light.rotation_euler=(.5,-.3,-.4); review.collection.objects.link(light)
    review.render.resolution_x=1200; review.render.resolution_y=900; review.render.resolution_percentage=100
    review_scenes.append(review)
bpy.context.window.scene=review_scenes[0]
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA'
        area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(EVIDENCE/'garden-assets.blend'))
print(json.dumps({'saved':str(EVIDENCE/'garden-assets.blend'),'reviews':[s.name for s in review_scenes]}))
