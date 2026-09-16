import bpy, json
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
with bpy.data.libraries.load(str(ROOT/'artifacts/avatars/lipsync/renaissance-court-lipsync.blend'),link=False) as (src,dst):
    dst.scenes=src.scenes
srcscene=next(s for s in dst.scenes if any(o.name.startswith('courtMale') and o.type=='ARMATURE' for o in s.objects))
bpy._natural_source=srcscene
print(json.dumps({'source':srcscene.name,'objects':[{'name':o.name,'type':o.type,'vertices':len(o.data.vertices) if o.type=='MESH' else 0,'materials':[m.name for m in o.data.materials] if o.type=='MESH' else [],'groups':list(o.vertex_groups.keys()) if o.type=='MESH' else [],'bounds':[[min(v.co[i] for v in o.data.vertices),max(v.co[i] for v in o.data.vertices)] for i in range(3)] if o.type=='MESH' else []} for o in srcscene.objects]}))
