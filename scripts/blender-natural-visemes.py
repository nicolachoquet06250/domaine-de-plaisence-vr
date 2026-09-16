import bpy, math
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
OUT=ROOT/'artifacts/avatars/natural'
src=bpy._natural_scene
scene=bpy.data.scenes.new('Cour naturelle - quinze visemes');bpy.context.window.scene=scene
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
poses=['sil','PP','FF','TH','DD','kk','CH','SS','nn','RR','aa','E','I','O','U']
for row,asset,scale in [(0,'courtMale',1),(1,'courtFemale',.95)]:
    for col,pose in enumerate(poses):
        for old in bpy._natural_models[asset]['objects']:
            if not old.get('firstPersonHidden'):continue
            obj=old.copy();obj.data=old.data.copy();obj.parent=None;obj.modifiers.clear();scene.collection.objects.link(obj)
            obj.location=(col*.21,0,-row*.30+1.64*(1-scale))
            if obj.data.shape_keys:
                for key in obj.data.shape_keys.key_blocks:
                    if key.name!='Basis':key.value=1 if key.name=='viseme_'+pose else 0
        font=bpy.data.curves.new(pose,'FONT');font.body=pose;font.size=.021;font.align_x='CENTER'
        ob=bpy.data.objects.new(asset+' '+pose,font);scene.collection.objects.link(ob);ob.location=(col*.21,-.14,1.445-row*.30);ob.rotation_euler=(math.pi/2,0,0)
world=bpy.data.worlds.new('Visemes studio');world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.16,.18,.21,1);bg.inputs[1].default_value=.7;scene.world=world
for pos,power,size in [((0,-3,4),350,4),((3,-2,3),250,3)]:
    d=bpy.data.lights.new('Softbox','AREA');d.energy=power;d.size=size;o=bpy.data.objects.new('Softbox',d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((1.45,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Visemes');cam=bpy.data.objects.new('Visemes',d);scene.collection.objects.link(cam);d.type='ORTHO';d.ortho_scale=3.23
cam.location=(1.47,-4,1.51);cam.rotation_euler=(Vector((1.47,0,1.51))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
scene.render.resolution_x=3300;scene.render.resolution_y=780;scene.render.resolution_percentage=100
scene.render.filepath=str(OUT/'visemes.png');bpy.ops.render.render(write_still=True)
bpy.context.window.scene=src
print('15 visemes x 2 avatars rendered')
