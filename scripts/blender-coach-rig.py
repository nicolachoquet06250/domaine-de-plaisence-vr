"""Rebuild the approved coach straight, then skin and animate both horses locally.

Executed through the telemetry-disabled local Blender MCP. Never rewrites the
original coach, terrace, gate, or an open user's blend file.
"""
import bpy, math, json, struct, re
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion

ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
EVID=ROOT/'artifacts/coach-journey-rig'; EVID.mkdir(parents=True,exist_ok=True)
OUT=ROOT/'public/gltf/arrival-coach'

# Execute the existing approved modelling recipe in an isolated namespace, before
# its decorative route warp. Split wheels during construction, not by proximity.
source=(ROOT/'scripts/blender-arrival-coach.py').read_text(encoding='utf-8')
source=source[source.index('# Reuse the exact'):source.index('# Placement is measured')]
source=source.replace("gate_obj=finish(gate);export('wicket',[gate_obj])", "gate_obj=finish(gate);gate_obj.hide_render=True;gate_obj.hide_set(True)")
start=source.index('# Four real spoked wheels:')
end=source.index('coach_obj=finish(coach)',start)
block=source[start:end]
block=block.replace('for x,r in', 'wheel_objects=[]\nfor x,r in',1)
block=block.replace(' for z in [-1.03,1.03]:', " for z in [-1.03,1.03]:\n  wheel=Builder('Wheel'+('Rear' if x<0 else 'Front')+('L' if z<0 else 'R'))")
block=block.replace('ring(coach,','ring(wheel,').replace('ell(coach,','ell(wheel,')
block=block.replace('  coach.tube(', '  wheel.tube(').replace('   coach.tube(', '   wheel.tube(')
block += "  wheel_obj=finish(wheel)\n  pivot=Vector((x,-z,r))\n  for vertex in wheel_obj.data.vertices:vertex.co-=pivot\n  wheel_obj.location=pivot\n  wheel_objects.append(wheel_obj)\n"
source=source[:start]+block+source[end:]
ns={'ROOT':ROOT,'bpy':bpy,'math':math,'json':json,'Path':Path,'Vector':Vector}
exec(compile(source,'approved-coach-straight-rebuild','exec'),ns)
scene=ns['scene']; scene.name='Royal coach - two skinned walking horses'
coach=ns['coach_obj']; horses=ns['horses']; wheels=ns['wheel_objects']
scene.render.fps=30

def xyz(p): return Vector((p[0],-p[2],p[1]))
def smooth(a,b,v):
 t=max(0,min(1,(v-a)/(b-a)));return t*t*(3-2*t)
rigs=[]; rig_reports=[]

for number,zbase in enumerate([-.64,.64],1):
 body,detail=horses[(number-1)*2:number*2]
 data=bpy.data.armatures.new('HorseRig%d'%number)
 rig=bpy.data.objects.new('HorseRig%d'%number,data);scene.collection.objects.link(rig)
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.object.mode_set(mode='EDIT')
 rest={}
 def bone(name,head,tail,parent=None):
  b=data.edit_bones.new(name);b.head=xyz(head);b.tail=xyz(tail)
  if parent:b.parent=data.edit_bones[parent]
  rest[name]=(Vector(head),Vector(tail));return b
 bone('Root',(3.9,1.25,zbase),(4.2,1.25,zbase))
 bone('Neck',(4.44,1.47,zbase),(4.96,2.18,zbase),'Root')
 bone('Head',(4.96,2.18,zbase),(5.42,1.78,zbase),'Neck')
 bone('Tail',(3.08,1.48,zbase),(2.94,.64,zbase),'Root')
 legs={}
 for part,x,kx,fx in [('Front',4.45,4.49,4.52),('Rear',3.41,3.34,3.39)]:
  for side,offset in [('L',-.205),('R',.205)]:
   name=part+side; zz=zbase+offset
   top=Vector((x,1.18,zz));knee=Vector((kx,.65,zz));ankle=Vector((fx,.155,zz));toe=Vector((fx+.055,.045,zz))
   bone(name+'Upper',top,knee,'Root');bone(name+'Lower',knee,ankle,name+'Upper');bone(name+'Foot',ankle,toe,name+'Lower')
   legs[name]=(top,knee,ankle,toe)
 bpy.ops.object.mode_set(mode='OBJECT')
 for obj in [body,detail]:
  obj.parent=rig
  groups={name:obj.vertex_groups.new(name=name) for name in rest}
  def weights(index,values):
   values={k:v for k,v in values.items() if v>1e-6};total=sum(values.values())
   for name,value in values.items():groups[name].add([index],value/total,'REPLACE')
  if obj is body:
   for vertex in obj.data.vertices:
    x,y,z=vertex.co.x,vertex.co.z,-vertex.co.y
    legpart='Front' if x>3.98 else 'Rear';side='L' if z<zbase else 'R';name=legpart+side
    top,knee,ankle,toe=legs[name]
    leg=max(0,1-smooth(.13,.35,abs(x-top.x)))*(1-smooth(.98,1.30,y))
    if y<.90 and abs(x-top.x)<.32:leg=1
    if leg>.001:
     foot=1-smooth(.12,.23,y);upper=smooth(.57,.74,y);lower=(1-foot)*(1-upper)
     weights(vertex.index,{'Root':1-leg,name+'Upper':leg*(1-foot)*upper,name+'Lower':leg*lower,name+'Foot':leg*foot})
    else:
     neck=smooth(4.35,4.71,x)*smooth(1.37,1.70,y);head=smooth(4.87,5.05,x)
     weights(vertex.index,{'Root':1-neck,'Neck':neck*(1-head),'Head':neck*head})
  else:
   # Connected sculpted components retain their shape: buckles, eyes, hooves,
   # individual mane locks and harness strips are bound as units.
   adjacent=[[] for _ in obj.data.vertices]
   for edge in obj.data.edges:
    a,b=edge.vertices;adjacent[a].append(b);adjacent[b].append(a)
   seen=set()
   for v in obj.data.vertices:
    if v.index in seen:continue
    pending=[v.index];seen.add(v.index);component=[]
    while pending:
     i=pending.pop();component.append(i)
     for j in adjacent[i]:
      if j not in seen:seen.add(j);pending.append(j)
    c=sum((obj.data.vertices[i].co for i in component),Vector())/len(component)
    x,y,z=c.x,c.z,-c.y
    if y<.16 and x>3.2:
     name=('Front' if x>4 else 'Rear')+('L' if z<zbase else 'R')+'Foot'
    elif x<3.13 and y>.25:name='Tail'
    elif x>4.95:name='Head'
    elif x>4.30 and y>1.65:name='Neck'
    else:name='Root'
    groups[name].add(component,1,'REPLACE')
  mod=obj.modifiers.new('Anatomical horse skin','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True
 rig.animation_data_create()
 rig_reports.append({'name':rig.name,'bones':len(rest),'vertices':sum(len(o.data.vertices) for o in [body,detail])})
 rigs.append(rig)

 def set_global_bone(name,head,tail):
  a=xyz(head);b=xyz(tail);rest_bone=data.bones[name]
  rotation=(rest_bone.tail_local-rest_bone.head_local).rotation_difference(b-a)
  desired=Matrix.Translation(a)@rotation.to_matrix().to_4x4()@rest_bone.matrix_local.to_quaternion().to_matrix().to_4x4()
  pb=rig.pose.bones[name]
  # Explicit conversion avoids dependency-graph lag while solving parent/child FK.
  parent=pb.parent
  pb.matrix_basis=rest_bone.convert_local_to_pose(desired,rest_bone.matrix_local,parent_matrix=parent.matrix if parent else Matrix.Identity(4),parent_matrix_local=parent.bone.matrix_local if parent else Matrix.Identity(4),invert=True)
  bpy.context.view_layer.update()

 for clip,frames in [('HorseIdle',90),('HorseWalk',36)]:
  action=bpy.data.actions.new(clip+'_'+str(number));rig.animation_data.action=action
  # Other NLA tracks must not influence the authored next action.
  for track in rig.animation_data.nla_tracks:track.mute=True
  for frame in range(frames+1):
   phase=math.tau*frame/frames
   for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
   # A moving horse flexes its shoulders/hips lower than the straight standing
   # bind pose. This gives the planted hoof a full stride without stretching the
   # leg chain or raising the stance hoof to satisfy an impossible reach.
   bob=-.12+.007*(1-math.cos(phase*2)) if clip=='HorseWalk' else .003*math.sin(phase)
   rig.pose.bones['Root'].location.z=bob
   rig.pose.bones['Neck'].rotation_mode='XYZ';rig.pose.bones['Neck'].rotation_euler.x=.014*math.sin(phase+number*.7)
   rig.pose.bones['Head'].rotation_mode='XYZ';rig.pose.bones['Head'].rotation_euler.x=.013*math.sin(phase+.5)
   rig.pose.bones['Tail'].rotation_mode='XYZ';rig.pose.bones['Tail'].rotation_euler.z=.035*math.sin(phase+number)
   bpy.context.view_layer.update()
   for leg_index,(name,(top,knee,ankle,toe)) in enumerate(legs.items()):
    if clip=='HorseIdle':continue
    # Four-beat walk, staggered across the pair. Ground-contact interval is 60%.
    offset={'RearL':0,'FrontL':.25,'RearR':.5,'FrontR':.75}[name]+(number-1)*.14
    t=(frame/frames+offset)%1
    if t<.6:dx=.39-.78*t/.6;lift=0
    else:
     swing=(t-.6)/.4;dx=-.39+.78*(swing*swing*(3-2*swing));lift=.13*math.sin(math.pi*swing)**2
    h=top+Vector((0,bob,0));target=ankle+Vector((dx,lift,0))
    l1=(knee-top).length;l2=(ankle-knee).length
    delta=target-h;dist=min(delta.length,l1+l2-.0001);axis=delta.normalized()
    along=(l1*l1-l2*l2+dist*dist)/(2*dist);perp=Vector((-axis.y,axis.x,0))
    bend=-1 if name.startswith('Front') else 1
    joint=h+axis*along+perp*(bend*math.sqrt(max(0,l1*l1-along*along)))
    # If the reach limit clips a target, preserve the rigid bone length.
    target=h+axis*dist
    set_global_bone(name+'Upper',h,joint)
    set_global_bone(name+'Lower',joint,target)
    set_global_bone(name+'Foot',target,target+(toe-ankle))
   for p in rig.pose.bones:
    p.keyframe_insert(data_path='location',frame=frame,group=p.name)
    p.keyframe_insert(data_path='rotation_euler' if p.rotation_mode!='QUATERNION' else 'rotation_quaternion',frame=frame,group=p.name)
    p.keyframe_insert(data_path='scale',frame=frame,group=p.name)
  rig.animation_data.action=None
  track=rig.animation_data.nla_tracks.new();track.name=clip
  strip=track.strips.new(clip,0,action);strip.name=clip
  # glTF merges equal NLA track names across the two rigs into one action.
 for track in rig.animation_data.nla_tracks:track.mute=False

scene.frame_start=0;scene.frame_end=90;scene.frame_set(0)
objects=[coach,*wheels,*horses,*rigs]
bpy.ops.object.select_all(action='DESELECT')
for obj in objects:obj.hide_set(False);obj.select_set(True)
bpy.context.view_layer.objects.active=rigs[0]
bpy.ops.export_scene.gltf(filepath=str(OUT/'royalCoachAnimated.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_yup=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_nla_strips=True,export_skins=True,export_image_format='AUTO',export_extras=True)
# Blender datablock names are globally unique, including other open scenes.
# Canonicalize only the exported node names, preserving every existing scene.
glb_path=OUT/'royalCoachAnimated.glb';payload=glb_path.read_bytes();json_size=struct.unpack_from('<I',payload,12)[0]
document=json.loads(payload[20:20+json_size]);binary_chunks=payload[20+json_size:]
for node in document['nodes']:
 if node.get('name','').startswith(('Wheel','HorseRig')):node['name']=re.sub(r'\.\d+$','',node['name'])
encoded=json.dumps(document,separators=(',',':'),ensure_ascii=False).encode('utf-8');encoded+=b' '*((-len(encoded))%4)
glb_path.write_bytes(struct.pack('<III',0x46546c67,2,20+len(encoded)+len(binary_chunks))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+binary_chunks)
for obj in [coach,*wheels,*horses]:obj.data.calc_loop_triangles()
report={'asset':'gltf/arrival-coach/royalCoachAnimated.glb','forward':'+X','seat':[-.6,2.1,0],'clips':{'HorseIdle':3,'HorseWalk':1.2},'walkNominalSpeed':.78/(1.2*.6),'rigs':rig_reports,'wheels':[{'name':o.name,'radius':.76 if 'Rear' in o.name else .59,'axis':'Z','position':[o.location.x,o.location.z,-o.location.y]} for o in wheels],'triangles':sum(len(o.data.loop_triangles) for o in [coach,*wheels,*horses]),'bytes':(OUT/'royalCoachAnimated.glb').stat().st_size}
(EVID/'rig-report.json').write_text(json.dumps(report,indent=2))
bpy.data.libraries.write(str(EVID/'attelage-chevaux-rigges.blend'),{scene},fake_user=True,compress=True)
print(json.dumps(report))
