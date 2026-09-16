import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/refined'
scene=bpy._natural_scene;bpy.context.window.scene=scene;m=bpy._natural_models['courtMale'];rig=m['rig']
base=next(o for o in m['objects'] if 'chatain profond' in o.name and not o.data.shape_keys)
ob=base.copy();ob.data=base.data.copy();ob.name='courtMale Particules Coiffure dense finale';scene.collection.objects.link(ob)
bm=bmesh.new();bm.from_mesh(ob.data)
dead=[v for v in bm.verts if not (v.co.z>1.686 or (v.co.z>1.60 and v.co.y>.015))]
bmesh.ops.delete(bm,geom=dead,context='VERTS');bm.to_mesh(ob.data);bm.free()
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
rig.data.pose_position='REST';bpy.ops.object.particle_system_add();ps=ob.particle_systems[-1];s=ps.settings
s.type='HAIR';s.count=300;s.hair_step=3;s.hair_length=.15;s.child_type='INTERPOLATED';s.child_percent=4;s.rendered_child_count=18
s.root_radius=.00035;s.tip_radius=.00004;s.radius_scale=1;ps.seed=91
scene.frame_set(1);bpy.context.view_layer.update();scene.tool_settings.particle_edit.default_key_count=9
bpy.ops.particle.particle_edit_toggle();bpy.ops.particle.particle_edit_toggle()
ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());eps=ev.particle_systems[-1];mod=next(m for m in ev.modifiers if m.type=='PARTICLE_SYSTEM')
proxy=next(o for o in m['objects'] if o.get('hairDynamics'));points=[Vector((p[0],-p[2],p[1])) for p in proxy['hairDynamics']['points']]
guides=[points[i:i+9] for i in range(0,2700,9)]
for i,p in enumerate(eps.particles):
    root=p.hair_keys[0].co.copy();guide=min(guides,key=lambda c:(c[0]-root).length_squared);offset=root-guide[0]
    for j,key in enumerate(ps.particles[i].hair_keys):
        key.co_object_set(ev,mod,p,guide[j]+offset*(1-j/8));key.weight=1 if j<2 else 0
ps.use_hair_dynamics=True
if ps.cloth:ps.cloth.settings.quality=6;ps.cloth.settings.mass=.015;ps.cloth.settings.bending_stiffness=8
ob.hide_render=True;ob.hide_set(True);bpy._organic_emitters.append(ob);rig.data.pose_position='POSE'
report=[{'name':o.name,'parents':len(o.particle_systems[0].particles),'settingsCount':o.particle_systems[0].settings.count,'dynamics':o.particle_systems[0].use_hair_dynamics} for o in bpy._organic_emitters]
assert len(report)==3 and all(r['parents']==r['settingsCount'] for r in report)
(OUT/'native-particles.json').write_text(json.dumps(report,indent=2))
bpy.data.libraries.write(str(OUT/'renaissance-refined.blend'),{scene},fake_user=True,compress=True);print(json.dumps(report))
