import bpy, bmesh, json, re
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/unity-interactions';OUT.mkdir(exist_ok=True)
def export(name, obs, animated=False):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.hide_set(False);o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,
        object_types={'MESH','EMPTY','ARMATURE'},use_mesh_modifiers=False,add_leaf_bones=False,
        bake_anim=animated,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,
        bake_anim_simplify_factor=0,axis_forward='-Z',axis_up='Y',apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_UNITS',path_mode='AUTO')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'artifacts/scene-fbx/scene-composee.blend'))
inside=bpy.data.objects['Interieur_Chateau'];door=bpy.data.objects['castle__door-entrance']
leaves=[o for o in door.children if o.type=='MESH'];mats=set(m for o in leaves for m in o.data.materials)
bm=bmesh.new();bm.from_mesh(inside.data)
faces=[f for f in bm.faces if inside.data.materials[f.material_index] in mats]
removed=len(faces);assert removed>0
bmesh.ops.delete(bm,geom=faces,context='FACES');bm.to_mesh(inside.data);bm.free()
export('interieur-sans-portes',[inside])
inverse=door.matrix_world.inverted()
for o in leaves:
    local=inverse@o.matrix_world;o.parent=None;o.matrix_world=local
export('portes-mobiles',leaves)
report={'removedInteriorDoorFaces':removed,'assets':[]}
for name,source in [('eau','estate/water.glb'),('jet-central','estate/centralJet.glb'),('jet-lateral','estate/lateralJet.glb'),('carrosse','arrival-coach/royalCoachAnimated.glb')]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'public/gltf'/source))
    scene=bpy.context.scene;scene.render.fps=30;scene.frame_start=0
    objects=list(scene.objects)
    # Retain original shape keys, armatures and mesh colors. Unity samples these
    # directly; the full-scene FBX remains an untouched static source.
    material_specs=[]
    for m in bpy.data.materials:
        if not m.use_nodes:continue
        s=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
        if not s:continue
        material_specs.append({'name':m.name,'color':list(s.inputs['Base Color'].default_value),
            'metallic':s.inputs['Metallic'].default_value,'roughness':s.inputs['Roughness'].default_value,
            'vertexColor':any(n.type=='VERTEX_COLOR' for n in m.node_tree.nodes)})
    if name=='carrosse':
        for clip,end in [('HorseIdle',90),('HorseWalk',36)]:
            for o in objects:
                ad=o.animation_data
                if not ad:continue
                ad.action=None
                for t in ad.nla_tracks:t.mute=not t.name.startswith(clip)
            scene.frame_end=end;scene.frame_set(0)
            export(name+'-'+clip,objects,True)
    else:
        scene.frame_set(0);export(name,objects)
    report['assets'].append({'name':name,'materials':material_specs,'shapes':[(o.name,len(o.data.shape_keys.key_blocks)-1) for o in objects if o.type=='MESH' and o.data.shape_keys]})
(OUT/'assets-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('INTERACTIONS_EXPORTED',removed,flush=True)
