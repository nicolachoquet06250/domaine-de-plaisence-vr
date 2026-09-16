"""Local modelling review of a quarter-stride pose; not an IWSDK runtime check."""
import bpy,math
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
scene=next(s for s in reversed(list(bpy.data.scenes)) if s.name.startswith('Royal coach - two skinned'))
bpy.context.window.scene=scene
for rig in [o for o in scene.objects if o.type=='ARMATURE']:
 for track in rig.animation_data.nla_tracks:track.mute=track.name!='HorseWalk'
scene.frame_set(9)
scene.render.engine='CYCLES';scene.cycles.samples=20
scene.render.resolution_x=1200;scene.render.resolution_y=750;scene.render.resolution_percentage=100
world=bpy.data.worlds.new('Coach rig review studio');world.use_nodes=True;background=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');background.inputs[0].default_value=(.31,.37,.44,1);background.inputs[1].default_value=.65;scene.world=world
cam=bpy.data.cameras.new('Coach rig review camera');camera=bpy.data.objects.new(cam.name,cam);scene.collection.objects.link(camera)
camera.location=(8.1,-10.6,5.0);target=Vector((1.8,0,1.25));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();cam.type='ORTHO';cam.ortho_scale=9.2;scene.camera=camera
light=bpy.data.lights.new('Coach review softbox','AREA');light.energy=2100;light.shape='DISK';light.size=7
lamp=bpy.data.objects.new(light.name,light);scene.collection.objects.link(lamp);lamp.location=(3,-4,8);lamp.rotation_euler=(target-lamp.location).to_track_quat('-Z','Y').to_euler()
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'artifacts/coach-journey-rig/walk-pose-blender.png');bpy.ops.render.render(write_still=True)
print(scene.render.filepath)
