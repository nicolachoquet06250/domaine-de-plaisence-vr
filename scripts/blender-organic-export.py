"""Export organic meshes; preserve all facial morphs, particle bindings and native grooms."""
import bpy,json
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/organic'
scene=bpy._natural_scene;bpy.context.window.scene=scene
reports={}
for asset,model in bpy._natural_models.items():
    rig=model['rig'];rig.location=(0,0,0);rig.data.pose_position='REST'
    facial=[o for o in model['objects'] if o.data.shape_keys]
    bpy.ops.object.select_all(action='DESELECT')
    for ob in facial:
        ob.select_set(True)
        for key in ob.data.shape_keys.key_blocks[1:]:key.value=0
    face=model['face'];bpy.context.view_layer.objects.active=face
    bpy.ops.object.join()
    model['objects']=[o for o in model['objects'] if o not in facial]+[face]
    for ob in model['objects']:
        if ob.data.shape_keys or (ob.get('strandSurface') and 'Fibres chignon' not in ob.name) or 'Mains' in ob.name:continue
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
        mod=ob.modifiers.new('Optimisation','DECIMATE');mod.ratio=.65 if 'Fibres chignon' in ob.name else .30;mod.use_collapse_triangulate=True
        bpy.ops.object.modifier_move_up(modifier=mod.name);bpy.ops.object.modifier_apply(modifier=mod.name)
    groups={};joined=[]
    for ob in model['objects']:
        if ob.data.shape_keys or ob.get('hairDynamics'):joined.append(ob);continue
        k=(bool(ob.get('firstPersonHidden')),tuple(m.name for m in ob.data.materials))
        groups.setdefault(k,[]).append(ob)
    for (hidden,mats),batch in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for ob in batch:ob.select_set(True)
        active=batch[0];bpy.context.view_layer.objects.active=active
        if len(batch)>1:bpy.ops.object.join()
        active.name=asset+(' Head ' if hidden else ' Costume ')+mats[0].replace('Atelier - ','');active['firstPersonHidden']=hidden;joined.append(active)
    model['objects']=joined
    for ob in joined:
        for v in ob.data.vertices:
            total=sum(g.weight for g in v.groups)
            if total:
                for g in list(v.groups):ob.vertex_groups[g.group].add([v.index],g.weight/total,'REPLACE')
        ob.data.calc_loop_triangles()
    tris=sum(len(o.data.loop_triangles) for o in joined)
    if tris>100000:raise RuntimeError(f'Avatar budget exceeded: {tris}')
    rig.data.pose_position='POSE';scene.frame_set(0)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in [rig]+joined:ob.select_set(True)
    bpy.context.view_layer.objects.active=rig
    path=OUT/(asset+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,use_active_scene=True,export_yup=True,
      export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_nla_strips=True,export_anim_single_armature=True,
      export_materials='EXPORT',export_skins=True,export_morph=True,export_morph_normal=True,export_extras=True,export_attributes=True)
    reports[asset]={'triangles':tris,'bytes':path.stat().st_size,'meshes':len(joined),'dynamicHairMeshes':sum(bool(o.get('hairDynamics')) for o in joined),'hairParticles':sum(len(o['hairDynamics']['points']) for o in joined if o.get('hairDynamics'))}
    rig.location.x=-.49 if asset=='courtMale' else .49
bpy.data.libraries.write(str(OUT/'renaissance-organic.blend'),{scene},fake_user=True,compress=True)
(OUT/'export.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports))
