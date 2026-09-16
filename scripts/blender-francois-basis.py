import bpy
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
face=bpy._natural_models['courtMale']['face'];keys=face.data.shape_keys.key_blocks
maximum=max((a.co-b.co).length for a,b in zip(keys['Basis'].data,keys['viseme_sil'].data))
for a,b,v in zip(keys['Basis'].data,keys['viseme_sil'].data,face.data.vertices):a.co=b.co;v.co=b.co
for key in keys[1:]:key.value=0
face.data.update()
print('Restored rest-pose coordinates from identical silence morph; previous difference',maximum)
code=(ROOT/'scripts/blender-refined-export.py').read_text(encoding='utf-8-sig')
start=code.index("    for ob in m['objects']:");end=code.index('    for ob in joined:\n',start)
code=code[:start]+"    joined=m['objects'];gaps=[.0033]\n"+code[end:]
code=code.replace('artifacts/avatars/refined','artifacts/avatars/francois').replace('renaissance-refined.blend','renaissance-francois.blend')
exec(compile(code,'francois-rest-export','exec'))
