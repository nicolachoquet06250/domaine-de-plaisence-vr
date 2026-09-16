from pathlib import Path
import bpy,math
from mathutils import Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/refined'
scene=bpy._natural_scene;bpy.context.window.scene=scene
for ob in list(scene.objects):
    if ob.type in {'LIGHT','CAMERA'}:bpy.data.objects.remove(ob,do_unlink=True)
for a,m in bpy._natural_models.items():m['rig'].location.x=-.49 if a=='courtMale' else .49
code=(ROOT/'scripts/blender-natural-render.py').read_text(encoding='utf-8-sig').replace('artifacts/avatars/natural','artifacts/avatars/refined').replace('samples=12','samples=8')
exec(compile(code,'refined-studio','exec'))
for a,m in bpy._natural_models.items():m['rig'].rotation_euler.z=math.pi/2 if a=='courtMale' else -math.pi/2
scene.render.filepath=str(OUT/'profiles.png');bpy.ops.render.render(write_still=True)
for m in bpy._natural_models.values():m['rig'].rotation_euler.z=0
# Low three-quarter detail of the newly modelled shoes, both genders visible.
hidden=[]
for m in bpy._natural_models.values():
    for ob in m['objects']:
        if any(s in ob.name for s in ['Robe plis continus','Galon de robe','Feuille brodee']):ob.hide_render=True;hidden.append(ob)
cam=scene.camera;cam.data.ortho_scale=.80
cam.location=(.32,-1.4,.66);cam.rotation_euler=(Vector((0,0,.085))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1300;scene.render.resolution_y=720
scene.render.filepath=str(OUT/'souliers.png');bpy.ops.render.render(write_still=True)
for ob in hidden:ob.hide_render=False
print('Refined portraits, strict profiles, shoes and full figures rendered')
