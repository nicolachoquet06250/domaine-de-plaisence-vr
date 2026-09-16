import bpy,json
from pathlib import Path
R=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
S=bpy.data.scenes.new('Inspection mobilier actuel - bustes');bpy.context.window.scene=S
bpy.ops.import_scene.gltf(filepath=str(R/'public/gltf/castle/palaceInterior.glb'))
report=[]
for ob in list(S.objects):
 if ob.type!='MESH':continue
 coords=[ob.matrix_world@v.co for v in ob.data.vertices]
 selected=[i for i,p in enumerate(coords) if abs(abs(p.x)-6.1)<.45 and abs(p.y-4.25)<.4 and 1.72<p.z<2.9]
 if selected:
  report.append({'name':ob.name,'materials':[m.name for m in ob.data.materials],'vertices':len(coords),'inside':len(selected),'bounds':[[min(coords[i][k] for i in selected),max(coords[i][k] for i in selected)] for k in range(3)]})
bpy._bust_clean_scene=S
(R/'artifacts/busts-makehuman/interior-inspection.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
