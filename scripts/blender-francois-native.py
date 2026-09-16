"""Rebind native hair in the final rest pose, using evaluated modifier coordinates."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/francois'
scene=bpy._natural_scene;bpy.context.window.scene=scene;scene.frame_set(1);report=[]
for ob in bpy._organic_emitters:
    asset='courtFemale' if ob.name.startswith('courtFemale') else 'courtMale';m=bpy._natural_models[asset];rig=m['rig'];rig.data.pose_position='REST'
    beard='Barbe' in ob.name;scale=.95 if asset=='courtFemale' else 1
    ob.hide_set(False);bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.particle_system_remove()
    if not beard:
        cap=next(o for o in m['objects'] if any('Chevelure microfibres' in mat.name for mat in o.data.materials))
        ob.data=cap.data.copy()
        if asset=='courtMale':
            proxy=next(o for o in m['objects'] if o.get('hairDynamics'))
            points=[Vector((p[0],-p[2],p[1])) for p in proxy['hairDynamics']['points']]
            guides=[points[i:i+9] for i in range(0,len(points),9)]
        else:
            proxy=next(o for o in m['objects'] if any('fibres capillaires denses' in mat.name for mat in o.data.materials))
            assert len(proxy.data.vertices)==460*36
            guides=[[sum((proxy.data.vertices[i+j*2+k].co for k in [0,1,18,19]),Vector())/4 for j in range(9)] for i in range(0,len(proxy.data.vertices),36)]
    bpy.ops.object.particle_system_add();ps=ob.particle_systems[0];s=ps.settings
    s.type='HAIR';s.count=600 if beard else 460;s.hair_step=1 if beard else 3;s.hair_length=.005 if beard else .12
    s.child_type='INTERPOLATED';s.child_percent=4;s.rendered_child_count=24;s.root_radius=.00016;s.tip_radius=.000025;s.radius_scale=1
    scene.tool_settings.particle_edit.default_key_count=3 if beard else 9
    bpy.context.view_layer.update();bpy.ops.particle.particle_edit_toggle();bpy.ops.particle.particle_edit_toggle()
    deps=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(deps);eps=ev.particle_systems[0]
    mod=next(mm for mm in ev.modifiers if mm.type=='PARTICLE_SYSTEM')
    original_roots=[]
    for i,p in enumerate(eps.particles):
        root=ps.particles[i].hair_keys[0].co_object(ev,mod,p).copy();original_roots.append(root.copy())
        if beard:
            n=Vector((root.x*.6,-max(.024,-root.y),-.10)).normalized()
            curve=[root+n*.0035*t+Vector((.0003*math.sin(i+t*6),0,-.001*t)) for t in [0,.5,1]]
        else:
            guide=min(guides,key=lambda g:(g[0]-root).length_squared);offset=root-guide[0]
            curve=[q+offset*(1-j/8) for j,q in enumerate(guide)]
        curve[0]=root
        for j,(key,q) in enumerate(zip(ps.particles[i].hair_keys,curve)):
            key.co_object_set(ev,mod,p,q);key.weight=1 if j<2 else 0
    ob.update_tag(refresh={'DATA'});bpy.context.view_layer.update()
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());eps=ev.particle_systems[0];mod=next(mm for mm in ev.modifiers if mm.type=='PARTICLE_SYSTEM')
    tree=BVHTree.FromPolygons([v.co.copy() for v in ev.data.vertices],[tuple(p.vertices) for p in ev.data.polygons])
    gaps=[];drifts=[];maxlen=0
    for i,p in enumerate(eps.particles):
        root=ps.particles[i].hair_keys[0].co_object(ev,mod,p)
        gaps.append(tree.find_nearest(root)[3]);drifts.append((root-original_roots[i]).length)
        tip=ps.particles[i].hair_keys[-1].co_object(ev,mod,p);maxlen=max(maxlen,(tip-root).length)
    result={'name':ob.name,'parents':len(ps.particles),'rootSurfaceGapMax':max(gaps),'rootDriftMax':max(drifts),'maxRootTipLength':maxlen}
    report.append(result);(OUT/'native-particles.json').write_text(json.dumps(report,indent=2))
    assert max(gaps)<.001 and max(drifts)<.0001 and maxlen<.35,result
    ps.use_hair_dynamics=True
    if ps.cloth:ps.cloth.settings.quality=6;ps.cloth.settings.mass=.015;ps.cloth.settings.bending_stiffness=15
    result['dynamics']=ps.use_hair_dynamics;ob.hide_set(True);ob.hide_render=True
(OUT/'native-particles.json').write_text(json.dumps(report,indent=2))
bpy.data.libraries.write(str(OUT/'renaissance-francois.blend'),{scene},fake_user=True,compress=True)
print(json.dumps(report))
