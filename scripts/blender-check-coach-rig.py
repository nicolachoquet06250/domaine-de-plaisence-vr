"""Local Blender deformation audit of the exported coach's source scene."""
import bpy,json,math
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
scene=next(s for s in reversed(list(bpy.data.scenes)) if s.name.startswith('Royal coach - two skinned'))
bpy.context.window.scene=scene
rigs=[o for o in scene.objects if o.type=='ARMATURE']
report={'horses':[]}
for rig in rigs:
 for track in rig.animation_data.nla_tracks:track.mute=track.name!='HorseWalk'
 obj=next(o for o in rig.children if o.type=='MESH' and 'criniere' in o.name)
 footgroups={g.index:g.name for g in obj.vertex_groups if g.name.endswith('Foot')}
 feet={name:[] for name in footgroups.values()}
 for v in obj.data.vertices:
  for g in v.groups:
   if g.group in footgroups:feet[footgroups[g.group]].append(v.index)
 samples=[]
 for frame in range(37):
  scene.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ev=obj.evaluated_get(dg)
  row={}
  for name,ids in feet.items():
   row[name]={'minY':min(ev.data.vertices[i].co.z for i in ids),'maxY':max(ev.data.vertices[i].co.z for i in ids),'meanX':sum(ev.data.vertices[i].co.x for i in ids)/len(ids)}
  samples.append(row)
 report['horses'].append({'name':rig.name,'minimumHoofY':min(f['minY'] for row in samples for f in row.values()),'maximumHoofLift':max(f['minY'] for row in samples for f in row.values()),'samples':samples})
 for track in rig.animation_data.nla_tracks:track.mute=False
scene.frame_set(0)
(ROOT/'artifacts/coach-journey-rig/deformation-check.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:[{a:b for a,b in h.items() if a!='samples'} for h in v] for k,v in report.items()}))
