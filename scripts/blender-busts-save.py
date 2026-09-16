import bpy
from pathlib import Path
from mathutils import Vector
R=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');S=bpy._bust_scene;bpy.context.window.scene=S
models=bpy._bust_models
for i,(asset,obs) in enumerate(models.items()):
 for ob in obs:ob.location.x=(i-1.5)*1.02;ob.hide_render=False
 for ob in S.objects:
  if ob.name.startswith(asset) and 'particules editables' in ob.name:ob.location.x=(i-1.5)*1.02
S.world=bpy.data.worlds.new('Galerie bustes fond');S.world.use_nodes=True
bg=next(n for n in S.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.06,.075,.10,1);bg.inputs[1].default_value=.45
for name,pos,power in [('Key',(-3,-4,4),600),('Fill',(3,-2,2.7),280),('Rim',(1,2,3),650)]:
 d=bpy.data.lights.new('Galerie '+name,'AREA');d.energy=power;d.size=3
 ob=bpy.data.objects.new('Galerie '+name,d);S.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector((0,0,.6))-ob.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Galerie quatre portraits');cam=bpy.data.objects.new('Galerie quatre portraits',d);S.collection.objects.link(cam);S.camera=cam
d.type='ORTHO';d.ortho_scale=4.45;cam.location=(.1,-7,1.8);cam.rotation_euler=(Vector((0,0,.62))-cam.location).to_track_quat('-Z','Y').to_euler()
S.render.engine='CYCLES';S.cycles.samples=16;S.cycles.use_denoising=True;S.render.resolution_x=1800;S.render.resolution_y=700;S.render.resolution_percentage=100
S.render.filepath=str(R/'artifacts/busts-makehuman/quatre-bustes.png');bpy.ops.render.render(write_still=True)
S['referencePortraits']='Francois Ier / Clouet; Louis XIV / Rigaud; Catherine de Medicis / Clouet; Anne de France / Jean Hey'
S['staticSculptures']='Marble GLB exports; native particle dynamics retained as editable authoring source only'
bpy.data.libraries.write(str(R/'artifacts/busts-makehuman/bustes-historiques-makehuman.blend'),{S,bpy._bust_clean_scene},fake_user=True,compress=True)
print('Saved atelier source and four-bust gallery')
