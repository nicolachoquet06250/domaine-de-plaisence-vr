import bpy
from pathlib import Path
root=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
COUT=root/'public/gltf/castle';CEVID=root/'artifacts/castle'
cscene=next((s for s in bpy.data.scenes if s.name.startswith('Chateau - Architecture et interieur')),None)
if cscene is None:
    with bpy.data.libraries.load(str(CEVID/'chateau-plaisance.blend'),link=False) as (source,target):
        target.scenes=[next(name for name in source.scenes if name.startswith('Chateau - Architecture et interieur'))]
    cscene=target.scenes[0]
bpy.context.window.scene=cscene
for obj in list(cscene.objects):
    if obj.name.startswith('Portrait historique '):
        for child in list(obj.children_recursive):bpy.data.objects.remove(child,do_unlink=True)
        bpy.data.objects.remove(obj,do_unlink=True)
for name,asset,x in [('Francois Ier','bustFrancoisI',-12.8),('Louis XIV','bustLouisXIV',12.8)]:
    existing=set(cscene.objects)
    bpy.ops.import_scene.gltf(filepath=str(COUT/(asset+'.glb')))
    imported=set(cscene.objects)-existing
    assembly=bpy.data.objects.new('Portrait historique '+name,None);cscene.collection.objects.link(assembly)
    for obj in imported:
        if obj.parent not in imported: obj.parent=assembly
    assembly.location=(x,-1,6.14)
bpy.ops.wm.save_as_mainfile(filepath=str(CEVID/'chateau-plaisance-coiffures.blend'),compress=True)
print('Historical portrait busts placed on their upstairs pedestals')
