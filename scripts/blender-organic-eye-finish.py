import bpy,bmesh
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/organic'
scene=bpy._natural_scene;bpy.context.window.scene=scene
with bpy.data.libraries.load(str(OUT/'renaissance-organic-work.blend'),link=False) as (a,b):
    b.objects=[n for n in a.objects if 'Iris anatomique Head' in n]
for asset,m in bpy._natural_models.items():
    rig=m['rig'];rig.location=(0,0,0)
    remove=[o for o in m['objects'] if 'Head pupille et cils' in o.name]
    m['objects']=[o for o in m['objects'] if o not in remove]
    for ob in remove:bpy.data.objects.remove(ob,do_unlink=True)
    for ob in b.objects:
        if not ob.name.startswith(asset):continue
        scene.collection.objects.link(ob);ob.parent=rig
        for mod in ob.modifiers:
            if mod.type=='ARMATURE':mod.object=rig
        m['objects'].append(ob)
    ob=m['face'];bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table()
    scale=.95 if asset=='courtFemale' else 1
    border=[v for v in bm.verts if v.is_boundary and v.co.z<1.525*scale]
    before={v.index:v.co.copy() for v in border}
    for _ in range(6):
        positions={v:sum((e.other_vert(v).co for e in v.link_edges if e.is_boundary),Vector())/max(1,sum(e.is_boundary for e in v.link_edges)) for v in border}
        for v,p in positions.items():v.co=v.co.lerp(p,.6)
    changes={v.index:v.co-before[v.index] for v in border};bm.free()
    for key in ob.data.shape_keys.key_blocks:
        for i,d in changes.items():key.data[i].co+=d
    ob.data.update()
    # Remove a small number of disconnected fixed bun fibres to pay for intact irises.
    if asset=='courtFemale':
        for o in m['objects']:
            if 'Head reflets chatains' not in o.name:continue
            bm=bmesh.new();bm.from_mesh(o.data);seen=set();dead=[];count=0
            for v in bm.verts:
                if v in seen:continue
                todo=[v];seen.add(v);strand=[]
                while todo:
                    q=todo.pop();strand.append(q)
                    for e in q.link_edges:
                        n=e.other_vert(q)
                        if n not in seen:seen.add(n);todo.append(n)
                if count%12==0:dead.extend(strand)
                count+=1
            bmesh.ops.delete(bm,geom=dead,context='VERTS');bm.to_mesh(o.data);bm.free()
src=(ROOT/'scripts/blender-organic-export.py').read_text(encoding='utf-8');a=src.index('    facial=');z=src.index('    for ob in joined:')
exec(compile(src[:a]+"    joined=model['objects']\n"+src[z:],'final-eyes-export','exec'))
