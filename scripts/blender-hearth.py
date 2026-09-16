import bpy, math, random, json
from pathlib import Path
from mathutils import Vector

workspace=Path(r'C:\Users\nicol\Documents\workspaces\vr-workspace\test-meta-web-sdk-update')
out=workspace/'public/gltf/castle/hearth.glb'
evidence=workspace/'artifacts/castle'
rng=random.Random(41027)
scene=bpy.data.scenes.new('Foyers - bois et fer forge')
bpy.context.window.scene=scene
parts=[]

def mat(name,color,metal=0,rough=.8,emission=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    m.node_tree.nodes.clear();bs=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    output=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(bs.outputs['BSDF'],output.inputs['Surface'])
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
    if emission:
        bs.inputs['Emission Color'].default_value=(*color,1);bs.inputs['Emission Strength'].default_value=emission
    return m

iron=mat('Fer forge patine',(.052,.058,.065),.83,.38)
wood=mat('Ecorce chene',(.16,.07,.026),0,.94)
cut=mat('Bois de bout',(.36,.21,.085),0,.88)
char=mat('Charbon et joints',(.024,.020,.017),0,1)
brick=mat('Briques de foyer enfumees',(.14,.075,.044),0,.95)
ember=mat('Braises incandescentes',(.9,.055,.004),0,.9,2.5)

def coord(p):return (p[0],-p[2],p[1])
def finish(o,name,m):
    o.name=name;o.data.materials.append(m);parts.append(o);return o
def box(name,p,size,m,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=coord(p));o=bpy.context.object;o.scale=(size[0],size[2],size[1])
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new('Aretes adoucies','BEVEL');mod.width=bevel;mod.segments=1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return finish(o,name,m)
def tube(name,points,r,m,sides=6):
    curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=1;curve.bevel_depth=r;curve.bevel_resolution=0;curve.resolution_u=1
    spline=curve.splines.new('POLY');spline.points.add(len(points)-1)
    for p,v in zip(spline.points,points):p.co=(*coord(v),1)
    o=bpy.data.objects.new(name,curve);scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    for other in bpy.context.selected_objects:
        if other!=o:other.select_set(False)
    bpy.ops.object.convert(target='MESH');return finish(bpy.context.object,name,m)

# Brick lining entirely covers the previous flat black back, with real mortar gaps.
box('Fond des joints',(0,.53,-.11),(1.64,1.08,.035),char)
for row in range(7):
    y=.077+row*.151
    for col in range(6):
        left=-.82+col*.32-(.16 if row%2 else 0);right=min(.82,left+.308);left=max(-.82,left)
        if right-left>.02:
            o=box('Brique refractaire',((left+right)/2,y,-.083),(right-left,.138,.042),brick,.005)
            # A vertex-color-free, tiny geometric relief keeps the masonry legible.
            o.location.y+=rng.uniform(-.002,.002)
box('Lit de cendres',(0,.014,.12),(1.49,.026,.43),char,.008)

def log(a,b,r):
    A=Vector(a);B=Vector(b);axis=(B-A).normalized();u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u).normalized()
    n=18;rings=7;verts=[];faces=[]
    radii=[r*(1+rng.uniform(-.15,.15)) for i in range(n)]
    for j in range(rings):
        centre=A.lerp(B,j/(rings-1))
        for i in range(n):
            theta=i*math.tau/n;rad=radii[i]*(1+rng.uniform(-.045,.045))
            verts.append(coord(centre+(u*math.cos(theta)+v*math.sin(theta))*rad))
    for j in range(rings-1):
        for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    faces.extend([tuple(reversed(range(n))),tuple((rings-1)*n+i for i in range(n))])
    mesh=bpy.data.meshes.new('Ecorce fendue');mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new('Buche de chene',mesh);scene.collection.objects.link(o);finish(o,o.name,wood);mesh.materials.append(cut);mesh.materials.append(char)
    for poly in mesh.polygons[:-2]:poly.material_index=2 if rng.random()<.17 else 0
    for poly in mesh.polygons[-2:]:poly.material_index=1
    for tip,sg in [(A,-1),(B,1)]:
        centre=tip+axis*sg*.0015
        for radius in [.27*r,.53*r,.77*r]:
            tube('Cernes de croissance',[centre+(u*math.cos(t)+v*math.sin(t))*radius*(1+.08*math.sin(t*3)) for t in [i*math.tau/24 for i in range(25)]],.0018,char)
        for theta in [.4,2.5,4.6]:
            radial=u*math.cos(theta)+v*math.sin(theta)
            tube('Fentes du bois',[centre+radial*r*.4,centre+radial*r*.94],.0025,char)
    for i in range(0,n,3):
        theta=i*math.tau/n;radial=u*math.cos(theta)+v*math.sin(theta)
        tube('Fissure incandescente',[A.lerp(B,t)+radial*radii[i]*1.015 for t in [.12,.35,.61,.85]],.0025,ember)

# Two lower logs and a crossed upper log, resting on the ash bed.
log((-.57,.13,.08),(.48,.13,.02),.107)
log((-.48,.13,.29),(.57,.13,.23),.11)
log((-.40,.29,.07),(.40,.30,.24),.087)
for i in range(32):
    x=rng.uniform(-.62,.62);z=rng.uniform(-.035,.32)
    box('Tison',(x,.034,z),(rng.uniform(.02,.065),.018,rng.uniform(.02,.045)),ember if i%3 else char,.004)

# Forged screen stands on two wide feet. Open ironwork leaves the fire visible.
for x in [-.73,.73]:
    box('Pied de grille',(x,.025,.32),(.15,.05,.28),iron,.009)
    tube('Montant forge',[(x,.05,.38),(x,.60,.38)],.019,iron)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.03,location=coord((x,.62,.38)))
    finish(bpy.context.object,'Pommeau de fer',iron)
for y in [.085,.52]:tube('Traverse',[(x,y+.035*(1-(x/.73)**2),.38) for x in [-.73+i*1.46/24 for i in range(25)]],.014,iron)
for x in [-.54,-.27,0,.27,.54]:
    y0=.085+.035*(1-(x/.73)**2);y1=.52+.035*(1-(x/.73)**2)
    tube('Barreau torsade',[(x+.009*math.sin(t*math.tau*2),y0+t*(y1-y0),.38+.009*math.cos(t*math.tau*2)) for t in [i/20 for i in range(21)]],.012,iron)
    for sg in [-1,1]:
        tube('Volute forge',[ (x+sg*(.102+.086*(1-t)*math.cos(t*math.tau*1.25)),.30+.13*(1-t)*math.sin(t*math.tau*1.25),.385) for t in [i/32 for i in range(33)]],.010,iron)
for sg in [-1,1]:
    for y in [.09,.52]:tube('Retour lateral',[(sg*.73,y,.38),(sg*.80,y,.17),(sg*.80,y,.02)],.013,iron)
    tube('Support lateral',[(sg*.80,.02,.02),(sg*.80,.52,.02)],.014,iron)

# One joined mesh, six material primitives; resources are shared by all four placements.
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();joined=bpy.context.object;joined.name='Bois braises briques et grille forge'
scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
out.parent.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,use_active_scene=True,export_yup=True,export_animations=False)
bpy.data.libraries.write(str(evidence/'foyers-bois-fer-forge.blend'),{scene})
joined.data.calc_loop_triangles()
print(json.dumps({'asset':str(out),'triangles':len(joined.data.loop_triangles),'materials':len(joined.data.materials),'bytes':out.stat().st_size}))
