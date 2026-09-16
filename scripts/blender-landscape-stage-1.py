"""Approved arrival landscape; run through the local Blender MCP. Y-up helper coordinates."""
import bpy, bmesh, math, random, json
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
OUT=ROOT/'public/gltf/arrival-landscape'; OUT.mkdir(parents=True,exist_ok=True)
EVID=ROOT/'artifacts/arrival-landscape'
scene=bpy.data.scenes.new('Accueil - domaine lointain et foret de chenes');bpy.context.window.scene=scene
C=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
parts={}; stats={}
def material(name,color,rough=1,texture=None):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
 if texture:
  n=256;rng=np.random.default_rng(615);a=rng.random((n,n));yy,xx=np.mgrid[0:n,0:n]
  if texture=='bark': a=.7+.3*np.sin(xx*.5+np.sin(yy*.025))+a*.2
  elif texture=='leaf': a=.7+.3*np.sin(xx*.22)*np.cos(yy*.32)+a*.18
  else:a=.7+a*.5
  rgba=np.ones((n,n,4),dtype=np.float32);rgba[:,:,:3]=np.clip(np.array(color)*a[:,:,None],0,1)
  img=bpy.data.images.new(name+' texture',width=n,height=n);img.pixels.foreach_set(rgba.ravel());img.pack()
  tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
 return m
turf=material('Prairie douce',(.22,.31,.095),texture='grass')
gravel=material('Gravier calcaire du chemin',(.55,.47,.33),texture='gravel')
bark=material('Ecorce de chene',(.20,.125,.065),texture='bark')
leaves=[material('Feuillage chene '+str(i),c,texture='leaf') for i,c in enumerate([(.18,.29,.055),(.24,.35,.07),(.30,.39,.10)])]
stone=material('Pierre du portail',(.69,.62,.47),.85);iron=material('Fer du portail',(.055,.075,.055),.5)
def mesh(asset,name,verts,faces,mat,smooth=True):
 assert verts and faces and all(0<=i<len(verts) for face in faces for i in face), 'Invalid geometry indices: '+name
 data=bpy.data.meshes.new(name);data.from_pydata([(x,-z,y) for x,y,z in verts],[],faces);data.update();data.materials.append(mat)
 bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
 uv=data.uv_layers.new(name='UVMap')
 for p in data.polygons:
  p.use_smooth=smooth
  for li in p.loop_indices:
   v=data.vertices[data.loops[li].vertex_index].co;uv.data[li].uv=(v.x*.7,v.y*.7) if abs(p.normal.z)>.5 else (v.x*.8+v.y*.8,v.z*.4)
 o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);parts.setdefault(asset,[]).append(o);return o
def export(asset,objects):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.hide_set(False);o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 bpy.ops.export_scene.gltf(filepath=str(OUT/(asset+'.glb')),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_image_format='JPEG',export_jpeg_quality=85)
 for o in objects:o.data.calc_loop_triangles()
 stats[asset]={'triangles':sum(len(o.data.loop_triangles) for o in objects),'meshes':len(objects),'bytes':(OUT/(asset+'.glb')).stat().st_size}
def combine(objects,name):
 # Merge explicitly: avoid the Blender operator joining linked mesh instances.
 verts=[];faces=[];material_ids=[];uvs=[];materials=[]
 for obj in objects:
  data=obj.data;offset=len(verts);world=obj.matrix_world.copy()
  verts.extend(tuple(world@v.co) for v in data.vertices)
  mapping=[]
  for mat in data.materials:
   if mat not in materials:materials.append(mat)
   mapping.append(materials.index(mat))
  uv=data.uv_layers.active
  for poly in data.polygons:
   faces.append(tuple(offset+i for i in poly.vertices))
   material_ids.append(mapping[poly.material_index] if mapping else 0)
   uvs.extend(tuple(uv.data[i].uv) if uv else (0,0) for i in poly.loop_indices)
 data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces)
 for mat in materials:data.materials.append(mat)
 for poly,mat in zip(data.polygons,material_ids):poly.material_index=mat;poly.use_smooth=True
 uv=data.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',[v for pair in uvs for v in pair]);data.update()
 obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj)
 for old in objects:bpy.data.objects.remove(old,do_unlink=True)
 return obj


# Smooth S path, exactly tangent to the garden's seven-metre central avenue at z=-68.
control=[(7.9,0),(15,-6),(29,-2),(43,-12),(53,-26),(70,-23),(88,-35),(100,-49),(100,-68)]
path=[]
for k in range(len(control)-1):
 p0=np.array(control[max(0,k-1)]);p1=np.array(control[k]);p2=np.array(control[k+1]);p3=np.array(control[min(len(control)-1,k+2)])
 for j in range(18):
  t=j/18;p=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t);path.append(tuple(p))
path.append(control[-1]);path_array=np.array(path)
def pathdistance(x,z):return float(np.sqrt(np.min(np.sum((path_array-np.array([x,z]))**2,axis=1))))
def height(x,z):
 r=math.hypot(x,z)
 if r<21 or (64<x<136 and -147<z<-55):return -.09
 hills=.6+.5*math.sin(x*.052)*math.cos(z*.04)+.32*math.sin(z*.072+x*.019)
 return -.09+hills*min(1,max(0,(r-21)/15))*min(1,max(0,(pathdistance(x,z)-3)/7))
v=[];f=[];n=121
for j in range(n):
 for i in range(n):
  x=-70+i*2;z=-180+j*2;v.append((x,height(x,z),z))
for j in range(n-1):
 for i in range(n-1):a=j*n+i;f.append((a,a+1,a+1+n,a+n))
mesh('terrain','Terrain de prairie 240m',v,f,turf)
v=[];f=[]
for i,(x,z) in enumerate(path):
 a=Vector(path[max(0,i-1)]);b=Vector(path[min(len(path)-1,i+1)]);t=(b-a).normalized();normal=Vector((-t.y,t.x))
 width=3.6+3.4*max(0,min(1,(-z-51)/17));r=math.hypot(x,z)
 h=.025+.20*max(0,1-abs(r-15)/9)
 for side in [-1,1]:v.append((x+normal.x*width*.5*side,h,z+normal.y*width*.5*side))
 if i:f.append((2*i-2,2*i-1,2*i+1,2*i))
mesh('path','Chemin de gravier en serpent',v,f,gravel)
(EVID/'path.json').write_text(json.dumps({'control':control,'samples':path,'widthStart':3.6,'widthEnd':7},indent=2))

# Three oak silhouettes, each with a distant version. Forked tapered branches,
# irregular opaque canopy clusters and genuinely lobed leaves avoid alpha overdraw.
def tube(v,f,points,radii,sides=7):
 off=len(v)
 for j,p in enumerate(points):
  p=Vector(p);t=(Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])).normalized();u=t.cross(Vector((0,1,0)))
  if u.length<.01:u=t.cross(Vector((1,0,0)))
  u.normalize();w=t.cross(u).normalized()
  for i in range(sides):v.append(tuple(p+radii[j]*(math.cos(i*math.tau/sides)*u+math.sin(i*math.tau/sides)*w)))
 for j in range(len(points)-1):
  for i in range(sides):a=off+j*sides+i;b=off+j*sides+(i+1)%sides;f.append((a,b,b+sides,a+sides))
 f.append(tuple(off+i for i in reversed(range(sides))));f.append(tuple(off+(len(points)-1)*sides+i for i in range(sides)))
bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=2,radius=1);bm.verts.ensure_lookup_table();bm.verts.index_update();ico_v=[tuple(v.co) for v in bm.verts];ico_f=[tuple(v.index for v in p.verts) for p in bm.faces];bm.free()
models={}
for variant,H in enumerate([9,13,17]):
 for lod in [0,1]:
  rng=random.Random(250+variant);asset=f'oak{variant+1}'+('Far' if lod else '')
  v=[];f=[];tube(v,f,[(0,0,0),(.10,H*.23,.05),(-.15,H*.48,.12),(.2,H*.69,0)],[H*.035,H*.026,H*.017,.035],9 if not lod else 6)
  crowns=[]
  for branch in range(11):
   angle=branch*2.4+rng.uniform(-.2,.2);spread=H*rng.uniform(.20,.34);h=H*rng.uniform(.54,.82)
   tip=(math.cos(angle)*spread,h,math.sin(angle)*spread);start=(0,H*(.32+.02*branch),0);middle=(tip[0]*.55,h*.89,tip[2]*.55)
   tube(v,f,[start,middle,tip],[H*.014,H*.009,.018],5)
   crowns.append((tip,H*rng.uniform(.13,.21)))
  crowns.append(((0,H*.88,0),H*.17));mesh(asset,'Tronc et branches '+asset,v,f,bark)
  v=[];f=[]
  for center,rad in crowns:
   off=len(v)
   for xx,yy,zz in ico_v:
    jitter=rng.uniform(.82,1.16);v.append((center[0]+xx*rad*jitter,center[1]+yy*rad*.78*jitter,center[2]+zz*rad*jitter))
   f.extend(tuple(off+i for i in face) for face in ico_f)
   if not lod:
    for leaf in range(15):
     a=rng.random()*math.tau;b=rng.uniform(-.9,.9);rr=rad*math.sqrt(1-b*b)
     c=Vector((center[0]+math.cos(a)*rr,center[1]+b*rad*.8,center[2]+math.sin(a)*rr))
     u=Vector((math.cos(a),.25,math.sin(a))).normalized();w=Vector((-math.sin(a),.6,math.cos(a))).normalized();length=rng.uniform(.20,.35)
     off=len(v);v.append(tuple(c))
     for k in range(14):
      t=k*math.tau/14;lobes=1+.23*math.cos(t*6);v.append(tuple(c+u*math.cos(t)*length+w*math.sin(t)*length*.5*lobes))
     f.extend((off,off+1+k,off+1+(k+1)%14) for k in range(14))
  mesh(asset,'Couronne de feuilles '+asset,v,f,leaves[variant]);export(asset,parts[asset]);models[(variant,lod)]=parts[asset]
  for o in parts[asset]:o.hide_set(True);o.hide_render=True

