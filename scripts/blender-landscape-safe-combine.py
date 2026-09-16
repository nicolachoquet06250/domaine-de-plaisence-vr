def combine(objects,name):
 # Merge explicitly: avoid the Blender operator joining linked mesh instances.
 verts=[];faces=[];material_ids=[];uvs=[];materials=[]
 for obj in objects:
  data=obj.data;offset=len(verts);world=obj.matrix_world.copy()
  verts.extend(tuple(world@v.co) for v in data.vertices)
  mapping=[]
  for mat in data.materials:
   if mat not in materials:materials.append(mat)
   mapping.append(materials.index(mat))
  uv=data.uv_layers.active
  for poly in data.polygons:
   faces.append(tuple(offset+i for i in poly.vertices))
   material_ids.append(mapping[poly.material_index] if mapping else 0)
   uvs.extend(tuple(uv.data[i].uv) if uv else (0,0) for i in poly.loop_indices)
 data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces)
 for mat in materials:data.materials.append(mat)
 for poly,mat in zip(data.polygons,material_ids):poly.material_index=mat;poly.use_smooth=True
 uv=data.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',[v for pair in uvs for v in pair]);data.update()
 obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj)
 for old in objects:bpy.data.objects.remove(old,do_unlink=True)
 return obj

print('Safe linked geometry merge installed')
