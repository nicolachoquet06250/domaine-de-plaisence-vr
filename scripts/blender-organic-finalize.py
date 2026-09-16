import bpy,bmesh
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
scene=bpy._natural_scene;bpy.context.window.scene=scene
for ob in bpy._natural_models['courtFemale']['objects']:
    if 'Head reflets chatains' in ob.name:
        bm=bmesh.new();bm.from_mesh(ob.data);seen=set();remove=[];component=0
        for v in bm.verts:
            if v in seen:continue
            todo=[v];seen.add(v);strand=[]
            while todo:
                q=todo.pop();strand.append(q)
                for e in q.link_edges:
                    n=e.other_vert(q)
                    if n not in seen:seen.add(n);todo.append(n)
            if component%4==0:remove.extend(strand)
            component+=1
        bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(ob.data);bm.free()
src=(ROOT/'scripts/blender-organic-export.py').read_text(encoding='utf-8')
a=src.index('    facial=');b=src.index('    for ob in joined:')
src=src[:a]+"    joined=model['objects']\n"+src[b:]
exec(compile(src,'organic-final-export','exec'))
