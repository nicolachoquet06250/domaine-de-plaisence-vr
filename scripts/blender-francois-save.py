from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
import bpy
assert all(o.particle_systems[0].use_hair_dynamics for o in bpy._organic_emitters)
code=(ROOT/'scripts/blender-natural-save.py').read_text(encoding='utf-8-sig')
code=code.replace('artifacts/avatars/natural','artifacts/avatars/francois').replace('renaissance-natural.blend','renaissance-francois.blend')
exec(compile(code,'francois-editable-source','exec'))
