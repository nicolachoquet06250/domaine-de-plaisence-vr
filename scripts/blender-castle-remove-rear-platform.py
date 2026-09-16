"""Remove only the disconnected rear upper slab; keep the usable 2.84 m landing."""
import bpy,bmesh,json
from pathlib import Path
root=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
with bpy.data.libraries.load(str(root/'artifacts/castle/chateau-plaisance-coiffures.blend'),link=False) as (source,target):
    target.scenes=[next(n for n in source.scenes if n.startswith('Chateau - Architecture et interieur'))]
scene=target.scenes[0];bpy.context.window.scene=scene
removed=[];objects=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('palaceInterior')]
assert objects,'Editable interior meshes missing'
for obj in objects:
    bm=bmesh.new();bm.from_mesh(obj.data);seen=set();erase=[]
    for seed in bm.verts:
        if seed in seen:continue
        todo=[seed];seen.add(seed);island=[]
        while todo:
            v=todo.pop();island.append(v)
            for edge in v.link_edges:
                other=edge.other_vert(v)
                if other not in seen:seen.add(other);todo.append(other)
        coords=[obj.matrix_world@v.co for v in island]
        lo=[min(v[i] for v in coords) for i in range(3)];hi=[max(v[i] for v in coords) for i in range(3)]
        if all(abs(a-b)<.002 for a,b in zip(lo+hi,[-4.65,4.0,4.78,4.65,5.78,5.04])):
            removed.append({'object':obj.name,'vertices':len(island),'boundsBlender':[lo,hi]});erase.extend(island)
    if erase:bmesh.ops.delete(bm,geom=erase,context='VERTS');bm.to_mesh(obj.data);obj.data.update()
    bm.free()
assert len(removed)==1,f'Expected exactly one disconnected slab, found {removed}'
bpy.ops.object.select_all(action='DESELECT')
for obj in objects:obj.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.export_scene.gltf(filepath=str(root/'public/gltf/castle/palaceInterior.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_yup=True,export_animations=False,export_materials='EXPORT',export_image_format='JPEG',export_jpeg_quality=90)
path=root/'src/scene-assets/castle-collision-data.json';solids=json.loads(path.read_text());kept=[s for s in solids if not(s.get('position')==[0,4.91,-4.89] and s.get('size')==[9.3,.26,1.78])]
assert len(solids)-len(kept)==1,'Expected matching slab collision'
path.write_text(json.dumps(kept,separators=(',',':')))
bpy.ops.wm.save_as_mainfile(filepath=str(root/'artifacts/castle/chateau-plaisance-escalier.blend'),compress=True)
(root/'artifacts/castle/platform-removal.json').write_text(json.dumps({'removed':removed,'removedColliders':1,'keptIntermediateLandingY':2.84},indent=2))
print(json.dumps({'removed':removed,'removedColliders':1}))
