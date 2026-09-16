# One reusable pair of carved oak doors. Each leaf has a real hinge pivot.
for side in [-1,1]:
    asset='doorLeft' if side<0 else 'doorRight'; x=side*.8
    cbox(asset,cwood,x,1.75,0,1.59,3.5,.14)
    for y,h in [(.53,.69),(1.75,1.33),(2.96,.66)]:
        cbox(asset,cwood,x,y,.085,1.27,h,.07)
        for z in [-.102,.13]:
            cframe(asset,cgold,x,y,z,1.32,h+.08,.032)
            cframe(asset,ctrim,x,y,z,1.19,h-.055,.022)
    for yy in [.45,1.75,3.05]:
        clathe(asset,cgold,side*1.53,yy-.09,.06,[(.045,0),(.045,.18)],10)
    for z in [-.16,.16]:
        cbox(asset,cgold,side*.16,1.65,z,.12,.39,.045)
        cpath(asset,cgold,[(side*.16,1.65,z),(side*.40,1.65,z)],.038,8)
    cflush(asset)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in cobjects[asset]: obj.select_set(True)
    bpy.context.view_layer.objects.active=cobjects[asset][0]; bpy.ops.object.join()
    leaf=bpy.context.object; leaf.name='Oak_Leaf_Left' if side<0 else 'Oak_Leaf_Right'
    pivot=bpy.data.objects.new('Hinge_Left' if side<0 else 'Hinge_Right',None); cscene.collection.objects.link(pivot)
    pivot.location=(side*1.6,0,0); leaf.parent=pivot; leaf.location=(-side*1.6,0,0)
    # Cubic smooth opening, reversible in the runtime mixer. Blender Z becomes glTF Y.
    for frame,angle in [(1,0),(13,-side*16),(37,-side*89),(49,-side*105)]:
        pivot.rotation_euler.z=math.radians(angle); pivot.keyframe_insert(data_path='rotation_euler',frame=frame)
    pivot.animation_data.action.name='Door_Open'
    cobjects[asset]=[pivot,leaf]
cscene.frame_set(1)
for asset in ['palace','palaceInterior','palaceGlass']: cflush(asset)

def cexport(asset,objects,animate=False):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects: obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.gltf(filepath=str(COUT/(asset+'.glb')),export_format='GLB',use_selection=True,use_active_scene=True,
        export_yup=True,export_animations=animate,export_animation_mode='SCENE',export_frame_range=True,
        export_force_sampling=True,export_materials='EXPORT',export_image_format='JPEG',export_jpeg_quality=90)
    for obj in objects:
        if obj.type=='MESH': obj.data.calc_loop_triangles()
    return {'bytes':(COUT/(asset+'.glb')).stat().st_size,'triangles':sum(len(o.data.loop_triangles) for o in objects if o.type=='MESH')}

cstats={}
for asset in ['palace','palaceInterior','palaceGlass']: cstats[asset]=cexport(asset,cobjects[asset])
cstats['palaceDoor']=cexport('palaceDoor',cobjects['doorLeft']+cobjects['doorRight'],True)
# Collision envelopes are generated from the same dimensions as the visible mesh.
(CROOT/'src/scene-assets/castle-collision-data.json').write_text(json.dumps(csolid,separators=(',',':')))
(CEVID/'asset-stats.json').write_text(json.dumps(cstats,indent=2))

# Place a linked door pair into the entry for the editable Blender presentation.
for asset in ['doorLeft','doorRight']:
    pivot,leaf=cobjects[asset]; pivot.location.y=-6; pivot.location.z=.64; pivot.scale.z=2.9/3.5
world=bpy.data.worlds.new('Chateau daylight'); world.use_nodes=True
background=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND'); background.inputs[0].default_value=(.62,.73,.86,1); background.inputs[1].default_value=.65; cscene.world=world
sun_data=bpy.data.lights.new('Sun','SUN'); sun_data.energy=2.5; sun_data.angle=.09
sun=bpy.data.objects.new('Sun',sun_data); cscene.collection.objects.link(sun); sun.rotation_euler=(.5,-.4,-.6)
for name,pos,target in [('Facade',(34,-39,24),(0,0,6)),('Vestibule',(0,-4.8,2.4),(0,2.5,3.7)),('Salon',(9,-4.8,2.4),(14,0,2.0))]:
    data=bpy.data.cameras.new(name); camera=bpy.data.objects.new(name,data); cscene.collection.objects.link(camera); camera.location=pos
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler(); data.lens=23 if name!='Facade' else 45
    if name=='Facade': cscene.camera=camera
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D': area.spaces.active.region_3d.view_perspective='CAMERA'; area.spaces.active.shading.type='MATERIAL'
cscene.render.resolution_x=1400; cscene.render.resolution_y=1000; cscene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(CEVID/'chateau-plaisance.blend'))
print(json.dumps(cstats))
