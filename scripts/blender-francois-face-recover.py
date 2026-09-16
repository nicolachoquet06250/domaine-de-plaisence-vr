"""Reassemble morph meshes directly from their authored coordinates, without BMesh key remapping."""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/francois'
scene=bpy._natural_scene;bpy.context.window.scene=scene;m=bpy._natural_models['courtMale'];old=m['face']
with bpy.data.libraries.load(str(OUT/'renaissance-francois-work.blend'),link=False) as (src,dst):dst.scenes=[src.scenes[0]]
archive=dst.scenes[0]
parts=[o for o in archive.objects if o.name.startswith('courtMale') and o.type=='MESH' and o.data.shape_keys and not o.particle_systems]
parts.sort(key=lambda o:0 if 'Visage anatomique' in o.name else 1)
names=[k.name for k in parts[0].data.shape_keys.key_blocks];vv=[];ff=[];materials=[];mi=[];colors=[];groups=[];shape={n:[] for n in names}
for ob in parts:
    fibres='Duvet' in ob.name
    keep=[v.index for v in ob.data.vertices if not fibres or (v.index//9)%5 not in [0,1]]
    lookup={i:len(vv)+k for k,i in enumerate(keep)};base=ob.data.shape_keys.key_blocks['Basis']
    cmap=ob.data.color_attributes.get('Complexion')
    for i in keep:
        vv.append(tuple(base.data[i].co));colors.append(tuple(cmap.data[i].color) if cmap else (1,1,1,1))
        groups.append({ob.vertex_groups[g.group].name:g.weight for g in ob.data.vertices[i].groups})
        for name in names:shape[name].extend(ob.data.shape_keys.key_blocks[name].data[i].co)
    matmap={}
    for i,mat in enumerate(ob.data.materials):
        if mat not in materials:materials.append(mat)
        matmap[i]=materials.index(mat)
    for p in ob.data.polygons:
        if all(i in lookup for i in p.vertices):ff.append(tuple(lookup[i] for i in p.vertices));mi.append(matmap[p.material_index])
me=bpy.data.meshes.new('courtMale Visage coordonnees coherentes');me.from_pydata(vv,[],ff);me.update()
for mat in materials:me.materials.append(mat)
for p,i in zip(me.polygons,mi):p.material_index=i;p.use_smooth=True
col=me.color_attributes.new(name='Complexion',type='FLOAT_COLOR',domain='POINT')
col.data.foreach_set('color',[v for c in colors for v in c])
ob=bpy.data.objects.new('courtMale Visage anatomique Head final',me);scene.collection.objects.link(ob);ob.parent=m['rig']
for bone in m['rig'].data.bones:ob.vertex_groups.new(name=bone.name)
for i,ws in enumerate(groups):
    for name,w in ws.items():ob.vertex_groups[name].add([i],w,'REPLACE')
for name in names:
    key=ob.shape_key_add(name=name);key.data.foreach_set('co',shape[name]);key.value=0
mod=ob.modifiers.new('Humanoid deformation','ARMATURE');mod.object=m['rig']
ob['firstPersonHidden']=True;ob['beardConstruction']='continuous facial topology, shared visemes, direct coordinate assembly'
m['objects']=[ob if o==old else o for o in m['objects']];m['face']=ob;bpy.data.objects.remove(old,do_unlink=True)
# Retain the reusable proof that render geometry and morph Basis agree exactly.
error=max((v.co-k.co).length for v,k in zip(me.vertices,ob.data.shape_keys.key_blocks['Basis'].data))
assert error<1e-7,error
(OUT/'face-recovery.json').write_text(json.dumps({'parts':[o.name for o in parts],'vertices':len(vv),'basisMeshError':error},indent=2))
code=(ROOT/'scripts/blender-refined-export.py').read_text(encoding='utf-8-sig')
start=code.index("    for ob in m['objects']:");end=code.index('    for ob in joined:\n',start)
code=code[:start]+"    joined=m['objects'];gaps=[.0033]\n"+code[end:]
code=code.replace('artifacts/avatars/refined','artifacts/avatars/francois').replace('renaissance-refined.blend','renaissance-francois.blend')
exec(compile(code,'francois-reassembled-export','exec'))
