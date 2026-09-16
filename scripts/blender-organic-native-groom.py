import bpy,json,math
from mathutils import Vector
scene=bpy._natural_scene;bpy.context.window.scene=scene
for ob in bpy._organic_emitters:
    ob.hide_set(False);ob.hide_render=False
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    while ob.particle_systems:bpy.ops.object.particle_system_remove()
    bpy.ops.object.particle_system_add();ps=ob.particle_systems[-1];s=ps.settings
    s.type='HAIR';s.count=600 if 'Barbe' in ob.name else 128 if 'Female' in ob.name else 112
    s.hair_step=1 if 'Barbe' in ob.name else 3;s.hair_length=.01 if 'Barbe' in ob.name else .15
    s.child_type='INTERPOLATED';s.child_percent=4;s.rendered_child_count=18
    s.root_radius=.00035;s.tip_radius=.00004;s.radius_scale=1
    scene.frame_set(1);bpy.context.view_layer.update()
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());print(ob.name,'fresh',len(ps.particles),len(ev.particle_systems[-1].particles))
    bpy.ops.particle.particle_edit_toggle();bpy.ops.particle.particle_edit_toggle()
    print('edit',len(ps.particles),ps.is_edited)
    ob.hide_render=True;ob.hide_set(True)
