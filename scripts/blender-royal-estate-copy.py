"""Refresh the distant exterior without old masonry boundaries; clear gateway grass."""
import bpy,bmesh,json
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
OUT=ROOT/'public/gltf/royal-enclosure';EVID=ROOT/'artifacts/royal-enclosure'
scene=bpy.data.scenes.new('Copie exterieure sans anciens murets');bpy.context.window.scene=scene
exec(compile((ROOT/'scripts/blender-landscape-safe-combine.py').read_text(),'safe-combine','exec'))
def clear_grass(obj):
 if 'Bent grass' not in obj.name:return
 bm=bmesh.new();bm.from_mesh(obj.data);remove=[]
 for f in bm.faces:
  p=obj.matrix_world@f.calc_center_median()
  if abs(p.x)<3.6 and -31.1<p.y<-26.85:remove.append(f)
 bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(obj.data);bm.free();obj.data.update()
def export_copy(name,objects):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_image_format='AUTO')

# Updated lawn is shared by the playable scene and the distant copy.
previous=set(scene.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'public/gltf/vegetation/estateLawnRelief.glb'));bpy.context.view_layer.update()
loaded=[o for o in scene.objects if o not in previous]
for obj in loaded:
 if obj.type=='MESH':clear_grass(obj)
export_copy('estateLawnReliefGate',[o for o in loaded if o.type=='MESH'])
for o in loaded:bpy.data.objects.remove(o,do_unlink=True)

C=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
spec=json.loads((ROOT/'artifacts/arrival-landscape/exterior-placements.json').read_text());cache={};exterior=[]
for placement in spec['placements']:
 asset=placement['asset']
 if asset=='gardenBorder':continue
 if asset not in cache:
  file=OUT/'estateLawnReliefGate.glb' if asset=='ground' else ROOT/placement['path']
  previous=set(scene.objects);bpy.ops.import_scene.gltf(filepath=str(file));bpy.context.view_layer.update();loaded=[o for o in scene.objects if o not in previous];prototypes=[]
  for o in loaded:
   if o.type!='MESH':continue
   bpy.context.view_layer.objects.active=o
   if len(o.data.polygons)>200:
    mod=o.modifiers.new('Details lointains','DECIMATE');mod.ratio=.4 if asset=='palace' else .17 if asset in ['parterre','ground','cypress'] else .3;bpy.ops.object.modifier_apply(modifier=mod.name)
   if asset=='palaceGlass':
    for material in o.data.materials:
     if material and material.use_nodes:
      p=next((n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
      if p:p.inputs['Transmission Weight'].default_value=0;p.inputs['Alpha'].default_value=1;p.inputs['Base Color'].default_value=(.08,.13,.15,1);p.inputs['Metallic'].default_value=.5;p.inputs['Roughness'].default_value=.25
   prototypes.append((o.data,o.matrix_world.copy()))
  cache[asset]=prototypes
  for o in loaded:bpy.data.objects.remove(o,do_unlink=True)
 m=placement['matrix'];world=C@Matrix(tuple(tuple(m[col*4+row] for col in range(4)) for row in range(4)))@C.inverted()
 for data,local in cache[asset]:
  o=bpy.data.objects.new(placement['id'],data);scene.collection.objects.link(o);o.matrix_world=world@local;exterior.append(o)
estate=combine(exterior,'Exterieurs sans anciens murets');estate.data.validate();export_copy('estateExterior',[estate])
bpy.data.libraries.write(str(EVID/'exterieurs-sans-murets.blend'),{scene},fake_user=True,compress=True)
print('Exterior replaced without old walls; shared lawn gateway cleared')
