import bpy,json
bpy.ops.wm.open_mainfile(filepath=r'C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update/artifacts/scene-fbx/scene-composee.blend')
g=bpy.data.objects['castle__door-entrance'];print('DOORS',[(o.name,[m.name for m in o.data.materials]) for o in g.children if o.type=='MESH']);o=bpy.data.objects['Interieur_Chateau'];print('INTERIOR MATS',[(i,m.name) for i,m in enumerate(o.data.materials)]);print('FOUNTAIN',[(o.name,[m.name for m in o.data.materials]) for o in bpy.data.objects if o.type=='MESH' and o.parent and o.parent.name.startswith('fountain')])
