import bpy, math
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
src=next(s for s in reversed(list(bpy.data.scenes)) if s.name.startswith('Cour Renaissance - articulation labiale'))
scene=bpy.data.scenes.new('Visemes - controle visuel');bpy.context.window.scene=scene
scene.render.engine='CYCLES';scene.cycles.samples=12
poses=['sil','PP','FF','aa','I','O','U','TH']
for row,asset,factor in [(0,'courtMale',1),(1,'courtFemale',.95)]:
    originals=[o for o in src.objects if o.type=='MESH' and o.name.startswith(asset) and 'Head' in o.name]
    for col,pose in enumerate(poses):
        for old in originals:
            obj=old.copy();obj.data=old.data.copy();obj.parent=None;obj.modifiers.clear();scene.collection.objects.link(obj)
            # Normalize head height for this detail-only contact sheet.
            obj.location=(col*.235,-0.0,row*-.32 + 1.625*(1-factor))
            if obj.data.shape_keys:
                for key in obj.data.shape_keys.key_blocks:
                    if key.name!='Basis':key.value=1 if key.name=='viseme_'+pose else 0
        font=bpy.data.curves.new(pose,'FONT');font.body=pose;font.size=.026;font.align_x='CENTER'
        label=bpy.data.objects.new(asset+' '+pose,font);scene.collection.objects.link(label);label.location=(col*.235,-.13,1.43-row*.32);label.rotation_euler=(math.pi/2,0,0)
world=bpy.data.worlds.new('Viseme studio');world.use_nodes=True;bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.3,.3,.3,1);bg.inputs[1].default_value=.8;scene.world=world
for name,pos,power,size in [('Key',(0,-2,3),170,3),('Fill',(2,-1,2),80,2)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((.8,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Visemes');cam=bpy.data.objects.new('Visemes',data);scene.collection.objects.link(cam);cam.location=(.8225,-3,1.49);cam.rotation_euler=(Vector((.8225,0,1.49))-cam.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=1.91;scene.camera=cam
scene.render.resolution_x=2400;scene.render.resolution_y=860;scene.render.resolution_percentage=100
scene.render.filepath=str(ROOT/'artifacts/avatars/lipsync/visemes.png');bpy.ops.render.render(write_still=True)
print(scene.render.filepath)
