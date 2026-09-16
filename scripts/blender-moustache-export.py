import bpy,json
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/moustache'
scene=bpy._natural_scene;bpy.context.window.scene=scene;m=bpy._natural_models['courtMale'];rig=m['rig']
rig.location=(0,0,0);rig.rotation_euler=(0,0,0);rig.data.pose_position='POSE';scene.frame_set(0)
bpy.ops.object.select_all(action='DESELECT')
for ob in [rig]+m['objects']:ob.select_set(True)
for key in m['face'].data.shape_keys.key_blocks[1:]:key.value=0
bpy.context.view_layer.objects.active=rig
path=OUT/'courtMale.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,use_active_scene=True,export_yup=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_nla_strips=True,export_anim_single_armature=True,export_materials='EXPORT',export_skins=True,export_morph=True,export_morph_normal=True,export_extras=True,export_attributes=True)
rig.location.x=-.2;rig.data.pose_position='REST'
bpy.data.libraries.write(str(OUT/'renaissance-moustache.blend'),{scene},fake_user=True,compress=True)
print(json.dumps({'path':str(path),'bytes':path.stat().st_size}))
