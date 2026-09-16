import bpy,math,json
from mathutils import Vector
scene=bpy._natural_scene;bpy.context.window.scene=scene;report=[]
for ob in bpy._organic_emitters:
    ob.hide_set(False);ob.hide_render=False
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    female='Female' in ob.name;scale=.95 if female else 1;beard='Barbe' in ob.name;ps=ob.particle_systems[0]
    scene.frame_set(1);bpy.context.view_layer.update()
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());eps=ev.particle_systems[0];mod=next(m for m in ev.modifiers if m.type=='PARTICLE_SYSTEM')
    guides=[]
    for i,p in enumerate(eps.particles):
        co=p.hair_keys[0].co;root=Vector((co.x,co.z,-co.y))/scale;curve=[]
        a=math.atan2(root.x,root.z+.027);h=root.y
        for j in range(len(p.hair_keys)):
            t=j/(len(p.hair_keys)-1)
            if beard:q=root+Vector((.001*math.sin(i)*t,-.006*t,.003*t))
            elif female:
                q=root.lerp(Vector((.008*math.sin(i),1.805,-.087)),smooth(t));q.x+=.017*math.sin(math.pi*t)*(1 if root.x>=0 else -1);q.z-=.025*math.sin(math.pi*t)
                u=Vector((q.x/.098,(q.y-1.65)/.137,(q.z+.027)/.118))
                if u.length<1.025:u.normalize();u*=1.025;q=Vector((u.x*.098,1.65+u.y*.137,-.027+u.z*.118))
            else:
                aa=a+(1 if a>=0 else -1)*1.20*t if math.cos(a)>.3 else a+.035*math.sin(t*4+i)
                hh=h-(.15+.035*math.sin(i*1.7))*t
                if h>1.71:hh=h-.025*math.sin(t*math.pi/2)-.15*t*t
                crown=math.sqrt(max(.03,1-((max(hh,1.63)-1.65)/.139)**2));q=root.lerp(Vector((.099*math.sin(aa)*crown,hh,.120*math.cos(aa)*crown-.027)),smooth(t*3))
                if math.cos(a)>.3:q.y=max(q.y,1.714-.045*t)
            key=ps.particles[i].hair_keys[j];key.co_object_set(ev,mod,p,Vector((q.x,-q.z,q.y))*scale);key.weight=1 if j<2 else 0
            curve.append(list(q*scale))
        guides.append(curve)
    ob['nativeGuides']=guides;ps.use_hair_dynamics=True
    if ps.cloth:
        ps.cloth.settings.quality=6;ps.cloth.settings.mass=.015;ps.cloth.settings.bending_stiffness=25 if female else 8
    ob.update_tag();bpy.context.view_layer.update()
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());n=len(ev.particle_systems[0].particles)
    report.append({'name':ob.name,'persistentParticles':len(ps.particles),'evaluatedParticles':n,'keys':sum(len(p.hair_keys) for p in ps.particles),'dynamics':ps.use_hair_dynamics})
    assert n==ps.settings.count
    ob.hide_render=True;ob.hide_set(True)
scene.frame_set(1)
bpy.data.libraries.write(str(OUT/'renaissance-organic.blend'),{scene},fake_user=True,compress=True)
(OUT/'native-particles.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
