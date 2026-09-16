import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=R/'artifacts/busts-makehuman'
S=bpy._bust_scene;bpy.context.window.scene=S;models=bpy._bust_models
S.render.engine='CYCLES';S.cycles.samples=16;S.cycles.use_denoising=True
S.world=bpy.data.worlds.new('Atelier bustes');S.world.use_nodes=True
bg=next(n for n in S.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.06,.072,.09,1);bg.inputs[1].default_value=.5
for name,pos,power,size in [('Key',(-3,-4,4),500,3),('Fill',(3,-2,2.7),180,2.5),('Rim',(1,2,3),500,2)]:
 data=bpy.data.lights.new('Bustes '+name,'AREA');data.energy=power;data.shape='DISK';data.size=size
 ob=bpy.data.objects.new('Bustes '+name,data);S.collection.objects.link(ob);ob.location=pos
 ob.rotation_euler=(Vector((0,0,.6))-ob.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Bustes portraits');cam=bpy.data.objects.new('Bustes portraits',data);S.collection.objects.link(cam);S.camera=cam
data.type='ORTHO';data.ortho_scale=1.3
S.render.resolution_x=820;S.render.resolution_y=980;S.render.resolution_percentage=100
for asset,obs in models.items():
 for key,others in models.items():
  for ob in others:ob.hide_render=key!=asset
 cam.location=(.65,-4,1.15);cam.rotation_euler=(Vector((0,0,.57))-cam.location).to_track_quat('-Z','Y').to_euler()
 S.render.filepath=str(OUT/(asset+'.png'));bpy.ops.render.render(write_still=True)
for obs in models.values():
 for ob in obs:ob.hide_render=False
print('Four portrait renders complete')
