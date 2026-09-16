import bpy,json
out={}
for a,m in bpy._natural_models.items():
    rows=[]
    for o in m['objects']:
        o.data.calc_loop_triangles();rows.append([o.name,len(o.data.loop_triangles),bool(o.data.shape_keys),bool(o.get('hairDynamics'))])
    out[a]=sorted(rows,key=lambda r:-r[1])
print(json.dumps(out))
