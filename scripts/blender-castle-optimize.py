# Small metallic fillets carry most furniture triangles. Decimate only this
# smooth ornament batch: architecture, flat inlay, porcelain and collisions stay exact.
for obj in cobjects['palaceInterior']:
    if obj.type!='MESH' or not any(p.use_smooth for p in obj.data.polygons): continue
    if not any(m==cgold for m in obj.data.materials): continue
    bpy.context.view_layer.objects.active=obj
    modifier=obj.modifiers.new('Optimisation des petits ornements dores','DECIMATE')
    modifier.ratio=.88; modifier.use_collapse_triangulate=True
    bpy.ops.object.modifier_apply(modifier=modifier.name)
cstats['palaceInterior']=cexport('palaceInterior',cobjects['palaceInterior'])
(CEVID/'asset-stats.json').write_text(json.dumps(cstats,indent=2))
print(json.dumps(cstats['palaceInterior']))
