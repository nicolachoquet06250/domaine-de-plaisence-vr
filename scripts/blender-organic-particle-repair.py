import bpy,json
scene=bpy._natural_scene;bpy.context.window.scene=scene;report=[]
for ob in bpy._organic_emitters:
    ob.hide_set(False);ob.hide_render=False
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    ps=ob.particle_systems[0]
    print(ob.name,[(m.type,m.show_viewport,m.show_render) for m in ob.modifiers],ps.settings.display_percentage,ps.is_edited)
    ps.use_hair_dynamics=False
    ps.settings.count+=1;ps.settings.count-=1
    for mod in ob.modifiers:mod.show_viewport=True;mod.show_render=True
    scene.frame_set(1);bpy.context.view_layer.update()
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());print('reset',len(ps.particles),len(ev.particle_systems[0].particles))
    if len(ev.particle_systems[0].particles):
        bpy.ops.particle.particle_edit_toggle();bpy.ops.particle.particle_edit_toggle()
        print('edited',len(ps.particles))
    ps.use_hair_dynamics=True
    ob.hide_set(True);ob.hide_render=True
