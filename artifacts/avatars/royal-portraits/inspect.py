import bpy,json
from pathlib import Path
ROOT=Path(r'C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'artifacts/avatars/moustache/renaissance-moustache.blend'))
data={}
for rig in bpy.context.scene.objects:
    if rig.type!='ARMATURE':continue
    data[rig.name]={'location':list(rig.location),'rotation':list(rig.rotation_euler),'scale':list(rig.scale),'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(r) for r in b.matrix_local]} for b in rig.data.bones}}
(ROOT/'artifacts/avatars/royal-portraits/rig-inspection.json').write_text(json.dumps(data,indent=2))
print('INSPECTION_COMPLETE')
for o in bpy.context.scene.objects:
    if o.type!='MESH' or not o.name.startswith('courtMale'):continue
    print('MESH_MATERIALS',o.name,[(m.name if m else None) for m in o.data.materials])
    if 'Costume' in o.name:
        for m in o.data.materials:
            if m and ('or' in m.name.lower() or 'gold' in m.name.lower()):
                ids={i for p in o.data.polygons if o.data.materials[p.material_index]==m for i in p.vertices}
                verts=[o.data.vertices[i] for i in ids if .20<abs(o.data.vertices[i].co.x)<.4 and .9<o.data.vertices[i].co.z<1.3]
                print('GOLD_ARM',m.name,[(list(v.co),[(o.vertex_groups[g.group].name,g.weight) for g in v.groups]) for v in verts[::max(1,len(verts)//8)]])
