import bpy, json, hashlib, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/scene-fbx'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'scene-composee.blend'))
scene=bpy.context.scene
textures=OUT/'Textures';textures.mkdir(exist_ok=True)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1
scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
scene.render.bake.margin=4
records=[];baked=set()
def select(ob):
    bpy.ops.object.select_all(action='DESELECT');ob.hide_set(False);ob.select_set(True);bpy.context.view_layer.objects.active=ob
for ob in list(scene.objects):
    if ob.type!='MESH' or ob.data in baked:continue
    baked.add(ob.data)
    if not any(m and m.use_nodes and any(n.type=='VERTEX_COLOR' for n in m.node_tree.nodes) for m in ob.data.materials):continue
    select(ob)
    # Make materials unique to this shared geometry, then make old UV usage explicit.
    olduv=ob.data.uv_layers.active
    for slot in ob.material_slots:
        slot.material=slot.material.copy();mat=slot.material
        if olduv:
            uvnode=mat.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map=olduv.name
            for n in list(mat.node_tree.nodes):
                if n.type=='TEX_IMAGE' and not n.inputs['Vector'].is_linked:mat.node_tree.links.new(uvnode.outputs['UV'],n.inputs['Vector'])
            for n in mat.node_tree.nodes:
                if n.type=='NORMAL_MAP' and not n.uv_map:n.uv_map=olduv.name
    uv=ob.data.uv_layers.new(name='UnityBakeUV');ob.data.uv_layers.active=uv;uv.active_render=True
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.151917,island_margin=.008)
    bpy.ops.object.mode_set(mode='OBJECT')
    tag=f'Couleurs_{len(records):02d}'
    image=bpy.data.images.new(tag,width=2048,height=2048,alpha=False)
    targets=[]
    for mat in ob.data.materials:
        node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;mat.node_tree.nodes.active=node;targets.append(node)
    bpy.ops.object.bake(type='DIFFUSE',pass_filter={'COLOR'})
    image.filepath_raw=str(textures/(tag+'.png'));image.file_format='PNG';image.save()
    normal=None
    if any(next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Normal'].is_linked for m in ob.data.materials):
        normal=bpy.data.images.new(tag+'_Normal',width=2048,height=2048,alpha=False)
        normal.colorspace_settings.name='Non-Color'
        for node in targets:node.image=normal
        bpy.ops.object.bake(type='NORMAL')
        normal.filepath_raw=str(textures/(tag+'_Normal.png'));normal.file_format='PNG';normal.save()
    # glTF color/normal source graphs are replaced by standard image sockets.
    for mat,node in zip(ob.data.materials,targets):
        shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        node.image=image
        mat.node_tree.links.new(node.outputs['Color'],shader.inputs['Base Color'])
        if normal:
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=normal
            norm=mat.node_tree.nodes.new('ShaderNodeNormalMap');norm.uv_map='UnityBakeUV'
            mat.node_tree.links.new(tex.outputs['Color'],norm.inputs['Color']);mat.node_tree.links.new(norm.outputs['Normal'],shader.inputs['Normal'])
        # Discard obsolete nodes to prevent FBX from selecting the old image.
        output=next(n for n in mat.node_tree.nodes if n.type=='OUTPUT_MATERIAL')
        reachable=set()
        def collect(n):
            if n in reachable:return
            reachable.add(n)
            for socket in n.inputs:
                for link in socket.links:collect(link.from_node)
        collect(output)
        for n in list(mat.node_tree.nodes):
            if n not in reachable:mat.node_tree.nodes.remove(n)
    # FBX/Unity's default shader uses UV0. Old UVs are no longer needed on these meshes.
    for layer in list(ob.data.uv_layers):
        if layer.name!='UnityBakeUV':ob.data.uv_layers.remove(layer)
    records.append({'mesh':ob.name,'color':image.name,'normal':normal.name if normal else None})
    print('BAKED_VERTEX_COLORS',len(records),ob.name,flush=True)

materials=set(m for o in scene.objects if o.type=='MESH' for m in o.data.materials if m)
saved=set()
for mat in materials:
    for node in mat.node_tree.nodes:
        if node.type!='TEX_IMAGE' or not node.image:continue
        image=node.image
        if image in saved:continue
        saved.add(image)
        filename=re.sub(r'[^A-Za-z0-9_.-]','_',image.name)
        if not filename.lower().endswith('.png'):filename+='.png'
        image.filepath_raw=str(textures/filename);image.file_format='PNG';image.save()
        if image.packed_file:image.unpack(method='REMOVE')

def export(filename, objects):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:ob.hide_set(False);ob.select_set(True)
    bpy.context.view_layer.objects.active=next(o for o in objects if o.type=='MESH')
    path=OUT/filename
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'EMPTY','MESH','LIGHT'},
        use_mesh_modifiers=False,add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y',
        apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',use_space_transform=True,bake_space_transform=False,
        path_mode='COPY',embed_textures=True,use_custom_props=True)
    return {'file':filename,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'meshes':len([o for o in objects if o.type=='MESH'])}

inside=bpy.data.objects['Interieur_Chateau']
exports=[export('scene-complete.fbx',list(scene.objects)),export('interieur-chateau.fbx',[inside]+list(inside.children_recursive))]
# The editable source uses portable relative PNG paths.
for image in saved:image.filepath=bpy.path.relpath(image.filepath,start=str(OUT))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'scene-composee.blend'),compress=True)
(OUT/'export-report.json').write_text(json.dumps({'exports':exports,'bakedVertexColors':records,'textures':len(saved)},indent=2),encoding='utf-8')
print('SCENE_FBX_EXPORT_COMPLETE',json.dumps(exports),flush=True)
