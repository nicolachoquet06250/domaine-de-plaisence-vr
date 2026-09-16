from pathlib import Path
import bpy
for ob in list(bpy._natural_scene.objects):
    if ob.type in {'LIGHT','CAMERA'}:bpy.data.objects.remove(ob,do_unlink=True)
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
code=(ROOT/'scripts/blender-natural-render.py').read_text(encoding='utf-8-sig').replace("artifacts/avatars/natural","artifacts/avatars/organic").replace('samples=12','samples=8')
exec(compile(code,'organic-studio-render','exec'))
