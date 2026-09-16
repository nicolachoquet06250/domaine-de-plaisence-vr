import bpy,math
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/francois'
scene=bpy._natural_scene;bpy.context.window.scene=scene
for im in bpy.data.images:
    if str(OUT).replace('\\','/') in im.filepath.replace('\\','/') and '-hair-' in im.name:
        im.scale(1024,256);im.filepath_raw=str(OUT/im.name.split('.png')[0])+'.png';im.file_format='PNG';im.save();im.pack()
m=bpy._natural_models['courtMale'];face=m['face'];colors=face.data.color_attributes['Complexion']
beardmat=next(i for i,mat in enumerate(face.data.materials) if 'Barbe mate' in mat.name)
beardfibremat={i for i,mat in enumerate(face.data.materials) if 'chatain profond' in mat.name}
fibreids={i for p in face.data.polygons if p.material_index in beardfibremat for i in p.vertices}
base=face.data.shape_keys.key_blocks[0]
for i,v in enumerate(base.data):
    x=v.co.x;h=v.co.z+.05;d=-v.co.y-.045
    if i in fibreids:
        w=math.exp(-(x/.045)**2)*math.exp(-((h-1.530)/.013)**2)*max(0,min(1,(d-.025)/.03))
        for key in face.data.shape_keys.key_blocks:key.data[i].co.z-=.0025*w
        continue
    # Taper the moustache down to the corners as in the portrait reference.
    u=abs(x);line=1.600-.019*smooth(u/.037)
    w=smooth((.037-u)/.005)*smooth((.0045-abs(h-line))/.002)*smooth((d-.064)/.009)
    if w:
        col=tuple(colors.data[i].color);target=(.019,.0065,.003)
        colors.data[i].color=(*(col[k]*(1-w)+target[k]*w for k in range(3)),1)
for p in face.data.polygons:
    if p.material_index in beardfibremat:continue
    if sum(colors.data[i].color[0] for i in p.vertices)/len(p.vertices)<.18:p.material_index=beardmat
# Export the already-optimised meshes without applying a second decimation pass.
code=(ROOT/'scripts/blender-refined-export.py').read_text(encoding='utf-8-sig')
start=code.index("    for ob in m['objects']:");end=code.index('    for ob in joined:\n',start)
code=code[:start]+"    joined=m['objects'];gaps=[.0033]\n"+code[end:]
code=code.replace('artifacts/avatars/refined','artifacts/avatars/francois').replace('renaissance-refined.blend','renaissance-francois.blend')
exec(compile(code,'francois-final-export','exec'))
