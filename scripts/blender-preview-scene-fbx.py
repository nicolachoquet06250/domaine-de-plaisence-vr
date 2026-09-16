import bpy, json, math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/scene-fbx'
def point(v):return Vector((v[0],-v[2],v[1]))
def setup(file):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(OUT/file),use_anim=False)
    scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
    scene.world=bpy.data.worlds.new('Ciel de controle');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.45,.52,.60,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.6
    scene.render.resolution_x=1200;scene.render.resolution_y=850;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    cam=bpy.data.objects.new('Camera de verification',bpy.data.cameras.new('Camera de verification'))
    scene.collection.objects.link(cam);scene.camera=cam
    return scene,cam
def render(scene,cam,name,pos,target,fov):
    cam.location=point(pos);cam.rotation_euler=(point(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.lens_unit='FOV';cam.data.angle=math.radians(fov)
    scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    print('PREVIEW_SAVED',name,flush=True)
scene,cam=setup('scene-complete.fbx')
render(scene,cam,'scene-complete-apercu',[175,130,95],[50,0,-55],57)
render(scene,cam,'chateau-apercu',[145,30,-66],[100,5,-117],57)
scene,cam=setup('interieur-chateau.fbx')
render(scene,cam,'interieur-apercu',[100,2.2,-118],[100,3.4,-127],80)
