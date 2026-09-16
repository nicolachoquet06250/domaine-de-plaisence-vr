import bpy,json
from mathutils import Vector
out={}
for asset,m in bpy._natural_models.items():
    report=[]
    for o in m['objects']:
        if any(s in o.name for s in ['Visage','Barbe','Cuir','Sourcil','helper']):
            ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
            report.append({'name':o.name,'z':[min(v.co.z for v in o.data.vertices),max(v.co.z for v in o.data.vertices)],'evalZ':[min(v.co.z for v in ev.data.vertices),max(v.co.z for v in ev.data.vertices)],'keys':[(k.name,k.value) for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],'mats':[(mat.name,sum(p.material_index==i for p in o.data.polygons)) for i,mat in enumerate(o.data.materials)]})
    out[asset]=report
print(json.dumps(out))
