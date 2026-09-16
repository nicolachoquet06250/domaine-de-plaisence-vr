"""Trim only grass intersecting the carriage forecourt; preserve source asset."""
import bpy, bmesh, json
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
scene=bpy.data.scenes.new('Pelouse raccord carrosse');bpy.context.window.scene=scene
bpy.ops.import_scene.gltf(filepath=str(ROOT/'public/gltf/royal-enclosure/estateLawnReliefGate.glb'))
removed=0
for obj in list(scene.objects):
 if obj.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(obj.data);faces=[]
 for face in bm.faces:
  p=obj.matrix_world@face.calc_center_median()
  # Estate placement is (100,0,-95); convert Blender XY into world XZ.
  x=p.x+100;z=-p.y-95
  if ((x-104.5)/10.55)**2+((z+54.7)/9.85)**2<1 and .04<p.z<.45:faces.append(face)
 removed+=len(faces)
 bmesh.ops.delete(bm,geom=faces,context='FACES');bm.to_mesh(obj.data);bm.free();obj.data.update()
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/gltf/arrival-coach/estateLawnCoach.glb'),export_format='GLB',use_active_scene=True,export_animations=False,export_image_format='AUTO')
bpy.data.libraries.write(str(ROOT/'artifacts/coach-journey/pelouse-raccord.blend'),{scene},fake_user=True,compress=True)
print(json.dumps({'removedGrassFaces':removed}))
