"""Local Blender MCP: low royal wicket and carved carriage with two harnessed horses.
Y-up metres. Originals and collision proxies are deliberately preserved.
"""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Vector
import numpy as np
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
OUT=ROOT/'public/gltf/arrival-coach'; OUT.mkdir(parents=True,exist_ok=True)
EVID=ROOT/'artifacts/arrival-coach'; EVID.mkdir(parents=True,exist_ok=True)

# Regenerate the same terrace, omitting precisely two east parapet bays.
# No other terrace geometry or placement changes; closed collision stays separate.
source=(ROOT/'scripts/blender-arrival-realistic.py').read_text(encoding='utf-8')
source=source.replace("ARR_ROOT/'public/gltf/arrival'", "ARR_ROOT/'public/gltf/arrival-coach'")
source=source.replace("ARR_ROOT/'artifacts/arrival-realistic'", "ARR_ROOT/'artifacts/arrival-coach'")
source=source.replace('gltf/arrival/arrival.glb','gltf/arrival-coach/arrival.glb')
source=source.replace('for i in range(40):\n', 'for i in range(40):\n    if i in (9,10): continue\n')
source=source.replace("bpy.ops.wm.save_as_mainfile(filepath=str(ARR_EVID/'arrival-realistic.blend'),compress=True)", "bpy.data.libraries.write(str(ARR_EVID/'terrasse-avec-ouverture.blend'),{arr_scene},fake_user=True,compress=True)")
exec(compile(source,'arrival-opening','exec'),{})

# Reuse the exact modelling vocabulary and metal materials of the castle gate.
source=(ROOT/'scripts/blender-royal-enclosure.py').read_text(encoding='utf-8').split("gate=Builder(")[0]
exec(compile(source,'royal-helpers','exec'),globals())
OUT=ROOT/'public/gltf/arrival-coach'; EVID=ROOT/'artifacts/arrival-coach'
scene.name='Attelage royal et portillon accueil'
wood=mat('Noyer sculpte et cire',(.22,.074,.021),0,.42)
red=mat('Velours cramoisi',(.24,.012,.022),0,.86)
leather=mat('Cuir noir des harnais',(.018,.012,.009),0,.48)
bay=mat('Robe baie acajou',(.22,.069,.022),0,.57)
chestnut=mat('Robe alezane',(.32,.12,.04),0,.58)
hair=mat('Crins brun noir',(.022,.010,.006),0,.84)
hoof=mat('Corne des sabots',(.052,.039,.026),0,.65)
eye=mat('Yeux humides',(.008,.006,.004),0,.16)
ivory=mat('Balezanes et liste ivoire',(.69,.64,.52),0,.79)
materials.extend([wood,red,leather,bay,chestnut,hair,hoof,eye,ivory])
# Packed 512px timber texture: long fibres and growth bands, baked glTF compatible.
yy,xx=np.mgrid[0:512,0:512]/512; rng=np.random.default_rng(1670)
grain=.78+.15*np.sin((yy+.035*np.sin(xx*math.tau))*math.tau*38)+.07*rng.random((512,512))
pixels=np.ones((512,512,4),dtype=np.float32); pixels[:,:,:3]=grain[:,:,None]*np.array([.30,.115,.038])
im=bpy.data.images.new('Noyer - fibres fines',width=512,height=512); im.pixels.foreach_set(pixels.ravel()); im.pack()
nt=wood.node_tree; tex=nt.nodes.new('ShaderNodeTexImage'); tex.image=im
nt.links.new(tex.outputs['Color'],next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED').inputs['Base Color'])

def finish(builder,smooth=False):
 obj=builder.mesh()
 uv=obj.data.uv_layers.new(name='UVMap')
 for p in obj.data.polygons:
  p.use_smooth=smooth
  for li in p.loop_indices:
   v=obj.data.vertices[obj.data.loops[li].vertex_index].co
   uv.data[li].uv=(v.x,v.y) if abs(p.normal.z)>.6 else ((v.x,v.z) if abs(p.normal.y)>.6 else (v.y,v.z))
 return obj

def ell(b,c,r,material=7,tilt=0,n=20,k=12):
 v=[]; f=[]
 for j in range(k+1):
  a=-math.pi/2+math.pi*j/k
  for i in range(n):
   t=i*math.tau/n; x=r[0]*math.cos(a)*math.cos(t); y=r[1]*math.sin(a); z=r[2]*math.cos(a)*math.sin(t)
   v.append((c[0]+x*math.cos(tilt)-y*math.sin(tilt),c[1]+x*math.sin(tilt)+y*math.cos(tilt),c[2]+z))
 for j in range(k):
  for i in range(n):a=j*n+i;d=j*n+(i+1)%n;f.append((a,d,d+n,a+n))
 b.add(v,f,material)

def ring(b,c,rx,ry,r,ma=1,n=40,plane='xy'):
 pts=[]
 for a in np.linspace(0,math.tau,n+1):
  pts.append((c[0]+rx*math.cos(a),c[1]+ry*math.sin(a),c[2]) if plane=='xy' else (c[0]+rx*math.cos(a),c[1],c[2]+ry*math.sin(a)))
 b.tube(pts,r,ma,6)

# Portillon local X across opening, placed at east tangent by the scene JSON.
gap=2*7.65*math.sin(math.pi/20); gx=7.65*math.cos(math.pi/20)
gate=Builder('Portillon - fleurs de lys volutes et medaillon royal')
for side in [-1,1]:
 x=side*gap/2
 for y,w,h in [(.10,.34,.20),(.54,.25,.70),(.94,.34,.1),(1.04,.36,.1)]:gate.box(x,y,0,w,h,.38,2)
 gate.box(x,1.101,0,.33,.026,.36,1)
 # Leaves top at the same 1.09 m as the balustrade, including fleur tips.
 for xx in [side*.035,side*(gap/2-.18)]:gate.box(xx,.52,0,.043,.87,.055)
 for y in [.12,.35,.91]:gate.box(side*(gap/4-.075),y,0,gap/2-.20,.035,.055)
 for xx in np.linspace(.14,gap/2-.26,7):
  gate.box(side*xx,.535,0,.023,.79,.027);gate.fleur(side*xx,.92,0,.17)
 for xx in [.26,.72]:
  for flip in [-1,1]:gate.scroll(side*xx+flip*.06,.24,.035,.10,flip,material=1)
 for flip in [-1,1]:gate.scroll(side*.55+flip*.12,.63,.04,.19,flip,material=1)
 for y in [.23,.79]:gate.box(side*(gap/2-.15),y,0,.09,.065,.085,1)
gate.outline([(0,.37),(.16,.47),(.16,.77),(-.16,.77),(-.16,.47)],.045,3)
gate.tube([(0,.37,.028),(.16,.47,.028),(.16,.77,.028),(-.16,.77,.028),(-.16,.47,.028),(0,.37,.028)],.015,1,5)
gate.fleur(0,.46,.036,.25)
for y in [.80,.85]:ring(gate,(0,y,0),.17,.075,.014,1,24,'xz')
for a in np.linspace(0,math.tau,7)[:-1]:
 gate.tube([(.16*math.cos(a)*math.cos(t),.85+.12*math.sin(t),.07*math.sin(a)*math.cos(t)) for t in np.linspace(0,math.pi/2,9)],.009,1,5)
gate.box(0,1.00,0,.02,.08,.02,1);gate.box(0,1.01,0,.065,.02,.02,1)
gate_obj=finish(gate);export('wicket',[gate_obj])

# Coach points along +X. Carriage centre is the placement anchor, 5 m from wicket.
coach=Builder('Voiture royale - noyer grave panneaux sculptes et dorures')
for z in [-.61,.61]:
 coach.box(0,.73,z,3.30,.15,.16,4)
 for axle in [-1.25,1.10]:
  for dy in [0,.035,.070]:
   coach.tube([(axle+t,.66+dy+.25*(t/.66)**2,z) for t in np.linspace(-.66,.66,15)],.026,0,5)
coach.box(0,.99,0,2.80,.19,1.47,4)
# Curved tumblehome body, with open windows and a canopy rather than opaque panes.
for z in [-.73,.73]:
 sign=1 if z>0 else -1
 coach.box(0,1.39,z,2.45,.65,.09,4)
 for x in [-1.21,-.49,.49,1.21]:
  coach.box(x,2.10,z,.11,1.46,.10,4)
  coach.box(x,2.10,z+sign*.065,.028,1.40,.018,1)
 for y in [1.08,1.18,1.64,1.75,2.58,2.68]:coach.box(0,y,z,2.55,.035,.14,1)
 # Actual recessed panel outlines, rosettes, acanthus curls and engraved strokes.
 for x in [-.86,0,.86]:
  w=.63 if x else .83
  coach.tube([(x-w/2,1.25,z+sign*.06),(x+w/2,1.25,z+sign*.06),(x+w/2,1.57,z+sign*.06),(x-w/2,1.57,z+sign*.06),(x-w/2,1.25,z+sign*.06)],.019,1,5)
  for flip in [-1,1]:
   coach.scroll(x+flip*.15,1.41,z+sign*.08,.16,flip,material=1)
  if x:coach.fleur(x,1.31,z+sign*.09,.21)
 for j in range(27):
  x=-1.19+j*.092
  coach.tube([(x,1.16,z+sign*.082),(x+.025,1.20,z+sign*.092),(x+.05,1.16,z+sign*.082)],.009,1,5)
 # Heraldic central door escutcheon.
 ring(coach,(0,1.42,z+sign*.10),.14,.19,.016,1,24)
 coach.fleur(0,1.31,z+sign*.11,.22)
 coach.box(.35,1.87,z+sign*.10,.13,.035,.035,1)
 # Velvet drapes tied back, keeping the cabin visibly hollow.
 for x in [-1.13,-.57,.57,1.13]:
  for q in range(3):coach.tube([(x+(q-1)*.03,2.57,z-sign*.04),(x+(q-1)*.013,2.23,z-sign*.025),(x+(q-1)*.04,1.79,z-sign*.02)],.035,5,7)
  coach.box(x,2.18,z,.13,.028,.11,1)
 # Double step under the door and supporting brackets.
 for y,zz in [(.62,1.02),(.83,.86)]:coach.box(0,y,sign*zz,.76,.07,.30,4)
 for x in [-.30,.30]:coach.tube([(x,.61,sign*1.13),(x,.63,sign*.85),(x,1.0,sign*.65)],.027,0,6)
for x in [-1.22,1.22]:
 coach.box(x,1.42,0,.10,.66,1.45,4)
 for z in [-.7,0,.7]:coach.box(x,2.12,z,.10,.91,.075,4)
 coach.box(x,2.61,0,.13,.10,1.5,1)
# Interior facing upholstered seats, visible through windows.
for x in [-.92,.92]:
 coach.box(x,1.38,0,.49,.18,1.28,5);coach.box(x*1.22,1.70,0,.14,.70,1.27,5)
 for z in [-.42,0,.42]:ell(coach,(x*1.22,1.83,z),(.083,.035,.035),1,n=10,k=6)
# Gently domed roof constructed as continuous strips.
v=[];f=[]
for x in [-1.40,1.40]:
 for i in range(17):
  z=-.86+i/16*1.72;v.append((x,2.73+.20*(1-(z/.86)**2),z))
for i in range(16):f.append((i,i+1,18+i,17+i))
v.extend([(x,y-.055,z) for x,y,z in v[:]])
f.extend([tuple(i+34 for i in reversed(face)) for face in f[:]])
for edge in [list(range(17)),list(range(17,34)),[0,17],[16,33]]:
 for a,b in zip(edge,edge[1:]):f.append((a,b,b+34,a+34))
coach.add(v,f,4)
for x in [-1.40,1.40]:coach.tube([(x,2.73+.20*(1-(z/.86)**2),z) for z in np.linspace(-.86,.86,25)],.048,1,6)
for z in [-.86,.86]:coach.box(0,2.73,z,2.88,.10,.09,1)
for x in [-1.2,0,1.2]:
 for z in [-.77,.77]:coach.fleur(x,2.80,z,.24)
ring(coach,(0,2.96,0),.26,.21,.029,1,26,'xz')
for a in np.linspace(0,math.tau,7)[:-1]:coach.tube([(.26*math.cos(a)*math.cos(t),2.97+.26*math.sin(t),.21*math.sin(a)*math.cos(t)) for t in np.linspace(0,math.pi/2,9)],.018,1,6)
coach.box(0,3.28,0,.025,.15,.025,1);coach.box(0,3.30,0,.10,.025,.025,1)
# Driver's sprung seat, footboard, tongue and crossbar.
coach.box(1.63,1.38,0,.62,.16,1.22,5);coach.box(1.38,1.66,0,.11,.54,1.24,4)
for z in [-.57,.57]:coach.tube([(1.35,.8,z),(1.58,1.35,z),(1.93,1.35,z)],.07,4,8)
coach.box(2.05,.97,0,.56,.09,1.25,4)
coach.tube([(1.1,.64,0),(2.8,.56,0),(4.48,.70,0)],.065,4,8)
coach.box(2.7,.61,0,.13,.13,2.05,4)
# Four real spoked wheels: iron tyres, timber felloes, hubs and gold spoke edges.
for x,r in [(-1.25,.76),(1.10,.59)]:
 coach.tube([(x,r,-1.14),(x,r,1.14)],.065,0,8)
 for z in [-1.03,1.03]:
  ring(coach,(x,r,z),r-.045,r-.045,.067,4,56)
  ring(coach,(x,r,z),r-.015,r-.015,.024,0,56)
  ring(coach,(x,r,z+(.06 if z>0 else -.06)),r-.07,r-.07,.014,1,48)
  coach.tube([(x,r,z-.13),(x,r,z+.13)],.12,4,12)
  ell(coach,(x,r,z+(.14 if z>0 else -.14)),(.105,.105,.055),1,n=16,k=8)
  for a in np.linspace(0,math.tau,15)[:-1]:
   coach.tube([(x+.11*math.cos(a),r+.11*math.sin(a),z),(x+(r-.09)*math.cos(a),r+(r-.09)*math.sin(a),z)],.034,4,6)
   coach.tube([(x+.16*math.cos(a),r+.16*math.sin(a),z+.035),(x+(r-.11)*math.cos(a),r+(r-.11)*math.sin(a),z+.035)],.008,1,5)
coach_obj=finish(coach)

horses=[]
for number,zbase in enumerate([-.64,.64],1):
 body=Builder('Cheval %s - anatomie continue'%number); m=6+number
 # Barrel, hindquarters, shoulders and rising neck overlap before voxel fusion.
 for c,r,tilt in [((3.92,1.26,zbase),(.87,.42,.29),0),((3.38,1.35,zbase),(.40,.39,.30),0),((4.48,1.38,zbase),(.32,.43,.28),-.18),((4.73,1.83,zbase),(.255,.55,.21),-.38),((5.02,2.16,zbase),(.19,.235,.155),.30),((5.23,1.95,zbase),(.34,.14,.13),-.85),((5.41,1.75,zbase),(.165,.115,.135),-.35)]:ell(body,c,r,m,tilt)
 for side in [-1,1]:
  zz=zbase+side*.205
  # Front: shoulder -> elbow -> knee -> fetlock; hind: thigh -> hock -> fetlock.
  for c,r,tilt in [((4.45,1.04,zz),(.15,.34,.13),.04),((4.49,.69,zz),(.075,.18,.075),0),((4.49,.41,zz),(.047,.24,.050),0),((4.52,.16,zz),(.085,.09,.072),-.30),((3.41,1.02,zz),(.22,.33,.17),-.35),((3.51,.70,zz),(.12,.20,.10),-.55),((3.34,.46,zz),(.062,.18,.056),.26),((3.37,.19,zz),(.055,.18,.055),-.20)]:ell(body,c,r,m,tilt,n=16,k=10)
  ell(body,(4.98+side*.015,2.43,zbase+side*.105),(.050,.14,.048),m,-.15,n=12,k=10)
 obj=finish(body,True);bpy.context.view_layer.objects.active=obj
 rem=obj.modifiers.new('Sculpture continue de la musculature','REMESH');rem.mode='VOXEL';rem.voxel_size=.022;rem.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rem.name)
 sm=obj.modifiers.new('Lissage de la robe','SMOOTH');sm.factor=1.0;sm.iterations=4;bpy.ops.object.modifier_apply(modifier=sm.name)
 dec=obj.modifiers.new('Optimisation Quest','DECIMATE');dec.ratio=.34;bpy.ops.object.modifier_apply(modifier=dec.name)
 # Voxel remesh drops face material indices. Reapply the coat explicitly.
 obj.data.materials.clear();obj.data.materials.append(materials[m])
 for polygon in obj.data.polygons:polygon.material_index=0;polygon.use_smooth=True
 horses.append(obj)
 detail=Builder('Cheval %s - criniere queue sabots yeux et harnachement'%number)
 for side in [-1,1]:
  zz=zbase+side*.205
  for x in [4.55,3.41]:
   # Hoof uses a tapered flat-bottom solid, toe forward.
   vv=[]
   for y,s in [(0,1),(.12,.78)]:
    for a in np.linspace(0,math.tau,13)[:-1]:vv.append((x+.105*s*math.cos(a),y,zz+.080*s*math.sin(a)))
   ff=[tuple(reversed(range(12))),tuple(range(12,24))]+[(i,(i+1)%12,(i+1)%12+12,i+12) for i in range(12)]
   detail.add(vv,ff,10)
   ring(detail,(x,.128,zz),.094,.073,.012,10,16,'xz')
  ell(detail,(5.10,2.13,zbase+side*.173),(.049,.040,.018),11,n=16,k=8)
  ell(detail,(5.42,1.80,zbase+side*.131),(.057,.027,.018),9,.3,n=12,k=8)
  # Headstall follows head contour with noseband, cheekpieces and bit rings.
  detail.tube([(4.97,2.33,zbase+side*.15),(5.06,2.10,zbase+side*.19),(5.40,1.72,zbase+side*.15)],.019,6,6)
  ring(detail,(5.36,1.70,zbase+side*.17),.05,.05,.013,1,16)
  # Breast collar, traces and reins connect the pair to the carriage.
  detail.tube([(4.49,1.71,zbase+side*.26),(4.70,1.29,zbase+side*.31),(4.47,1.01,zbase+side*.24)],.04,6,7)
  detail.tube([(4.65,1.31,zbase+side*.29),(3.72,.93,zbase+side*.35),(2.7,.63,zbase+side*.28)],.023,6,6)
  detail.tube([(5.35,1.69,zbase+side*.18),(4.0,1.46,zbase+side*.35),(2.8,1.36,zbase*.8),(1.73,1.55,side*.15)],.009,6,5)
  for x,y in [(4.59,1.40),(3.93,1.58),(5.07,2.15)]:ell(detail,(x,y,zbase+side*.30 if x<5 else zbase+side*.20),(.034,.045,.013),1,n=10,k=6)
 # Girth and backpad wrap around the barrel rather than float above it.
 detail.tube([(3.94,1.26+.41*math.cos(a),zbase+.31*math.sin(a)) for a in np.linspace(0,math.tau,33)],.032,6,7)
 detail.box(3.94,1.67,zbase,.24,.06,.29,6)
 # Many tapered locks form a continuous crest and full rear tail.
 for j in range(22):
  t=j/21; x=4.27+.61*t;y=1.72+.66*t
  detail.tube([(x,y,zbase),(x-.045,y-.015,zbase+.13),(x+.045,y-.16,zbase+.24)],.038,9,7)
 for j in range(15):
  a=j*math.tau/15
  detail.tube([(3.06,1.49,zbase),(2.96,1.19,zbase+.045*math.cos(a)),(2.91,.68,zbase+.08*math.cos(a)),(2.97,.25,zbase+.055*math.sin(a))],.023,9,7)
 # Forelock between the ears and fine muzzle split.
 for j in range(5):detail.tube([(5.02,2.34,zbase+(j-2)*.025),(5.20,2.19,zbase+(j-2)*.03)],.022,9,6)
 if number==2:
  detail.tube([(5.16,2.27,zbase),(5.29,2.10,zbase),(5.43,1.94,zbase),(5.52,1.83,zbase)],.022,12,7)
 detail.tube([(5.48,1.70,zbase-.09),(5.53,1.68,zbase),(5.48,1.70,zbase+.09)],.007,9,5)
 horses.append(finish(detail,True))

# Placement is measured along the existing path from the wicket tangent.
samples=json.loads((ROOT/'artifacts/royal-enclosure/model-stats.json').read_text())['pathSamples']
remain=5-(samples[0][0]-gx);position=None;direction=None
for a,b in zip(samples,samples[1:]):
 d=math.dist(a,b)
 if remain<=d:
  t=remain/d;position=[a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])];direction=[(b[0]-a[0])/d,(b[1]-a[1])/d];break
 remain-=d
assert position is not None
yaw=-math.degrees(math.atan2(direction[1],direction[0]))
radius=math.hypot(*position);height=.048+.18*math.sin(math.pi*min(1,max(0,(radius-8)/16)))**2
# Follow the bend: the drawbar, traces and horses stay within the gravel ribbon.
# The coach remains rigid; only the flexible front of the decorative assembly curves.
arc=[0.0]
for a,b in zip(samples,samples[1:]):arc.append(arc[-1]+math.dist(a,b))
anchor_arc=5-(samples[0][0]-gx)
def path_at(distance):
 for i in range(len(arc)-1):
  if arc[i+1]>=distance:
   t=(distance-arc[i])/(arc[i+1]-arc[i]);a=samples[i];b=samples[i+1]
   return np.array(a)+(np.array(b)-np.array(a))*t,(np.array(b)-np.array(a))/(arc[i+1]-arc[i])
 return np.array(samples[-1]),np.array(direction)
ang=math.radians(yaw);c=math.cos(ang);s=math.sin(ang)
for obj in [coach_obj,*horses]:
 for vertex in obj.data.vertices:
  x,z,y=vertex.co.x,-vertex.co.y,vertex.co.z
  if x<=2.1:continue
  centre,tangent=path_at(anchor_arc+x);normal=np.array([-tangent[1],tangent[0]])
  point=centre+normal*z;delta=point-np.array(position)
  nx=delta[0]*c-delta[1]*s;nz=delta[0]*s+delta[1]*c
  r=float(np.linalg.norm(point));ground=.048+.18*math.sin(math.pi*min(1,max(0,(r-8)/16)))**2
  blend=min(1,(x-2.1)/.65)
  vertex.co=(x+(nx-x)*blend,-(z+(nz-z)*blend),y+(ground-height)*blend)
 obj.data.update()
export('royalCoach',[coach_obj,*horses])
report={'assets':stats,'gatePosition':[gx,0,0],'gateRotationDeg':[0,90,0],'openingWidth':gap,'gateHeight':1.114,'coachPosition':[position[0],height,position[1]],'coachRotationDeg':[0,yaw,0],'distanceAlongPath':5,'horseCount':2,'collision':'Original arrivalCollision and arrivalBoundary retained unchanged'}
(EVID/'model-stats.json').write_text(json.dumps(report,indent=2))
bpy.data.libraries.write(str(EVID/'attelage-royal-et-portillon.blend'),{scene},fake_user=True,compress=True)
print(json.dumps(report))
