# Separate inspection scenes share the authored meshes; original scenes are preserved.
for label,ids,pos,target in [
    ('REVIEW - Bench',['bench'],(3,-3,2),(0,0,.5)),
    ('REVIEW - Fountain',['basin','water','centralJet','lateralJet'],(10,-12,8),(0,0,1.5)),
]:
    review=bpy.data.scenes.new(label)
    review.frame_start=0; review.frame_end=96; review.render.fps=24
    review.world=bpy.data.worlds.new(label+' world'); review.world.use_nodes=True
    review.world.node_tree.nodes.get('Background') and None
    for node in review.world.node_tree.nodes:
        if node.type=='BACKGROUND': node.inputs[0].default_value=(.25,.29,.32,1)
    for asset_id in ids:
        for obj in groups[asset_id]: review.collection.objects.link(obj)
    # Instantiate the six lateral jets in their real fountain layout for inspection.
    if 'lateralJet' in ids:
        for obj in groups['lateralJet']: review.collection.objects.unlink(obj)
        for i in range(6):
            a=i*math.tau/6
            for obj in groups['lateralJet']:
                clone=obj.copy(); clone.data=obj.data
                clone.location=(3.1*math.cos(a),3.1*math.sin(a),0)
                clone.rotation_euler.z=a
                review.collection.objects.link(clone)
    camera_data=bpy.data.cameras.new(label+' camera')
    camera=bpy.data.objects.new(label+' camera',camera_data); review.collection.objects.link(camera)
    camera.location=pos; camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    review.camera=camera; camera_data.lens=45
    light_data=bpy.data.lights.new(label+' sun','SUN'); light_data.energy=2
    light=bpy.data.objects.new(label+' sun',light_data); review.collection.objects.link(light)
    light.rotation_euler=(.4,-.5,-.4)
    review.render.engine='CYCLES'; review.cycles.samples=32
    review.render.resolution_x=1000; review.render.resolution_y=750; review.render.resolution_percentage=100
    review.frame_set(0)
bpy.context.window.scene=review
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'artifacts/blender/estate-assets.blend'))
print('Saved editable Blender project with separate bench and fountain review scenes.')
