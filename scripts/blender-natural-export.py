"""Optimize non-facial surfaces, batch by material/visibility and export via Blender MCP."""
import bpy, json, shutil
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
OUT=ROOT/'artifacts/avatars/natural'; scene=bpy._natural_scene;bpy.context.window.scene=scene
reports={}
for asset,model in bpy._natural_models.items():
    rig=model['rig'];rig.location=(0,0,0);rig.data.pose_position='REST'
    for obj in model['objects']:
        if obj.data.shape_keys or 'Mains' in obj.name:continue
        # Only the static topology is reduced. Morph topology stays exactly authored.
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
        mod=obj.modifiers.new('Optimisation des surfaces','DECIMATE');mod.ratio=.36;mod.use_collapse_triangulate=True
        bpy.ops.object.modifier_move_up(modifier=mod.name)
        bpy.ops.object.modifier_apply(modifier=mod.name)
    groups={}
    for obj in model['objects']:
        if obj.data.shape_keys:continue
        k=(bool(obj.get('firstPersonHidden')),tuple(m.name for m in obj.data.materials))
        groups.setdefault(k,[]).append(obj)
    joined=[model['face']]
    for (hidden,mats),batch in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for ob in batch:ob.select_set(True)
        active=batch[0];bpy.context.view_layer.objects.active=active
        if len(batch)>1:bpy.ops.object.join()
        active.name=asset+(' Head ' if hidden else ' Costume ')+mats[0].replace('Atelier - ','')
        active['firstPersonHidden']=hidden;joined.append(active)
    model['objects']=joined
    # Normalize interpolated skin weights after collapse/join.
    for obj in joined:
        for v in obj.data.vertices:
            total=sum(g.weight for g in v.groups)
            if total:
                for g in list(v.groups):obj.vertex_groups[g.group].add([v.index],g.weight/total,'REPLACE')
        obj.data.calc_loop_triangles()
    tris=sum(len(o.data.loop_triangles) for o in joined)
    if tris>=60000:raise RuntimeError(f'{asset}: triangle budget exceeded: {tris}')
    rig.data.pose_position='POSE';scene.frame_set(0)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in [rig]+joined:ob.select_set(True)
    bpy.context.view_layer.objects.active=rig
    path=OUT/(asset+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,use_active_scene=True,export_yup=True,
        export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_nla_strips=True,export_anim_single_armature=True,
        export_materials='EXPORT',export_skins=True,export_morph=True,export_morph_normal=True,export_extras=True)
    reports[asset]={'triangles':tris,'meshObjects':len(joined),'bytes':path.stat().st_size,'visemes':[k.name for k in model['face'].data.shape_keys.key_blocks if k.name!='Basis']}
    rig.location.x=-.49 if asset=='courtMale' else .49
bpy.data.libraries.write(str(OUT/'renaissance-natural.blend'),{scene},fake_user=True,compress=True)
(OUT/'export.json').write_text(json.dumps(reports,indent=2))
print(json.dumps(reports))
