import bpy,json
from pathlib import Path
R=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
S=bpy._bust_clean_scene;bpy.context.window.scene=S
bpy.ops.object.select_all(action='DESELECT')
selected=[]
for ob in S.objects:
 if ob.type=='MESH' and len(ob.data.vertices):ob.select_set(True);selected.append(ob.name)
assert all(n.startswith('palaceInterior ') for n in selected),selected
bpy.ops.export_scene.gltf(filepath=str(R/'public/gltf/castle/palaceInterior.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_extras=True)
print(json.dumps({'exportedObjects':len(selected),'activeSceneOnly':True}))
