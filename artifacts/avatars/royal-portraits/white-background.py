import bpy
from pathlib import Path
root=Path(r'C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update/artifacts/avatars/royal-portraits')
for name in ['homme','femme']:
    path=root/(name+'-pose-royale.blend')
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene=bpy.context.scene
    scene.render.dither_intensity=0
    for node in scene.world.node_tree.nodes:
        if node.type=='BACKGROUND' and node.inputs['Strength'].default_value>.9:
            node.inputs['Strength'].default_value=2
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    bpy.ops.render.render(write_still=True)
    print('PURE_WHITE_RENDERED',name,flush=True)
exec(compile((root/'verify.py').read_text(),str(root/'verify.py'),'exec'))
