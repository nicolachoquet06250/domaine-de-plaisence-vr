"""Export final revision; preserve hair, eyes, footwear and fitted jewellery detail."""
import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/refined'
scene=bpy._natural_scene;bpy.context.window.scene=scene;reports={}
for asset,m in bpy._natural_models.items():
    rig=m['rig'];rig.location=(0,0,0);rig.rotation_euler=(0,0,0);rig.data.pose_position='REST';scale=.95 if asset=='courtFemale' else 1
    for ob in m['objects']:
        if ob.data.shape_keys or ob.get('strandSurface') or ob.get('keepDetail') or 'Mains' in ob.name:continue
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
        dec=ob.modifiers.new('Optimisation surfaces secondaires','DECIMATE');dec.ratio=.30;dec.use_collapse_triangulate=True
        bpy.ops.object.modifier_move_up(modifier=dec.name);bpy.ops.object.modifier_apply(modifier=dec.name)
    # Fit against the actual final torso, after its tessellation has changed.
    torso=next(o for o in m['objects'] if 'Pourpoint taille' in o.name)
    tree=BVHTree.FromPolygons([v.co.copy() for v in torso.data.vertices],[tuple(p.vertices) for p in torso.data.polygons]);gaps=[]
    for ob in m['objects']:
        if not any(s in ob.name for s in ['Chaine de cour','Medaille','Passementerie pourpoint']):continue
        for v in ob.data.vertices:
            hit=tree.ray_cast(Vector((v.co.x,-scale,v.co.z)),Vector((0,1,0)))
            if hit[0] is not None:v.co.y=hit[0].y-.0033*scale;gaps.append((hit[0].y-v.co.y)/scale)
    shapes=[o for o in m['objects'] if o.data.shape_keys]
    bpy.ops.object.select_all(action='DESELECT')
    for ob in shapes:
        ob.select_set(True)
        for key in ob.data.shape_keys.key_blocks[1:]:key.value=0
    bpy.context.view_layer.objects.active=m['face'];bpy.ops.object.join()
    objects=[o for o in m['objects'] if o not in shapes]+[m['face']];groups={};joined=[]
    for ob in objects:
        if ob.data.shape_keys or ob.get('hairDynamics'):joined.append(ob);continue
        groups.setdefault((bool(ob.get('firstPersonHidden')),tuple(mat.name for mat in ob.data.materials)),[]).append(ob)
    for (hidden,mats),batch in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for ob in batch:ob.select_set(True)
        ob=batch[0];bpy.context.view_layer.objects.active=ob
        if len(batch)>1:bpy.ops.object.join()
        ob.name=asset+(' Head ' if hidden else ' Costume ')+mats[0];ob['firstPersonHidden']=hidden;joined.append(ob)
    m['objects']=joined
    for ob in joined:
        for v in ob.data.vertices:
            total=sum(g.weight for g in v.groups)
            if total:
                for g in list(v.groups):ob.vertex_groups[g.group].add([v.index],g.weight/total,'REPLACE')
        ob.data.calc_loop_triangles()
    triangles=sum(len(o.data.loop_triangles) for o in joined)
    reports[asset]={'triangles':triangles,'meshes':len(joined),'necklaceClearanceMm':[min(gaps)*1000,max(gaps)*1000],'headAdvanceMm':45,'hairGuidePoints':sum(len(o['hairDynamics']['points']) for o in joined if o.get('hairDynamics'))}
    if triangles>100000:
        (OUT/'budget-report.json').write_text(json.dumps(reports,indent=2));raise RuntimeError(f'Budget exceeded {asset}: {triangles}')
    rig.data.pose_position='POSE';scene.frame_set(0)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in [rig]+joined:ob.select_set(True)
    bpy.context.view_layer.objects.active=rig
    path=OUT/(asset+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,use_active_scene=True,export_yup=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_nla_strips=True,export_anim_single_armature=True,export_materials='EXPORT',export_skins=True,export_morph=True,export_morph_normal=True,export_extras=True,export_attributes=True)
    reports[asset]['bytes']=path.stat().st_size;rig.location.x=-.49 if asset=='courtMale' else .49
bpy.data.libraries.write(str(OUT/'renaissance-refined.blend'),{scene},fake_user=True,compress=True)
(OUT/'export.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports))
