from pathlib import Path
import bpy,math
from mathutils import Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
OUT=ROOT/'artifacts/avatars/francois'
scene=bpy._natural_scene;bpy.context.window.scene=scene
for ob in list(scene.objects):
    if ob.type in {'LIGHT','CAMERA'}:bpy.data.objects.remove(ob,do_unlink=True)
for asset,m in bpy._natural_models.items():
    m['rig'].location.x=-.49 if asset=='courtMale' else .49
    m['rig'].rotation_euler=(0,0,0);m['rig'].data.pose_position='REST'
src=(ROOT/'scripts/blender-natural-render.py').read_text(encoding='utf-8-sig')
src=src.replace('artifacts/avatars/natural','artifacts/avatars/francois').replace('samples=12','samples=16')
src=src.replace('cam.location=(.06,-4,1.65)','cam.location=(.0,-4,1.60)').replace('Vector((0,0,1.65))','Vector((0,0,1.60))')
exec(compile(src,'francois-studio','exec'))
for asset,m in bpy._natural_models.items():m['rig'].rotation_euler.z=math.pi/2 if asset=='courtMale' else -math.pi/2
scene.render.filepath=str(OUT/'profiles.png');bpy.ops.render.render(write_still=True)
for asset,m in bpy._natural_models.items():m['rig'].rotation_euler.z=.65 if asset=='courtMale' else -.65
scene.render.filepath=str(OUT/'trois-quarts.png');bpy.ops.render.render(write_still=True)
for m in bpy._natural_models.values():m['rig'].rotation_euler.z=0
print('Francois revision rendered: portraits, strict profiles, three-quarter and full figures')
