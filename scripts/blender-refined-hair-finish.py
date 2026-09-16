import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/refined'
scene=bpy._natural_scene;bpy.context.window.scene=scene
code=(ROOT/'scripts/blender-refined-avatars.py').read_text(encoding='utf-8')
exec(compile(code[code.index('def frontal_guides'):code.index('old_clothes=')],'dense-frontal-groom','exec'))
for asset,m in bpy._natural_models.items():
    female=asset=='courtFemale';scale=.95 if female else 1;rig=m['rig'];objects=m['objects'];face=m['face']
    old=next(o for o in objects if 'Coiffure dense en meches' in o.name or 'fibres capillaires denses' in o.name)
    if old.get('hairDynamics'):
        points=[Vector(p)/scale for p in old['hairDynamics']['points']]
    else:
        points=[]
        for i in range(300):
            for j in range(9):
                a=old.data.vertices[i*72+j*2].co;b=old.data.vertices[i*72+j*2+1].co;q=(a+b)*.5
                points.append(Vector((q.x,q.z,-q.y))/scale)
    for p in points:p.z-=.045*smooth((p.y-1.45)/.105)
    guides=[points[i:i+9] for i in range(0,len(points),9)]
    vv=[]
    for v in face.data.vertices:
        p=Vector((v.co.x,v.co.z,-v.co.y))/scale;p.z-=.045*smooth((p.y-1.45)/.105);vv.append(p)
    tree=BVHTree.FromPolygons(vv,[tuple(p.vertices) for p in face.data.polygons])
    guides+=frontal_guides(tree)
    objects.remove(old);bpy.data.objects.remove(old,do_unlink=True)
    dense_ribbons(guides);ob=objects[-1]
    for v in ob.data.vertices:v.co.y-=.045*scale*smooth((v.co.z/scale-1.45)/.105)
    if ob.get('hairDynamics'):
        d=ob['hairDynamics'].to_dict()
        for p in d['points']:p[2]+=.045*scale*smooth((p[1]/scale-1.45)/.105)
        d['headCenter'][2]+=.045*scale;ob['hairDynamics']=d
src=(ROOT/'scripts/blender-refined-export.py').read_text(encoding='utf-8')
a=src.index("    for ob in m['objects']:");b=src.index("    for ob in joined:\n")
src=src[:a]+"    joined=m['objects'];gaps=[.0033]\n"+src[b:]
exec(compile(src,'refined-final-export','exec'))
