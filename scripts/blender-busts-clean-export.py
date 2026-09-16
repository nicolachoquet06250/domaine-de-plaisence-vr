"""Remove only the two old baked salon busts; preserve their pedestals and all furniture."""
import bpy,bmesh,json,shutil,hashlib
from pathlib import Path
R=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=R/'artifacts/busts-makehuman'
backup=OUT/'before';backup.mkdir(exist_ok=True)
for name in ['palaceInterior','bustFrancoisI','bustLouisXIV']:
 p=R/'public/gltf/castle'/(name+'.glb');dest=backup/p.name
 if not dest.exists():shutil.copy2(p,dest)
S=bpy._bust_clean_scene;bpy.context.window.scene=S;report=[];counts={-1:0,1:0}
for ob in list(S.objects):
 if ob.type!='MESH':continue
 if not any('Moulures ivoire' in m.name or 'Marbre noir' in m.name for m in ob.data.materials):continue
 bm=bmesh.new();bm.from_mesh(ob.data);remove=[]
 for v in bm.verts:
  p=ob.matrix_world@v.co
  if abs(abs(p.x)-6.1)<.36 and abs(p.y-4.25)<.25 and 1.725<p.z<2.70:
   remove.append(v);counts[-1 if p.x<0 else 1]+=1
 if remove:
  before=len(bm.verts);bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(ob.data);ob.data.update()
  report.append({'object':ob.name,'removedVertices':before-len(bm.verts)})
 bm.free()
assert counts[-1]==2010 and counts[1]==2010,counts
bpy.ops.object.select_all(action='DESELECT')
for ob in S.objects:
 if ob.type=='MESH' and len(ob.data.vertices):ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'public/gltf/castle/palaceInterior.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_extras=True)
(OUT/'interior-cleanup.json').write_text(json.dumps({'removed':report,'perBustVertices':counts,'pedestalTopsPreserved':1.74},indent=2))
print(json.dumps(report))
