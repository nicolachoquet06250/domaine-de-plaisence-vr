# Blender's localized cube UV name differed from UVMap on custom meshes.
# Consolidate the two layers of the already merged review models.
for parts in gparts.values():
    for obj in parts:
        layers=obj.data.uv_layers
        if len(layers)>1:
            first=layers[0]; second=layers[1]
            for p in obj.data.polygons:
                if all(first.data[i].uv.length_squared<1e-12 for i in p.loop_indices):
                    for i in p.loop_indices: first.data[i].uv=second.data[i].uv
            layers.remove(second)
        layers[0].name='UVMap'; layers.active_index=0
for mat in [grass,gravel,limestone,hedge_mat,bark_mat,soil]: mat.use_backface_culling=True
print('Unified UV maps; foliage veins and leaf-cluster normals now export on the correct coordinates.')
