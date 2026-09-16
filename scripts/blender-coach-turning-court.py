"""Local-only Blender MCP: rounded gravel forecourt for the broad carriage turn."""
import bpy, bmesh, json, math
import numpy as np
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
scene=bpy.data.scenes.new('Aire de retournement du carrosse');bpy.context.window.scene=scene
bpy.ops.import_scene.gltf(filepath=str(ROOT/'public/gltf/garden/pathLong.glb'))
source=next(o for o in scene.objects if o.type=='MESH');material=source.data.materials[0]
coords=[];uv=[]
for face in source.data.polygons:
 if face.normal.z>.8:
  for li in face.loop_indices:
   p=source.matrix_world@source.data.vertices[source.data.loops[li].vertex_index].co
   coords.append([p.x*7,-p.y*54,1]);uv.append(tuple(source.data.uv_layers.active.data[li].uv))
mapping=np.linalg.lstsq(np.array(coords),np.array(uv),rcond=None)[0]
verts=[(104.5,54.7,.052)]+[(104.5+10.5*math.cos(i*math.tau/96),54.7+9.8*math.sin(i*math.tau/96),.052) for i in range(96)]
faces=[(0,1+i,1+(i+1)%96) for i in range(96)]
mesh=bpy.data.meshes.new('Gravier aire de demi tour');mesh.from_pydata(verts,[],faces);mesh.materials.append(material)
layer=mesh.uv_layers.new(name='UVMap')
for poly in mesh.polygons:
 for li in poly.loop_indices:
  p=mesh.vertices[mesh.loops[li].vertex_index].co;layer.data[li].uv=tuple(np.array([p.x,-p.y,1])@mapping)
obj=bpy.data.objects.new('Aire de retournement',mesh);scene.collection.objects.link(obj)
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/gltf/arrival-coach/turningCourt.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_image_format='AUTO')
directory=ROOT/'artifacts/coach-journey';directory.mkdir(exist_ok=True,parents=True)
bpy.data.libraries.write(str(directory/'aire-retournement.blend'),{scene},fake_user=True,compress=True)
print(json.dumps({'triangles':96,'bounds':[94,115,-64.5,-44.9],'height':.052,'material':material.name}))
