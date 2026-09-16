import bpy
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/avatars/fbx'
bpy.ops.wm.read_factory_settings(use_empty=True)
for name, x in [('courtMale', -.46), ('courtFemale', .46)]:
    bpy.ops.import_scene.fbx(filepath=str(OUT / name / (name + '.fbx')), use_anim=False)
    rig = next(o for o in bpy.context.selected_objects if o.type == 'ARMATURE')
    rig.data.pose_position = 'REST'
    rig.location.x = x
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.world = bpy.data.worlds.new('Preview world')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.18, .18, .18, 1)
for name, loc, power, size in [('Key', (-3, -4, 5), 450, 4), ('Fill', (3, -2, 3), 220, 3), ('Rim', (0, 2, 4), 350, 3)]:
    light = bpy.data.lights.new(name, 'AREA')
    light.energy = power
    light.shape = 'DISK'
    light.size = size
    ob = bpy.data.objects.new(name, light)
    scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector((0, 0, 1.1)) - ob.location).to_track_quat('-Z', 'Y').to_euler()
camera = bpy.data.objects.new('Preview camera', bpy.data.cameras.new('Preview camera'))
scene.collection.objects.link(camera)
scene.camera = camera
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 2.1
camera.location = (0, -6, 2.0)
camera.rotation_euler = (Vector((0, 0, .93)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.resolution_x = 1000
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(OUT / 'preview-fbx.png')
bpy.ops.render.render(write_still=True)
