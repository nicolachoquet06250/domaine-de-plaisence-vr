import bpy,json,traceback
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
report={'scene':bpy.context.scene.name,'mode':bpy.context.mode,'objectCount':len(bpy.context.scene.objects),
        'models':{a:[o.name for o in m['objects']] for a,m in getattr(bpy,'_natural_models',{}).items()},
        'currentAsset':globals().get('asset'),'native':[o.name for o in globals().get('native_emitters',[])],
        'scenes':[(s.name,len(s.objects)) for s in bpy.data.scenes]}
(ROOT/'artifacts/avatars/francois/status.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
