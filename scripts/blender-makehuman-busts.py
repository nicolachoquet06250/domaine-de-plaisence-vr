"""Four reference-led marble portraits. MakeHuman CC0 anatomical topology.
All custom surfaces are authored meshes, not primitive operators. Run via Blender MCP.
Input coordinates: X right, Y up, Z towards viewer. Busts rest at Y=0.
"""
import bpy, math, json, random
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
OUT=R/'artifacts/busts-makehuman'; OUT.mkdir(exist_ok=True,parents=True)
S=bpy.data.scenes.new('Quatre portraits historiques - MakeHuman');bpy.context.window.scene=S
S.unit_settings.system='METRIC';S.gravity=(0,0,-9.81)
TAU=math.tau
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def gauss(x,c,w):return math.exp(-((x-c)/w)**2)
def interp(rows,t):
 for a,b in zip(rows,rows[1:]):
  if t<=b[0]:
   u=smooth((t-a[0])/(b[0]-a[0]));return tuple(a[k]*(1-u)+b[k]*u for k in range(1,len(a)))
 return rows[-1][1:]
def mat(name,c,rough):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough
 return m
stone=mat('Marbre ivoire - anatomie',(.71,.685,.62),.48)
hairmat=mat('Marbre ivoire - chevelure ciselee',(.65,.624,.56),.60)
cloth=mat('Marbre ivoire - drapes',(.69,.665,.60),.57)
detail=mat('Marbre ivoire - ornements polis',(.76,.73,.66),.39)
iris=mat('Iris graves dans le marbre',(.40,.38,.34),.65)
objects=[];models={};stats={}
def mesh(name,v,f,m=stone,sub=0):
 me=bpy.data.meshes.new(asset+' '+name);me.from_pydata([(p[0],-p[2],p[1]) for p in v],[],f);me.update()
 ob=bpy.data.objects.new(asset+' '+name,me);S.collection.objects.link(ob);me.materials.append(m)
 for p in me.polygons:p.use_smooth=True
 objects.append(ob)
 if sub:
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
  mod=ob.modifiers.new('Subdivision anatomique','SUBSURF');mod.levels=sub;bpy.ops.object.modifier_apply(modifier=mod.name)
 return ob
def tube(name,points,r,m=detail,n=8,radii=None):
 vv=[];ff=[];pp=list(map(Vector,points))
 for i,p in enumerate(pp):
  t=(pp[min(i+1,len(pp)-1)]-pp[max(0,i-1)]).normalized();a=t.cross(Vector((0,0,1)))
  if a.length<.01:a=t.cross(Vector((0,1,0)))
  a.normalize();b=t.cross(a);rr=r if radii is None else radii[i]
  for k in range(n):vv.append(p+rr*(a*math.cos(k*TAU/n)+b*math.sin(k*TAU/n)))
 for i in range(len(pp)-1):
  for k in range(n):q=i*n+k;ff.append((q,i*n+(k+1)%n,(i+1)*n+(k+1)%n,q+n))
 ff.extend([tuple(reversed(range(n))),tuple((len(pp)-1)*n+k for k in range(n))]);return mesh(name,vv,ff,m)
def loft(name,rings,m=cloth,n=80,pleat=0):
 vv=[];ff=[]
 for j,(h,rx,rz,d) in enumerate(rings):
  for i in range(n):
   a=i*TAU/n;w=1+pleat*math.sin(14*a+j*.42)*math.sin(math.pi*j/(len(rings)-1));vv.append((rx*math.sin(a)*w,h,d+rz*math.cos(a)*w))
 for j in range(len(rings)-1):
  for i in range(n):q=j*n+i;ff.append((q,j*n+(i+1)%n,(j+1)*n+(i+1)%n,q+n))
 ff.extend([tuple(reversed(range(n))),tuple((len(rings)-1)*n+i for i in range(n))]);return mesh(name,vv,ff,m,1)
raw=[];groups={};g=''
for line in (R/'artifacts/avatars/organic/reference/makehuman-base.obj').read_text().splitlines():
 p=line.split()
 if not p:continue
 if p[0]=='v':raw.append(tuple(map(float,p[1:4])))
 elif p[0]=='g':g=p[1]
 elif p[0]=='f':groups.setdefault(g,[]).append(tuple(int(a.split('/')[0])-1 for a in p[1:]))
def anatomy(p):
 x,y,z=p;fem=identity in ['Catherine','Anne'];front=smooth((z-.35)/.65)
 xx=x*.104*(1+(.035 if fem else .11)*gauss(y,6.35,.45));h=.892+y*.104
 d=z*.104-.063+(.009 if fem else .018)*gauss(y,6.24,.38)*smooth((z-.2)/.7)
 # Portrait-specific continuous tissue deformations: bridge, tip, cheek, jaw and lips.
 if identity=='Francois':
  d+=.013*gauss(x,0,.19)*gauss(y,7.02,.47)*front;h-=.006*gauss(x,0,.20)*gauss(y,6.94,.18)*front
  xx*=1-.055*gauss(y,7.6,.6);d+=.003*gauss(abs(x),.47,.23)*gauss(y,7.02,.35)*front
 elif identity=='Louis':
  xx*=1+.12*gauss(y,6.60,.56);d+=.008*gauss(abs(x),.41,.24)*gauss(y,6.70,.44)*front
  d+=.009*gauss(x,0,.18)*gauss(y,7.02,.39)*front;h-=.003*gauss(abs(x),.22,.15)*gauss(y,6.7,.1)*front
  d-=.0023*gauss(abs(x),.28,.065)*gauss(y,6.95,.25)*front
 elif identity=='Catherine':
  xx*=1+.09*gauss(y,6.9,.47);d+=.006*gauss(abs(x),.43,.23)*gauss(y,6.95,.38)*front
  d+=.005*gauss(x,0,.15)*gauss(y,7.12,.35)*front;xx*=1-.11*gauss(y,6.67,.13)*front
  d+=.003*gauss(y,6.20,.20)*front;d-=.0018*gauss(abs(x),.29,.05)*gauss(y,6.95,.23)*front
 else:
  xx*=.91;h+=.005*gauss(y,7.95,.5);d+=.007*gauss(x,0,.15)*gauss(y,7.10,.40)*front
  xx*=1-.16*gauss(y,6.70,.13)*front;d-=.003*gauss(abs(x),.38,.20)*gauss(y,6.8,.35)*front
 return Vector((xx,h,d))
def bust(p):return Vector((p[0]*2.2,.30+(p[1]-1.443)*2.2,p[2]*2.2))
def human(p):return Vector((p[0]/2.2,(p[1]-.3)/2.2+1.443,p[2]/2.2))
def extend_neck(vv,ff):
 edges={}
 for f in ff:
  for a,b in zip(f,f[1:]+f[:1]):k=tuple(sorted((a,b)));edges[k]=edges.get(k,0)+1
 adj={}
 for (a,b),n in edges.items():
  if n==1 and max(vv[a].y,vv[b].y)<1.55:adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
 first=min(adj);loop=[first];prev=None;cur=first
 while True:
  nxt=next(i for i in adj[cur] if i!=prev)
  if nxt==first:break
  loop.append(nxt);prev,cur=cur,nxt
  assert len(loop)<=len(adj)
 top=[vv[i].copy() for i in loop];last=loop
 for j in range(1,7):
  t=j/6;ring=[]
  for p in top:
   a=math.atan2(p.x,p.z+.027);q=p.lerp(Vector((.049*math.sin(a),1.443,.043*math.cos(a))),smooth(t));q.y=p.y*(1-t)+1.443*t
   ring.append(len(vv));vv.append(q)
  for i in range(len(loop)):k=(i+1)%len(loop);ff.append((last[i],last[k],ring[k],ring[i]))
  last=ring
 ff.append(tuple(reversed(last)));return vv,ff
def head():
 fs=[f for f in groups['body'] if all(raw[i][1]>6.04 for i in f)];ids=sorted(set(i for f in fs for i in f));mp={i:j for j,i in enumerate(ids)}
 vv,ff=extend_neck([anatomy(raw[i]) for i in ids],[tuple(mp[i] for i in f) for f in fs])
 ob=mesh('Visage MakeHuman - levres paupieres oreilles menton',[bust(p) for p in vv],ff,stone,1)
 ob['anatomicalSource']='MakeHuman base.obj CC0';ob['portraitIdentity']=identity
 for side,sg in [('l',1),('r',-1)]:
  fs=groups['helper-'+side+'-eye'];ids=sorted(set(i for f in fs for i in f));mp={i:j for j,i in enumerate(ids)}
  mesh('Globe oculaire '+side,[bust(anatomy(raw[i])+Vector((0,0,.001))) for i in ids],[tuple(mp[i] for i in f) for f in fs],stone,1)
  center=anatomy((sg*.30775,7.28415,1.39))+Vector((0,0,.0018));vv=[];ff=[]
  for j,r in enumerate([0,.002,.0025,.0048,.005]):
   for k in range(40):
    a=k*TAU/40;vv.append(bust(center+Vector((r*math.cos(a),r*math.sin(a),-.001*(r/.005)**2))))
  for j in range(4):
   for k in range(40):q=j*40+k;ff.append((q,j*40+(k+1)%40,(j+1)*40+(k+1)%40,q+40))
  eye=mesh('Regard grave '+side,vv,ff,stone);eye.data.materials.append(iris)
  for p in eye.data.polygons:p.material_index=1 if p.index//40 in [0,3] else 0
 return ob

# Reuse the avatars' actual ear contour, with dense coherent volume beneath strands.
def hairline(a):
 u=abs((a+math.pi)%TAU-math.pi)
 rows=[(0,1.704),(.45,1.701),(.82,1.684),(1.04,1.642),(1.13,1.629),(1.25,1.653),(1.43,1.662),(1.61,1.650),(1.79,1.605),(1.99,1.578),(2.4,1.574),(math.pi,1.577)]
 h=interp(rows,u)[0]
 if identity=='Anne':h+=.018*smooth((1.1-u)/.5)
 if identity=='Louis':h+=.035*smooth((1.05-u)/.65)
 return h
def make_hair(face):
 points=[human(Vector((v.co.x,v.co.z,-v.co.y))) for v in face.data.vertices]
 tree=BVHTree.FromPolygons(points,[tuple(p.vertices) for p in face.data.polygons])
 def surface(a,t,extra=0):
  low=hairline(a);h=low+(1.778-low)*t;d=Vector((math.sin(a),0,math.cos(a)));c=Vector((0,h,-.027));hit=tree.ray_cast(c,d)
  q=hit[0] if hit[0] is not None else c+d*.009;u=abs((a+math.pi)%TAU-math.pi)
  if 1.13<u<1.86 and h<1.665:q.x=max(-.079,min(.079,q.x))
  volume=(.007 if identity!='Louis' else .021)*smooth(t/.06)*math.sqrt(1-t)
  volume+=.001*math.sin(a*68+t*8)*smooth(t/.06)*math.sqrt(1-t)
  if t>.9:
   anchor_h=low+(1.778-low)*.9;anchor=tree.ray_cast(Vector((0,anchor_h,-.027)),d)[0]
   radius=((Vector((anchor.x,0,anchor.z+.027))).length if anchor is not None else .025)*math.sqrt(max(0,(1-t)/.1))
   q=Vector((d.x*radius,h,-.027+d.z*radius))
  q+=d*(volume+extra);q.y+=.003*smooth((t-.70)/.30)
  return q
 vv=[];ff=[];n=144;rows=26
 for j in range(rows+1):
  for i in range(n):vv.append(bust(surface(i*TAU/n,j/rows)))
 for j in range(rows):
  for i in range(n):q=j*n+i;ff.append((q,j*n+(i+1)%n,(j+1)*n+(i+1)%n,q+n))
 ff.append(tuple(rows*n+i for i in range(n)));ob=mesh('Chevelure pleine - contour anatomique des oreilles',vv,ff,hairmat)
 guides=[]
 for i in range(360):
  a=TAU*i/360;start=.4+.57*((i*.618)%1);path=[]
  for j in range(12):
   t=j/11;aa=a+.03*math.sin(t*4+i)*t;tt=start*(1-.98*t)
   path.append(bust(surface(aa,tt,.00045)))
  guides.append(path)
 strand_batch('Cheveux fins implantes',guides,.00048,hairmat)
 ob['earContour']='continuous C-shaped hairline; hair sits behind the helix'
 native.append((ob,guides))
 return tree,surface
def strand_batch(name,curves,r,m):
 vv=[];ff=[]
 for pp in curves:
  base=len(vv)
  for j,p in enumerate(pp):
   t=(Vector(pp[min(j+1,len(pp)-1)])-Vector(pp[max(0,j-1)])).normalized();a=t.cross(Vector((0,0,1)))
   if a.length<.01:a=t.cross(Vector((0,1,0)))
   a.normalize();b=t.cross(a);rr=r*(1-.72*j/(len(pp)-1))
   for k in range(3):vv.append(Vector(p)+rr*(a*math.cos(k*TAU/3)+b*math.sin(k*TAU/3)))
  for j in range(len(pp)-1):
   for k in range(3):q=base+j*3+k;ff.append((q,base+j*3+(k+1)%3,base+(j+1)*3+(k+1)%3,q+3))
 return mesh(name,vv,ff,m)
def make_beard(face):
 # Continuous displacement of native facial skin avoids a detached beard mask.
 def weight(p):
  x,h,d=p;u=abs(x);line=1.580+.058*smooth((u-.028)/.047)
  w=smooth((line-h)/.005)*smooth((h-1.520)/.010)*smooth((d-.008)/.021)
  w*=smooth((math.hypot(x/.0305,(h-1.588)/.021)-1)/.16)
  center=interp([(0,1.5957),(.012,1.597),(.021,1.5948),(.027,1.5908),(.032,1.585),(.039,1.5775),(.049,1.579)],u)[0]
  stroke=smooth((.0048+.002*smooth((u-.025)/.012)-abs(h-center))/.002)*smooth((.05-u)/.01)*smooth((d-.025)/.045)
  return max(w,stroke)
 weights=[];positions=[]
 for v in face.data.vertices:
  p=human(Vector((v.co.x,v.co.z,-v.co.y)));w=weight(p);weights.append(w)
  n=Vector((p.x*.7,-.22 if p.y<1.56 else -.07,max(.018,p.z))).normalized()
  p+=n*(.006+.018*gauss(p.y,1.543,.025))*w;p.y-=.010*w*gauss(p.y,1.533,.017)
  q=bust(p);v.co=(q.x,-q.z,q.y);positions.append(q)
 face.data.materials.append(hairmat)
 for f in face.data.polygons:
  if sum(weights[i] for i in f.vertices)/len(f.vertices)>.52:f.material_index=1
 curves=[];rng=random.Random(519)
 polys=[p for p in face.data.polygons if min(weights[i] for i in p.vertices)>.7]
 for i in range(1000):
  f=rng.choice(polys);u=rng.random();v=rng.random()
  if u+v>1:u=1-u;v=1-v
  q=positions[f.vertices[0]]*(1-u-v)+positions[f.vertices[1]]*u+positions[f.vertices[2]]*v
  h=human(q);n=Vector((h.x*.7,-.16,max(.025,h.z))).normalized();side=n.cross(Vector((0,1,0))).normalized()
  curves.append([q+n*.004*t+side*.0008*math.sin(t*TAU+i)-Vector((0,.003*t,0)) for t in [0,.33,.67,1]])
 strand_batch('Barbe fournie bouclee - moustache raccordee',curves,.00040,hairmat)
 face['beardConstruction']='native face displaced into beard volume; connected lowered moustache and jaw; 1000 surface rooted curls'

def costume():
 # Continuous tailored shoulder volume with a flat support, not stacked body primitives.
 width=.43 if identity in ['Francois','Louis'] else .39
 loft('Torse et epaules drapes',[(0,.20,.14,0),(.018,.24,.16,0),(.065,.28,.17,0),(.16,width*.88,.17,-.012),(.25,width,.17,-.025),(.32,width*.97,.15,-.033),(.38,width*.76,.12,-.033),(.415,.14,.09,-.018),(.43,.105,.09,0)],cloth,96,.05 if identity=='Louis' else .016)
 if identity=='Francois':
  # Square Renaissance neckline and slashed doublet, following the torso surface.
  tube('Encolure carree',[(x,.345+.055*(abs(x)/.26)**2,.153-.055*(abs(x)/.3)**2) for x in [(-.28+.56*i/40) for i in range(41)]],.009,detail)
  for x in [-.27,-.21,-.15,-.09,0,.09,.15,.21,.27]:
   tube('Creve de pourpoint',[(x*(.76+.24*t),.065+.255*t,.145-.045*(abs(x)/.3)**2+.009*math.sin(t*math.pi)) for t in [i/12 for i in range(13)]],.0048,hairmat,6)
  tube('Chaine sur le torse',[(.27*math.sin(a),.315-.205*math.cos(a),.182-.038*abs(math.sin(a))) for a in [-math.pi/2+i*math.pi/60 for i in range(61)]],.010,detail)
 elif identity=='Louis':
  # Broad layered cravat with a scalloped surface, plus diagonal mantle folds.
  vv=[];ff=[]
  for j in range(25):
   t=j/24;w=.063+.058*t
   for i in range(25):
    u=-1+2*i/24;vv.append((w*u,.44-.255*t,.125+.065*t+.010*math.cos(u*math.pi*5)*(1-.35*t)))
  for j in range(24):
   for i in range(24):q=j*25+i;ff.append((q,q+1,q+26,q+25))
  mesh('Cravate de dentelle plis sculptes',vv,ff,detail,1)
  vv=[];ff=[]
  for j in range(24):
   t=j/23
   for i in range(49):
    u=i/48;x=-.34+.68*u;vv.append((x,.075+.21*u+.105*t,.125+.030*math.sin(math.pi*u)+.012*math.cos(t*math.pi*5)*math.sin(math.pi*u)))
  for j in range(23):
   for i in range(48):q=j*49+i;ff.append((q,q+1,q+50,q+49))
  mesh('Manteau diagonal drape continu',vv,ff,cloth,1)
 elif identity=='Catherine':
  # Small figure-eight ruff of the Clouet portrait, closely fitted below the jaw.
  vv=[];ff=[];n=384
  for j in range(5):
   t=j/4
   for i in range(n):
    a=i*TAU/n;radius=.108+.061*t;vv.append((radius*math.sin(a),.443-.026*math.cos(a)+.022*t*math.sin(a*32),radius*.86*math.cos(a)))
  for j in range(4):
   for i in range(n):q=j*n+i;ff.append((q,j*n+(i+1)%n,(j+1)*n+(i+1)%n,q+n))
  mesh('Fraise plis en huit',vv,ff,detail)
 else:
  tube('Encolure Anne de France',[(x,.29+.066*(abs(x)/.29)**2,.143-.068*(abs(x)/.30)**2) for x in [-.30+i*.60/60 for i in range(61)]],.008,detail)
  for sg in [-1,1]:tube('Bord manteau',[(sg*(.20+.17*t),.10+.235*t,.17-.05*t) for t in [i/20 for i in range(21)]],.012,detail)

def headdress(surface):
 if identity=='Francois':
  # Soft slanted bonnet, open at the forehead; continuous cloth section.
  vv=[];ff=[];n=112
  rings=[(1.718,.103,.106),(1.744,.136,.121),(1.775,.145,.123),(1.797,.117,.102),(1.809,.051,.045),(1.810,.003,.003)]
  for h,rx,rz in rings:
   for i in range(n):
    a=i*TAU/n;vv.append(bust((rx*math.sin(a),h+.030*math.sin(a),-.023+rz*math.cos(a))))
  for j in range(len(rings)-1):
   for i in range(n):q=j*n+i;ff.append((q,j*n+(i+1)%n,(j+1)*n+(i+1)%n,q+n))
  ff.append(tuple((len(rings)-1)*n+i for i in range(n)));mesh('Bonnet incline de Francois Ier',vv,ff,cloth,1)
  # Sculpted feather rachis and individual barbs on the top of the bonnet.
  spine=[bust((-.095+.175*t,1.795+.042*math.sin(t*math.pi)+.030*(-.095+.175*t)/.14,.082)) for t in [i/40 for i in range(41)]]
  tube('Plume du bonnet rachis',spine,.003,detail,7)
  curves=[]
  for i in range(70):
   t=i/69;p=spine[min(40,round(t*40))]
   for sg in [-1,1]:curves.append([p+Vector((-.016*s,sg*.017*s*math.sin(math.pi*t),.005*s)) for s in [0,.33,.66,1]])
  strand_batch('Plume sculptee barbes',curves,.001,detail)
 elif identity=='Louis':
  # Full-bottomed Rigaud wig: overlapping S-shaped locks, tapering as curls.
  rng=random.Random(1701);curves=[]
  for sg in [-1,1]:
   for layer in range(3):
    for k in range(10):
     u=k/9;a=sg*(.52+u*2.26);root=surface(a,.72+.22*(layer/2));pp=[];rr=[]
     length=.16+.065*math.sin(u*math.pi)+.028*layer
     for j in range(27):
      t=j/26;rad=(.018+.004*layer)*smooth(t/.17);angle=TAU*(3.0*t)+k*.68+layer
      p=root+Vector((sg*(.033*smooth(t/.25)+rad*math.sin(angle)),.012*math.sin(t*math.pi)-length*t,(.035 if layer==0 else -.019*layer)*t+rad*math.cos(angle)))
      # Lateral locks stay outside the cheeks, with visible ear edges.
      if abs(a)<1.45:p.x=sg*max(abs(p.x),.083+.012*math.sin(t*math.pi))
      pp.append(bust(p));rr.append(2.2*(.014+.003*layer)*(.13+.87*smooth(t/.14))*max(.06,(1-t)**.3))
     tube('Perruque boucle S %s %d %d'%(sg,layer,k),pp,0,hairmat,10,rr)
     for f in range(5):
      phase=f*TAU/5;fine=[]
      for j,p in enumerate(pp):
       tangent=(pp[min(j+1,len(pp)-1)]-pp[max(0,j-1)]).normalized();ax=tangent.cross(Vector((0,0,1))).normalized();bx=tangent.cross(ax)
       fine.append(p+(ax*math.cos(phase)+bx*math.sin(phase))*rr[j]*1.005)
      curves.append(fine)
  strand_batch('Perruque stries de meches',curves,.0005,hairmat)
 else:
  # Fitted hood, open at the forehead and the front of the ears. Catherine's veil
  # continues down the back; Anne's jewelled lappets cover the temple hair.
  vv=[];ff=[];n=128;rows=28
  def edge(a):
   u=abs((a+math.pi)%TAU-math.pi)
   if identity=='Catherine':return interp([(0,1.706),(.42,1.730),(.78,1.721),(1.10,1.676),(1.4,1.628),(2,1.563),(math.pi,1.558)],u)[0]
   return interp([(0,1.735),(.55,1.732),(.88,1.717),(1.12,1.591),(1.55,1.581),(2,1.598),(math.pi,1.600)],u)[0]
  def hood(a,t):
   lo=edge(a);h=lo+(1.789-lo)*t;direction=Vector((math.sin(a),0,math.cos(a)));c=Vector((0,h,-.027));hit=headtree.ray_cast(c,direction)
   q=hit[0] if hit[0] is not None else c+direction*.009
   # Below the skull the head covering descends rather than collapsing onto neck.
   blend=smooth((1.67-h)/.06)
   side=Vector((math.sin(a)*.095,h,-.027+math.cos(a)*.104));q=q.lerp(side,blend)
   q+=direction*(.009+.0006*math.sin(a*26+t*2))*math.sqrt(1-t)
   if h>1.735:
    hit=headtree.ray_cast(Vector((0,1.735,-.027)),direction)[0]
    anchor=(Vector((hit.x,0,hit.z+.027)).length if hit is not None else .058)+.009
    rr=anchor*math.sqrt(max(0,(1.789-h)/(1.789-1.735)));q=Vector((rr*math.sin(a),h,-.027+rr*math.cos(a)))
   return q
  for j in range(rows+1):
   for i in range(n):vv.append(bust(hood(i*TAU/n,j/rows)))
  for j in range(rows):
   for i in range(n):q=j*n+i;ff.append((q,j*n+(i+1)%n,(j+1)*n+(i+1)%n,q+n))
  ff.append(tuple(rows*n+i for i in range(n)));ob=mesh('Coiffe en coeur et voile' if identity=='Catherine' else 'Coiffe a pans brodes',vv,ff,cloth)
  solid=ob.modifiers.new('Epaisseur du tissu sculpte','SOLIDIFY');solid.thickness=.006
  tube('Bord de coiffe', [bust(hood(i*TAU/160,0)) for i in range(161)],.004 if identity=='Catherine' else .009,detail,8)
  if identity=='Catherine':
   vv=[];ff=[];cols=80
   for j in range(22):
    t=j/21
    for i in range(cols+1):
     a=1.3+(TAU-2.6)*i/cols;top=hood(a,.08);target=Vector((.17*math.sin(a),1.435,-.05+.084*math.cos(a)))
     p=top.lerp(target,t);p.z-=.008*math.sin(a*18)*math.sin(t*math.pi);vv.append(bust(p))
   for j in range(21):
    for i in range(cols):q=j*(cols+1)+i;ff.append((q,q+1,q+cols+2,q+cols+1))
   v=mesh('Voile de veuve descendant sur les epaules',vv,ff,cloth);mod=v.modifiers.new('Voile epais','SOLIDIFY');mod.thickness=.005
  else:
   # Crown proportions and pearl edging from Anne de France's donor panel.
   for h in [1.737,1.754]:
    rr=.106*math.sqrt(max(0,1-((h-1.68)/.109)**2))+.008
    tube('Cercle de couronne',[bust((rr*math.sin(a),h,-.027+rr*math.cos(a))) for a in [i*TAU/96 for i in range(97)]],.0055,detail,8)
   vv=[];ff=[]
   for j in range(3):
    h=1.737+j*.0085;rr=.106*math.sqrt(1-((h-1.68)/.109)**2)+.008
    for i in range(112):a=i*TAU/112;vv.append(bust((rr*math.sin(a),h,-.027+rr*math.cos(a))))
   for j in range(2):
    for i in range(112):q=j*112+i;ff.append((q,j*112+(i+1)%112,(j+1)*112+(i+1)%112,q+112))
   mesh('Bandeau plein de la couronne',vv,ff,detail)
   for i in range(14):
    a=i*TAU/14;pp=[]
    for j in range(13):
     t=j/12;aa=a+(t-.5)*.27;h=1.754+.019*math.sin(t*math.pi)**1.4;rr=.082;pp.append(bust((rr*math.sin(aa),h,-.027+rr*math.cos(aa))))
    tube('Fleuron de couronne',pp,.0038,detail,7)
   for sg in [-1,1]:
    for i in range(13):
     a=sg*(.92+.26*i/12);q=bust(hood(a,0));r=.004
     tube('Perle de coiffe',[q+Vector((r*math.cos(t),r*math.sin(t),0)) for t in [j*TAU/10 for j in range(11)]],.0025,detail,5)

native=[]
for identity,asset in [('Francois','bustFrancoisI'),('Louis','bustLouisXIV'),('Catherine','bustCatherineMedici'),('Anne','bustAnneFrance')]:
 objects=[];face=head()
 if identity=='Francois':make_beard(face)
 headtree,surface=make_hair(face);costume();headdress(surface)
 # Correct winding globally without destroying the retained anatomical mesh.
 for ob in objects:
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
  if ob.modifiers:
   for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
  import bmesh
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
 models[asset]=list(objects)
 stats[asset]={'objects':len(objects),'vertices':sum(len(o.data.vertices) for o in objects),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects)}
bpy._bust_models=models;bpy._bust_scene=S;bpy._bust_native=native
(OUT/'model-stats.json').write_text(json.dumps(stats,indent=2))
print(json.dumps(stats))
