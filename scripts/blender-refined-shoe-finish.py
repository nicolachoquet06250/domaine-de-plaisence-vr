import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/refined'
scene=bpy._natural_scene;bpy.context.window.scene=scene
m=bpy._natural_models['courtFemale'];scale=.95
for ob in m['objects']:
    if 'cuir prune' not in ob.name:continue
    # The upper is the largest connected component; straps and rolled edges are separate.
    neighbors={i:[] for i in range(len(ob.data.vertices))}
    for e in ob.data.edges:
        a,b=e.vertices;neighbors[a].append(b);neighbors[b].append(a)
    seen=set();parts=[]
    for i in neighbors:
        if i in seen:continue
        stack=[i];seen.add(i);part=set()
        while stack:
            j=stack.pop();part.add(j)
            for k in neighbors[j]:
                if k not in seen:seen.add(k);stack.append(k)
        parts.append(part)
    upper=max(parts,key=len);tree=BVHTree.FromPolygons([v.co.copy() for v in ob.data.vertices],[tuple(p.vertices) for p in ob.data.polygons if all(i in upper for i in p.vertices)])
    cx=sum(ob.data.vertices[i].co.x for i in upper)/len(upper);cx=.095 if cx>0 else -.095
    for v in ob.data.vertices:
        if v.index in upper or abs(v.co.x-cx)<.030*scale or -v.co.y<0 or v.co.z<.070*scale:continue
        v.co.x=cx+(.028*scale if v.co.x>cx else -.028*scale)
        hit=tree.ray_cast(Vector((v.co.x,v.co.y,.35*scale)),Vector((0,0,-1)))
        if hit[0] is not None:v.co.z=hit[0].z+.0015*scale
src=(ROOT/'scripts/blender-refined-export.py').read_text(encoding='utf-8');a=src.index("    for ob in m['objects']:");b=src.index('    for ob in joined:\n')
exec(compile(src[:a]+"    joined=m['objects'];gaps=[.0033]\n"+src[b:],'final-shoe-export','exec'))
