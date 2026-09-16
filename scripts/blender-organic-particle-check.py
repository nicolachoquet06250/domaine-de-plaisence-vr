import bpy,json
scene=bpy._natural_scene;bpy.context.window.scene=scene;rows=[]
for ob in bpy._organic_emitters:
    print(ob.name,'systems',len(ob.particle_systems),'hidden',ob.hide_render,ob.hide_viewport)
    ob.hide_set(False);ob.hide_render=False;ob.hide_viewport=False;ps=ob.particle_systems[0]
    ob.update_tag();scene.frame_set(0)
    scene.frame_set(1);bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());eps=ev.particle_systems[0]
    print('original',len(ps.particles),'evaluated',len(eps.particles))
    a=[list(k.co) for k in eps.particles[0].hair_keys] if len(eps.particles) else []
    row={'name':ob.name,'type':ps.settings.type,'count':ps.settings.count,'children':ps.settings.rendered_child_count,'dynamics':ps.use_hair_dynamics,'originalCount':len(ps.particles),'start':a}
    for frame in range(2,11):scene.frame_set(frame)
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());row['after']=[list(k.co) for k in ev.particle_systems[0].particles[0].hair_keys] if len(ev.particle_systems[0].particles) else []
    rows.append(row);ob.hide_set(True);ob.hide_render=True
scene.frame_set(1)
(OUT/'native-particles.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
