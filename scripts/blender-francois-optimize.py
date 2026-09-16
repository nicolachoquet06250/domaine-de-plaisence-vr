import bpy,bmesh,json
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/francois'
face=bpy._natural_models['courtMale']['face']
matids={i for i,mat in enumerate(face.data.materials) if 'chatain profond' in mat.name}
ids=sorted({i for p in face.data.polygons if p.material_index in matids for i in p.vertices})
assert len(ids)==9000,len(ids)
dead={i for k,i in enumerate(ids) if (k//9)%5 in [0,1]}
bm=bmesh.new();bm.from_mesh(face.data);bm.verts.ensure_lookup_table()
assert len(bm.verts.layers.shape.keys())==16,list(bm.verts.layers.shape.keys())
for v in bm.verts:v.co=face.data.shape_keys.key_blocks['Basis'].data[v.index].co
bmesh.ops.delete(bm,geom=[bm.verts[i] for i in dead],context='VERTS')
bm.to_mesh(face.data);bm.free();face.data.update()
assert all(len(k.data)==len(face.data.vertices) for k in face.data.shape_keys.key_blocks)
code=(ROOT/'scripts/blender-refined-export.py').read_text(encoding='utf-8-sig')
start=code.index("    for ob in m['objects']:");end=code.index('    for ob in joined:\n',start)
code=code[:start]+"    joined=m['objects'];gaps=[.0033]\n"+code[end:]
code=code.replace('artifacts/avatars/refined','artifacts/avatars/francois').replace('renaissance-refined.blend','renaissance-francois.blend')
exec(compile(code,'francois-optimised-export','exec'))
