"""Compose the authored visit in Blender, with one separate interior mesh."""
import bpy, json, math, hashlib, re
from pathlib import Path
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/scene-fbx'
INPUT=json.loads((OUT/'composition-input.json').read_text(encoding='utf-8'))
C=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
def matrix(values): return Matrix([values[i:i+4] for i in range(0,16,4)]).transposed()
def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects: ob.hide_set(False);ob.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
def empty(name):
    ob=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(ob);return ob

bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.name='Domaine de Plaisance - Scene composee'
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1
root=empty('Scene_Complete')
exterior=empty('Exterieur_Domaine');exterior.parent=root
interior_parts=[];interior_lights=[];placed=[];prototypes={};material_report=[]
for aid,spec in INPUT['assets'].items():
    if 'path' not in spec:continue
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/spec['path']))
    imported=list(set(bpy.data.objects)-before)
    scene.frame_set(0);bpy.context.view_layer.update()
    meshes=[]
    for ob in imported:
        if ob.type!='MESH':continue
        transform=ob.matrix_world.copy()
        # Export a static modeled scene, with evaluated geometry at frame zero.
        evaluated=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get())
        meshes.append((ob.name,mesh,transform))
    prototypes[aid]=meshes
    for ob in imported:bpy.data.objects.remove(ob,do_unlink=True)
    print('LOADED',aid,len(meshes),flush=True)

for node in INPUT['nodes']:
    world=C@matrix(node['matrix'])@C.inverted()
    if 'light' in node:
        p=node['light'];kind='SUN' if p['type']=='DirectionalLight' else 'POINT'
        data=bpy.data.lights.new(node['id'],kind)
        data.color=p.get('color',[1,1,1])[:3]
        data.energy=p.get('intensity',1)*(4*math.pi if kind=='POINT' else 1)
        ob=bpy.data.objects.new(node['id'],data);scene.collection.objects.link(ob)
        # Three light local -Z is converted to Blender local -Z.
        ob.matrix_world=C@matrix(node['matrix'])
        ob.parent=exterior if not node['interior'] else root
        if node['interior']:interior_lights.append(ob)
        continue
    aid=node['asset'];spec=INPUT['assets'][aid]
    group=empty(node['id'].replace('/','__'));group.parent=exterior;group.matrix_world=world
    obs=[]
    if 'path' in spec:
        for name,mesh,local in prototypes[aid]:
            ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob)
            ob.parent=group;ob.matrix_world=world@local;obs.append(ob)
    else:
        for part in spec['meshes']:
            positions=part['positions'];verts=[positions[i:i+3] for i in range(0,len(positions),3)]
            indices=part['indices'] or list(range(len(verts)))
            faces=[indices[i:i+3] for i in range(0,len(indices),3)]
            mesh=bpy.data.meshes.new(part['name']);mesh.from_pydata(verts,[],faces);mesh.update()
            if part['uv']:
                uv=mesh.uv_layers.new(name='UVMap')
                for loop in mesh.loops:uv.data[loop.index].uv=part['uv'][loop.vertex_index*2:loop.vertex_index*2+2]
            mat=bpy.data.materials.new(aid);mat.use_nodes=True
            shader=mat.node_tree.nodes.get('Principled BSDF');p=part['material']
            shader.inputs['Base Color'].default_value=(*p['color'],1)
            shader.inputs['Metallic'].default_value=p['metalness'];shader.inputs['Roughness'].default_value=p['roughness']
            shader.inputs['Alpha'].default_value=p['opacity']
            mat.diffuse_color=(*p['color'],p['opacity'])
            if p['unlit'] or p['shader']:
                shader.inputs['Emission Color'].default_value=(*p['color'],1)
                shader.inputs['Emission Strength'].default_value=1
            # Procedural WebXR flames become a static texture silhouette.
            if p['shader']:
                import numpy as np
                size=256;y,x=np.mgrid[0:size,0:size].astype(float)/(size-1)
                sway=np.sin(y*7-2.4)*.10*y
                density=.43*np.maximum(0,1-y)**.85-np.abs(x-.5+sway)
                alpha=np.clip((density+.035)/.1,0,1)*np.clip(y/.1,0,1)*np.clip((1-y)/.27,0,1)
                pixels=np.stack((np.ones_like(x),.19+np.clip(density,0,.3)*2,np.full_like(x,.009),alpha*.68),axis=-1).astype('float32')
                image=bpy.data.images.get('Flammes_Instantane') or bpy.data.images.new('Flammes_Instantane',width=size,height=size,alpha=True)
                image.pixels.foreach_set(pixels.ravel());image.pack()
                tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
                mat.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color']);mat.node_tree.links.new(tex.outputs['Color'],shader.inputs['Emission Color']);mat.node_tree.links.new(tex.outputs['Alpha'],shader.inputs['Alpha'])
            mesh.materials.append(mat)
            ob=bpy.data.objects.new(part['name'],mesh);scene.collection.objects.link(ob)
            ob.parent=group;ob.matrix_world=world@C@matrix(part['matrix']);obs.append(ob)
    for ob in obs:
        ob['source_node']=node['id'];ob['source_asset']=aid
    if node['interior']:
        interior_parts.extend(obs)
    placed.append({'id':node['id'],'asset':aid,'interior':node['interior'],'meshes':len(obs)})

bpy.context.view_layer.update()
# Keep the castle's world-space placement in both exports for exact alignment.
select(interior_parts)
bpy.ops.object.join()
inside=bpy.context.object;inside.name='Interieur_Chateau';inside.data.name='Interieur_Chateau_Geometrie'
world=inside.matrix_world.copy();inside.parent=root;inside.matrix_world=world
for lamp in interior_lights:
    world=lamp.matrix_world.copy();lamp.parent=inside;lamp.matrix_world=world
for ob in list(scene.objects):
    if ob.type=='EMPTY' and not ob.children and ob not in [root,exterior]:bpy.data.objects.remove(ob,do_unlink=True)

meshes=[o for o in scene.objects if o.type=='MESH']
for ob in meshes:ob.data.calc_loop_triangles()
for mat in bpy.data.materials:
    if not mat.use_nodes:continue
    material_report.append({'name':mat.name,'vertexColor':any(n.type=='VERTEX_COLOR' for n in mat.node_tree.nodes),
        'nodes':[n.type for n in mat.node_tree.nodes], 'textures':[n.image.name for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]})
report={'source':INPUT['source'],'sourceSha256':INPUT['sourceSha256'],'placements':placed,'excluded':INPUT['excluded'],
        'meshes':len(meshes),'triangles':sum(len(o.data.loop_triangles) for o in meshes),
        'interiorTriangles':len(inside.data.loop_triangles),'interiorMesh':'Interieur_Chateau',
        'interiorNodes':[p['id'] for p in placed if p['interior']],'materials':material_report,
        'limitations':['Static geometry at frame 0; application scripts and UI are not FBX geometry.', 'Procedural flames use a static texture approximation; mirror reflection requires Unity setup.']}
(OUT/'composition-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'scene-composee.blend'),compress=True)
print('COMPOSITION_SAVED',json.dumps({k:report[k] for k in ['meshes','triangles','interiorTriangles']}),flush=True)
