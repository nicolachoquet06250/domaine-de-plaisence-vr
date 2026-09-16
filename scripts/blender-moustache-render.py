import bpy,math
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/moustache'
scene=bpy._natural_scene;bpy.context.window.scene=scene;cam=scene.camera
male=bpy._natural_models['courtMale']['rig'];male.location.x=-.2;male.data.pose_position='REST'
hidden=[]
for ob in bpy._natural_models['courtFemale']['objects']:hidden.append((ob,ob.hide_render));ob.hide_render=True
cam.data.type='ORTHO';cam.data.ortho_scale=.35;cam.location=(-.2,-4,1.595)
cam.rotation_euler=(Vector((-.2,0,1.595))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.cycles.samples=12
for suffix,yaw in [('face',0),('trois-quarts',.8)]:
    male.rotation_euler.z=yaw;scene.render.filepath=str(OUT/(suffix+'.png'));bpy.ops.render.render(write_still=True)
male.rotation_euler.z=0
for ob,hide in hidden:ob.hide_render=hide
print('Moustache rendered front and three-quarter')
