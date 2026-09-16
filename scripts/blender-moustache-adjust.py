"""Lower the moustache onto the upper lip and merge both tips into the beard.
Edits the existing facial topology and all visemes together; no mesh primitives.
"""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/moustache'
scene=bpy._natural_scene;bpy.context.window.scene=scene;m=bpy._natural_models['courtMale'];face=m['face']
# Isolate this revision and retain the already approved geometry for comparison.
backup=face.data.copy();backup.name='Avant retouche moustache';backup.use_fake_user=True
face.data=face.data.copy();keys=face.data.shape_keys.key_blocks
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def gauss(x,c,w):return math.exp(-((x-c)/w)**2)
def author(v):return Vector((v.x,v.z+.05,-v.y-.045))
def blender_delta(p):return Vector((p.x,-p.z,p.y))
def cheek(p):
    x,h,d=p;u=abs(x);line=1.580+.058*smooth((u-.028)/.047)
    w=smooth((line-h)/.005)*smooth((h-1.520)/.010)*smooth((d-.008)/.021)
    return w*smooth((math.hypot(x/.0305,(h-1.588)/.021)-1)/.16)
def old_weight(p):
    x,h,d=p;u=abs(x)
    return max(cheek(p),smooth((h-1.597)/.003)*smooth((1.608-h)/.003)*smooth((.033-u)/.006)*smooth((d-.080)/.010)*(.9+.1*smooth(u/.004)))
def line(u):
    knots=[(0,1.5957),(.012,1.5970),(.021,1.5948),(.027,1.5908),(.032,1.5850),(.039,1.5775),(.049,1.579)]
    for (a,h0),(b,h1) in zip(knots,knots[1:]):
        if u<=b:return h0+(h1-h0)*smooth((u-a)/(b-a))
    return knots[-1][1]
def new_weight(p):
    x,h,d=p;u=abs(x);half=.0032+.0022*smooth((u-.025)/.012)
    stroke=smooth((half-abs(h-line(u)))/.0011)*smooth((.049-u)/.006)*smooth((d-.035)/.025)
    return max(cheek(p),stroke)
def relief(p,w):
    n=Vector((p.x*.7,-.22 if p.y<1.56 else -.07,max(.018,p.z))).normalized()
    return n*(.0035+.008*gauss(p.y,1.543,.025))*w-Vector((0,.006*w*gauss(p.y,1.533,.017),0))
def skin_color(p):
    x,h,d=p;c=gauss(abs(x),.047,.027)*gauss(h,1.616,.023)*smooth(d/.07)
    noise=.004*math.sin(x*930+h*320)*math.sin(h*710-d*610)
    y=(h-.892)/.104;u=abs(x)/.028
    lip=smooth((y-(6.49+.055*u*u))/.026)*smooth(((6.741-.09*u*u)-y)/.024)*smooth((1-u)/.14)*smooth((d-.088)/.010)
    base=(.40+.026*c+noise,.20-.018*c+noise,.128-.012*c+noise);tint=(.31,.105,.077)
    return tuple(base[k]*(1-lip*.76)+tint[k]*lip*.76 for k in range(3))
skinmat=next(i for i,mat in enumerate(face.data.materials) if 'peau nuancee' in mat.name)
beardmat=next(i for i,mat in enumerate(face.data.materials) if 'Barbe mate' in mat.name)
fibreMat={i for i,mat in enumerate(face.data.materials) if 'chatain profond' in mat.name}
surfaceIds={i for p in face.data.polygons if p.material_index in {skinmat,beardmat} for i in p.vertices}
fiberIds=sorted({i for p in face.data.polygons if p.material_index in fibreMat for i in p.vertices})
colors=face.data.color_attributes['Complexion'];changes={};touched=set()
for i in surfaceIds:
    current=author(keys[0].data[i].co)
    if abs(current.x)>.054 or not 1.568<current.y<1.617 or current.z<.045:continue
    p=current.copy()
    for _ in range(8):p=current-relief(p,old_weight(p))
    old=old_weight(p);new=new_weight(p)
    if abs(new-old)<.001:continue
    changes[i]=blender_delta(relief(p,new)-relief(p,old));touched.add(i)
    color=skin_color(p);shade=1+.12*math.sin(p.x*550+p.y*700);brown=(.019*shade,.0065*shade,.003*shade)
    colors.data[i].color=(*(color[k]*(1-new)+brown[k]*new for k in range(3)),1)
for key in keys:
    for i,delta in changes.items():key.data[i].co+=delta
    key.value=0
for p in face.data.polygons:
    if p.material_index not in {skinmat,beardmat} or not any(i in touched for i in p.vertices):continue
    p.material_index=beardmat if sum(colors.data[i].color[0] for i in p.vertices)/len(p.vertices)<.18 else skinmat
# Move the existing short moustache fibres onto the new surface, preserving their morph deltas.
tree=BVHTree.FromPolygons([k.co.copy() for k in keys[0].data],[tuple(p.vertices) for p in face.data.polygons if p.material_index in {skinmat,beardmat}])
moved=0
for start in range(0,len(fiberIds),9):
    strand=fiberIds[start:start+9]
    if len(strand)!=9:continue
    root=sum((keys[0].data[i].co for i in strand[:3]),Vector())/3;p=author(root)
    if abs(p.x)>.038 or not 1.594<p.y<1.612:continue
    target=root.copy();target.z=line(abs(p.x))-.05
    hit=tree.ray_cast(Vector((target.x,-.4,target.z)),Vector((0,1,0)))
    if hit[0] is not None:target.y=hit[0].y-.00015
    delta=target-root
    for key in keys:
        for i in strand:key.data[i].co+=delta
    moved+=1
for v,k in zip(face.data.vertices,keys[0].data):v.co=k.co
face.data.update();face['moustacheRevision']='lower upper-lip curve, continuous left and right beard junctions'
# The hidden native emitter follows the same relocation; roots retain their face bindings.
for ob in bpy._organic_emitters:
    if not ob.name.startswith('courtMale') or 'Barbe' not in ob.name:continue
    for v in ob.data.vertices:
        p=author(v.co)
        if abs(p.x)>.038 or not 1.594<p.y<1.612:continue
        v.co.z=line(abs(p.x))-.05
        hit=tree.ray_cast(Vector((v.co.x,-.4,v.co.z)),Vector((0,1,0)))
        if hit[0] is not None:v.co.y=hit[0].y
report={'changedSurfaceVertices':len(changes),'relocatedFibreStrands':moved,'centerLineAuthorHeight':line(0),'keys':len(keys)-1,
        'basisMeshError':max((v.co-k.co).length for v,k in zip(face.data.vertices,keys[0].data))}
(OUT/'adjustment.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
# Store before rendering so a rendering interruption cannot lose the edit.
bpy.data.libraries.write(str(OUT/'renaissance-moustache.blend'),{scene},fake_user=True,compress=True)
