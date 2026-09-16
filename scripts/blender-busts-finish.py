"""Fit sculptural trim, retain editable particle grooms, save the four-bust atelier."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=R/'artifacts/busts-makehuman'
S=bpy._bust_scene;bpy.context.window.scene=S;models=bpy._bust_models
# Fit Anne's crown to the actual hood, with a thin contiguous raised border.
obs=models['bustAnneFrance'];hood=next(o for o in obs if 'Coiffe a pans' in o.name)
tree=BVHTree.FromPolygons([v.co.copy() for v in hood.data.vertices],[tuple(p.vertices) for p in hood.data.polygons])
for ob in obs:
 if not any(s in ob.name for s in ['Cercle de couronne','Bandeau plein','Fleuron de couronne']):continue
 for v in ob.data.vertices:
  center=Vector((0,.027*2.2,v.co.z));direction=Vector((v.co.x,v.co.y-center.y,0)).normalized()
  # Crown fleurons rise above the band instead of following the taper all the way in.
  limit=.30+(1.754-1.443)*2.2;probe=center.copy();probe.z=min(center.z,limit)
  hit=tree.ray_cast(probe,direction)[0]
  if hit is not None:
   radius=Vector((hit.x,hit.y-probe.y,0)).length+.008
   v.co.x=direction.x*radius;v.co.y=center.y+direction.y*radius
# Subdivide only the wig's broad curls to remove hard kinks; the export is simplified later.
for ob in models['bustLouisXIV']:
 if 'Perruque boucle S' not in ob.name:continue
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 mod=ob.modifiers.new('Boucles arrondies','SUBSURF');mod.levels=1;bpy.ops.object.modifier_apply(modifier=mod.name)

report=[]
for source,guides in bpy._bust_native:
 ob=source.copy();ob.data=source.data.copy();ob.name=source.name+' - particules editables';S.collection.objects.link(ob)
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.object.particle_system_add();ps=ob.particle_systems[0];s=ps.settings
 s.type='HAIR';s.count=180;s.hair_step=3;s.hair_length=.15;s.child_type='INTERPOLATED';s.child_percent=3;s.rendered_child_count=16
 s.root_radius=.0003;s.tip_radius=.00004;s.radius_scale=1
 S.tool_settings.particle_edit.default_key_count=9;bpy.context.view_layer.update()
 bpy.ops.particle.particle_edit_toggle();bpy.ops.particle.particle_edit_toggle()
 deps=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(deps);eps=ev.particle_systems[0];mod=next(m for m in ev.modifiers if m.type=='PARTICLE_SYSTEM')
 gg=[[Vector((p.x,-p.z,p.y)) for p in guide] for guide in guides]
 for i,p in enumerate(eps.particles):
  root=ps.particles[i].hair_keys[0].co_object(ev,mod,p).copy();guide=min(gg,key=lambda g:(g[0]-root).length_squared);offset=root-guide[0]
  for j,key in enumerate(ps.particles[i].hair_keys):
   t=j/8;idx=t*(len(guide)-1);a=int(idx);q=guide[a].lerp(guide[min(a+1,len(guide)-1)],idx-a)+offset*(1-t)
   key.co_object_set(ev,mod,p,root if j==0 else q);key.weight=1 if j<2 else 0
 ob.update_tag(refresh={'DATA'});bpy.context.view_layer.update()
 # Same native tooling as the avatars, stored off for the static marble sculpture.
 ps.use_hair_dynamics=True
 if ps.cloth:ps.cloth.settings.quality=6;ps.cloth.settings.mass=.015;ps.cloth.settings.bending_stiffness=15
 ob['sculptureGroom']='Editable native groom with gravity; static mesh equivalent exported for the marble bust'
 report.append({'object':ob.name,'parents':len(ps.particles),'children':16,'gravity':list(S.gravity),'dynamics':ps.use_hair_dynamics})
 ob.hide_render=True;ob.hide_set(True)
(OUT/'native-grooms.json').write_text(json.dumps(report,indent=2))
bpy._bust_particle_report=report
print(json.dumps(report))
