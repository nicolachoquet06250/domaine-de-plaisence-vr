import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/refined'
scene=bpy._natural_scene;bpy.context.window.scene=scene;copies=[];hidden=[]
for asset,m in bpy._natural_models.items():
    m['rig'].location.x=-.235 if asset=='courtMale' else .235
    for ob in m['objects']:
        hidden.append((ob,ob.hide_render));ob.hide_render=True
        feet={g.index for g in ob.vertex_groups if g.name.startswith('Foot.')}
        if not any(sum(g.weight for g in v.groups if g.group in feet)>.9 for v in ob.data.vertices):continue
        cp=ob.copy();cp.data=ob.data.copy();cp.hide_render=False;scene.collection.objects.link(cp);copies.append(cp)
        bm=bmesh.new();bm.from_mesh(cp.data);deform=bm.verts.layers.deform.active
        dead=[v for v in bm.verts if sum(w for g,w in v[deform].items() if g in feet)<.9]
        bmesh.ops.delete(bm,geom=dead,context='VERTS');bm.to_mesh(cp.data);bm.free()
cam=scene.camera;cam.data.ortho_scale=.84
cam.location=(.32,-1.4,.65);cam.rotation_euler=(Vector((0,0,.055))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1300;scene.render.resolution_y=720;scene.render.filepath=str(OUT/'souliers.png');bpy.ops.render.render(write_still=True)
cam.location=(.48,.9,.36);cam.rotation_euler=(Vector((0,0,.06))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(OUT/'talons.png');bpy.ops.render.render(write_still=True)
for ob in copies:bpy.data.objects.remove(ob,do_unlink=True)
for ob,value in hidden:ob.hide_render=value
native=[]
for ob in bpy._organic_emitters:
    ps=ob.particle_systems[0];native.append({'name':ob.name,'parents':len(ps.particles),'settingsCount':ps.settings.count,'dynamics':ps.use_hair_dynamics})
    assert len(ps.particles)==ps.settings.count
(OUT/'native-particles.json').write_text(json.dumps(native,indent=2))
src=(ROOT/'scripts/blender-natural-save.py').read_text(encoding='utf-8-sig').replace('artifacts/avatars/natural','artifacts/avatars/refined').replace('renaissance-natural.blend','renaissance-refined.blend')
exec(compile(src,'refined-editable-save','exec'))
print(json.dumps(native))
