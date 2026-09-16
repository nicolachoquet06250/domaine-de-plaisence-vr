import bpy, math
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
OUT=ROOT/'artifacts/avatars/natural'
scene=bpy._natural_scene;bpy.context.window.scene=scene
scene.render.engine='CYCLES';scene.cycles.samples=12
scene.cycles.use_denoising=True
scene.world=bpy.data.worlds.new('Atelier studio');scene.world.use_nodes=True
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.065,.08,.10,1);bg.inputs[1].default_value=.5
for name,pos,power,size in [('Key',(-3,-4,4),380,3),('Fill',(3,-2,2.7),180,2.5),('Rim',(1,2,3),420,2)]:
    data=bpy.data.lights.new('Atelier '+name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    ob=bpy.data.objects.new('Atelier '+name,data);scene.collection.objects.link(ob);ob.location=pos
    ob.rotation_euler=(Vector((0,0,1.2))-ob.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Atelier portraits');cam=bpy.data.objects.new('Atelier portraits',data);scene.collection.objects.link(cam);scene.camera=cam
data.type='ORTHO';data.ortho_scale=2.35
cam.location=(.6,-6,2.35);cam.rotation_euler=(Vector((0,0,.95))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.render.filepath=str(OUT/'duo.png');bpy.ops.render.render(write_still=True)
data.ortho_scale=.79;cam.location=(.06,-4,1.65);cam.rotation_euler=(Vector((0,0,1.65))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1400;scene.render.resolution_y=1000
bpy._natural_models['courtMale']['rig'].location.x=-.20
bpy._natural_models['courtFemale']['rig'].location.x=.20
scene.render.filepath=str(OUT/'portraits.png');bpy.ops.render.render(write_still=True)
bpy._natural_camera=cam
print('Studio renders complete')
