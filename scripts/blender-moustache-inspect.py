import bpy,json
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/moustache'
scene=bpy.context.scene;bpy._natural_scene=scene;models={}
for asset in ['courtMale','courtFemale']:
    rig=next(o for o in scene.objects if o.type=='ARMATURE' and o.name.startswith(asset))
    obs=[o for o in scene.objects if o.type=='MESH' and o.parent==rig and not o.particle_systems]
    models[asset]={'rig':rig,'objects':obs,'face':next(o for o in obs if o.data.shape_keys)}
bpy._natural_models=models;bpy._organic_emitters=[o for o in scene.objects if o.particle_systems]
m=models['courtMale'];face=m['face']
keys=face.data.shape_keys.key_blocks
report={'scene':scene.name,'face':face.name,'materials':[m.name for m in face.data.materials],'vertices':len(face.data.vertices),'keys':[k.name for k in keys],
 'basisMeshError':max((v.co-k.co).length for v,k in zip(face.data.vertices,keys[0].data)),
 'nearLip':[(v.index,tuple(v.co),tuple(face.data.color_attributes['Complexion'].data[v.index].color)) for v in face.data.vertices if abs(v.co.x)<.006 and 1.536<v.co.z<1.563 and -v.co.y>.12]}
(OUT/'inspection.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
