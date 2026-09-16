import bpy, json
from pathlib import Path
root=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
with bpy.data.libraries.load(str(root/'artifacts/avatars/renaissance-court.blend'),link=False) as (src,dst):
    dst.scenes=src.scenes
scene=next(s for s in dst.scenes if any(o.name.startswith('courtMale') and o.type=='ARMATURE' for o in s.objects))
bpy.context.window.scene=scene
print(json.dumps({'scene':scene.name,'objects':[{'name':o.name,'type':o.type,'vertices':len(o.data.vertices) if o.type=='MESH' else None,'location':list(o.location)} for o in scene.objects if o.name.startswith('court')]}))
bpy._lip_source_scene=scene
