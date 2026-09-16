import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
scene=bpy._natural_scene;bpy.context.window.scene=scene
for asset,m in bpy._natural_models.items():m['rig'].location.x=-.49 if asset=='courtMale' else .49
cam=scene.camera;cam.data.type='ORTHO';cam.data.ortho_scale=2.35
cam.location=(.6,-6,2.35);cam.rotation_euler=(Vector((0,0,.95))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1200;scene.render.resolution_y=1200
scene.render.filepath=str(ROOT/'artifacts/avatars/natural/duo.png')
bpy.ops.object.select_all(action='DESELECT')
for model in bpy._natural_models.values():
    for obj in model['objects']:obj.select_set(True)
bpy.context.view_layer.objects.active=bpy._natural_models['courtMale']['face']
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.shading.type='MATERIAL'
        area.spaces.active.region_3d.view_distance=3.0
        area.spaces.active.region_3d.view_location=Vector((0,0,1))
        area.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
bpy.data.libraries.write(str(ROOT/'artifacts/avatars/natural/renaissance-natural.blend'),{scene},fake_user=True,compress=True)
print('Editable avatar scene saved with studio, framing, skin, actions and visemes')
