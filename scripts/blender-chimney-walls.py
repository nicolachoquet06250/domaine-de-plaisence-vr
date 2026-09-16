"""Targeted edit of the latest castle: four central end-wall windows become masonry."""
import bpy, bmesh, json, shutil
from pathlib import Path

root=Path(r'C:\Users\nicol\Documents\workspaces\vr-workspace\test-meta-web-sdk-update')
source_path=root/'artifacts/castle/chateau-plaisance-escalier.blend'
if bpy.data.filepath and Path(bpy.data.filepath).resolve()==source_path.resolve():
    copy_path=root/'artifacts/castle/chimney-walls-source.blend'
    shutil.copyfile(source_path,copy_path);source_path=copy_path
with bpy.data.libraries.load(str(source_path),link=False) as (source,target):
    target.scenes=[next(n for n in source.scenes if n.startswith('Chateau - Architecture et interieur'))]
scene=target.scenes[0];bpy.context.window.scene=scene
exterior=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('palace ') ]
glazing=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('palaceGlass')]
interior=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('palaceInterior')]
assert exterior and glazing and interior
stone=next(m for o in exterior for m in o.data.materials if 'Calcaire de taille' in m.name)
plaster=next(m for o in interior for m in o.data.materials if 'Stuc creme' in m.name)
report={'removed':[], 'glassOpeningsRemoved':0}

for obj in exterior+glazing:
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
        # Blender Z is height, Y is the negative application Z coordinate.
        lo=[min(v[i] for v in coords) for i in range(3)];hi=[max(v[i] for v in coords) for i in range(3)]
        on_end=(lo[0]>20.69 or hi[0]<-20.69)
        central=lo[1]>-1.31 and hi[1]<1.31
        within_window=any(lo[2]>low and hi[2]<high for low,high in [(1.04,4.92),(5.64,9.62)])
        if on_end and central and within_window:
            erase.extend(island);report['removed'].append({'object':obj.name,'bounds':[lo,hi],'vertices':len(island)})
            if obj in glazing:report['glassOpeningsRemoved']+=1
    if erase:bmesh.ops.delete(bm,geom=erase,context='VERTS');bm.to_mesh(obj.data);obj.data.update()
    bm.free()
assert report['glassOpeningsRemoved']==4,report['glassOpeningsRemoved']

def box(name,center,size,material):
    x,y,z=center;w,h,d=size
    verts=[(x+a*w/2,-(z+c*d/2),y+b*h/2) for a,b,c in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    uv=mesh.uv_layers.new(name='UVMap')
    for p in mesh.polygons:
        for li in p.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv=(v.x*.5,v.y*.5) if abs(p.normal.z)>.6 else ((v.x*.5,v.z*.5) if abs(p.normal.y)>.6 else (v.y*.5,v.z*.5))
    mesh.materials.append(material);obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj);return obj

for side in [-1,1]:
    for bottom,height in [(1.35,2.95),(5.95,3.05)]:
        exterior.append(box('palace Maconnerie baie condamnee',(side*21,bottom+height/2,0),(.44,height,1.7),stone))
    # Back of the gold frames touches plaster at x=19.965; the fireplace jambs
    # overlap the breast. This also hides the obsolete polished-metal mirror back.
    interior.append(box('palaceInterior Dosseret cheminees',(side*20.3825,6.19,0),(.835,11.10,2.60),plaster))

for asset,objects in [('palace',exterior),('palaceGlass',glazing),('palaceInterior',interior)]:
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.gltf(filepath=str(root/f'public/gltf/castle/{asset}.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_yup=True,export_animations=False,export_materials='EXPORT',export_image_format='JPEG',export_jpeg_quality=90)

collision=root/'src/scene-assets/castle-collision-data.json';solids=json.loads(collision.read_text())
solids=[s for s in solids if not(s.get('size')==[.66,11.10,2.60] and abs(s.get('position',[0])[0])==20.47)]
for side in [-1,1]:
    block={'kind':'box','position':[side*20.3825,6.19,0],'size':[.835,11.10,2.60]}
    if block not in solids:solids.append(block)
collision.write_text(json.dumps(solids,separators=(',',':')))
bpy.data.libraries.write(str(root/'artifacts/castle/chateau-plaisance-cheminees-murs.blend'),{scene},compress=True)
(root/'artifacts/castle/chimney-wall-edit.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'removedGlassOpenings':report['glassOpeningsRemoved'],'removedMeshIslands':len(report['removed']),'solidChimneyBreasts':2}))
