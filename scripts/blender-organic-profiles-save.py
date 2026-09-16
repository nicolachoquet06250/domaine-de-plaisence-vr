import bpy,math,json
from mathutils import Vector
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/organic'
scene=bpy._natural_scene;bpy.context.window.scene=scene
for asset,m in bpy._natural_models.items():m['rig'].rotation_euler.z=.95 if asset=='courtMale' else -.95
scene.render.filepath=str(OUT/'profiles.png');bpy.ops.render.render(write_still=True)
for m in bpy._natural_models.values():m['rig'].rotation_euler.z=0
src=(ROOT/'scripts/blender-natural-save.py').read_text(encoding='utf-8-sig').replace('artifacts/avatars/natural','artifacts/avatars/organic').replace('renaissance-natural.blend','renaissance-organic.blend')
exec(compile(src,'organic-save','exec'))
