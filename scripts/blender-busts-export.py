import bpy,json
from pathlib import Path
R=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=R/'artifacts/busts-makehuman'
S=bpy._bust_scene;bpy.context.window.scene=S;models=bpy._bust_models;report={}
for ob in list(S.objects):
 if ' - portrait MakeHuman' in ob.name:bpy.data.objects.remove(ob,do_unlink=True)
for asset,obs in models.items():
 copies=[]
 for ob in obs:
  cp=ob.copy();cp.data=ob.data.copy();cp.location=(0,0,0);S.collection.objects.link(cp);cp.hide_render=False;cp.hide_set(False);copies.append(cp)
  ratio=1 if 'Visage MakeHuman' in cp.name or 'Regard grave' in cp.name else .12 if 'Perruque boucle S' in cp.name else .60
  if ratio<1:
   bpy.ops.object.select_all(action='DESELECT');cp.select_set(True);bpy.context.view_layer.objects.active=cp
   mod=cp.modifiers.new('Optimisation details hors visage','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.ops.object.select_all(action='DESELECT')
 for cp in copies:cp.select_set(True)
 bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();ob=copies[0];ob.name=asset+' - portrait MakeHuman'
 # Static sculptural assets may be decimated together: no morph/skin attachments.
 ob['anatomicalSource']='MakeHuman base.obj CC0';ob['referencePortrait']=asset;ob['staticSculpture']=True
 base=min(v.co.z for v in ob.data.vertices)
 for v in ob.data.vertices:v.co.z-=base
 tri=sum(len(p.vertices)-2 for p in ob.data.polygons);bounds=[[min(v.co[k] for v in ob.data.vertices),max(v.co[k] for v in ob.data.vertices)] for k in range(3)]
 assert 30000<tri<145000 and abs(bounds[2][0])<.0001 and .9<bounds[2][1]<1.3,(asset,tri,bounds)
 path=R/'public/gltf/castle'/(asset+'.glb')
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_extras=True)
 report[asset]={'triangles':tri,'boundsBlender':bounds,'bytes':path.stat().st_size,'materialPrimitives':len(ob.data.materials)}
 bpy.data.objects.remove(ob,do_unlink=True)
(OUT/'export-stats.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
