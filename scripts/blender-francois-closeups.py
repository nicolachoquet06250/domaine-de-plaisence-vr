import bpy,math
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/francois'
scene=bpy._natural_scene;bpy.context.window.scene=scene;scene.cycles.samples=12
cam=scene.camera;cam.data.ortho_scale=.79;cam.location=(0,-4,1.60);cam.rotation_euler=(Vector((0,0,1.60))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1400;scene.render.resolution_y=1000
for asset,m in bpy._natural_models.items():
    m['rig'].location.x=-.2 if asset=='courtMale' else .2;m['rig'].rotation_euler=(0,0,0);m['rig'].data.pose_position='REST'
scene.render.filepath=str(OUT/'portraits.png');bpy.ops.render.render(write_still=True)
for asset,m in bpy._natural_models.items():m['rig'].rotation_euler.z=math.pi/2 if asset=='courtMale' else -math.pi/2
scene.render.filepath=str(OUT/'profiles.png');bpy.ops.render.render(write_still=True)
for m in bpy._natural_models.values():m['rig'].rotation_euler.z=0
print('Final facial coordinate review complete')
