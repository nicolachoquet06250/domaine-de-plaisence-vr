"""Standalone Blender MCP authoring: realistic, batched Renaissance arrival terrace.

All helper coordinates are metres, Y up, matching the existing arrival asset.
Does not modify other Blender scenes or overwrite the shared castle namespace.
"""
import bpy, bmesh, math, json
import numpy as np
from pathlib import Path
from mathutils import Vector

ARR_ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
ARR_OUT=ARR_ROOT/'public/gltf/arrival'; ARR_OUT.mkdir(parents=True,exist_ok=True)
ARR_EVID=ARR_ROOT/'artifacts/arrival-realistic'; ARR_EVID.mkdir(parents=True,exist_ok=True)
arr_scene=bpy.data.scenes.new('Accueil Renaissance - Pierre et or'); bpy.context.window.scene=arr_scene
arr_scene.unit_settings.system='METRIC'; arr_batches={}; arr_objects=[]

def arr_mat(name,color,rough=.6,metal=0,texture=False):
    m=bpy.data.materials.new('Arrival '+name); m.use_nodes=True; m.use_backface_culling=True
    nt=m.node_tree; nt.nodes.clear(); p=nt.nodes.new('ShaderNodeBsdfPrincipled'); p.name='PBR'
    p.inputs['Base Color'].default_value=(*color,1); p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    out=nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(p.outputs['BSDF'],out.inputs['Surface']); m.diffuse_color=(*color,1)
    if texture:
        n=256; y,x=np.mgrid[0:n,0:n]/n; rng=np.random.default_rng(sum(map(ord,name)))
        field=.93+.03*np.sin(x*math.tau*4)*np.cos(y*math.tau*7)+.06*(rng.random((n,n))-.5)
        rgba=np.ones((n,n,4),dtype=np.float32); rgba[:,:,:3]=np.clip(np.array(color)*field[:,:,None],0,1)
        img=bpy.data.images.new('Arrival '+name+' albedo',width=n,height=n); img.pixels.foreach_set(rgba.ravel()); img.pack()
        tex=nt.nodes.new('ShaderNodeTexImage'); tex.image=img; nt.links.new(tex.outputs['Color'],p.inputs['Base Color'])
        rgba[:,:,0]=.5-(np.roll(field,-1,1)-np.roll(field,1,1))*.15
        rgba[:,:,1]=.5-(np.roll(field,-1,0)-np.roll(field,1,0))*.15; rgba[:,:,2]=1
        img=bpy.data.images.new('Arrival '+name+' normal',width=n,height=n); img.colorspace_settings.name='Non-Color'; img.pixels.foreach_set(rgba.ravel()); img.pack()
        tex=nt.nodes.new('ShaderNodeTexImage'); tex.image=img; norm=nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(tex.outputs['Color'],norm.inputs['Color']); nt.links.new(norm.outputs['Normal'],p.inputs['Normal'])
    return m

arr_stone=arr_mat('Calcaire creme',(.79,.73,.60),.79,texture=True)
arr_trim=arr_mat('Pierre sculptee',(.88,.83,.71),.66,texture=True)
arr_floor=arr_mat('Dalles de Bourgogne',(.67,.60,.46),.75,texture=True)
arr_dark=arr_mat('Marbre vert',(.065,.15,.13),.36,texture=True)
arr_grout=arr_mat('Joints et terre',(.20,.18,.13),.94)
arr_gold=arr_mat('Bronze dore patine',(.67,.39,.095),.27,.82)
arr_iron=arr_mat('Fer forge',(.025,.035,.03),.45,.72)
arr_light=arr_mat('Lumiere des lanternes',(1,.72,.29),.24)
arr_light.node_tree.nodes['PBR'].inputs['Emission Color'].default_value=(1,.57,.17,1)
arr_light.node_tree.nodes['PBR'].inputs['Emission Strength'].default_value=2.0

def arr_add(group,mat,verts,faces,smooth=False):
    key=(group,mat.name,smooth); b=arr_batches.setdefault(key,{'verts':[],'faces':[],'mat':mat})
    off=len(b['verts']); b['verts'].extend(verts); b['faces'].extend(tuple(off+i for i in f) for f in faces)

def arr_box(group,mat,x,y,z,w,h,d,yaw=0):
    c=math.cos(yaw); s=math.sin(yaw)
    v=[(x+sx*w/2*c+sz*d/2*s,y+sy*h/2,z-sx*w/2*s+sz*d/2*c) for sx,sy,sz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    arr_add(group,mat,v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)])

def arr_lathe(group,mat,x,y,z,profile,n=16,flute=0):
    v=[]; f=[]; k=len(profile)
    for i in range(n):
        a=i*math.tau/n
        for r,h in profile:
            rr=r*(1+flute*math.cos(a*12)); v.append((x+rr*math.cos(a),y+h,z+rr*math.sin(a)))
    for i in range(n):
        for j in range(k-1):
            a=i*k+j; b=((i+1)%n)*k+j; f.append((a,a+1,b+1,b))
    f.extend([tuple(i*k for i in range(n)),tuple(i*k+k-1 for i in reversed(range(n)))])
    arr_add(group,mat,v,f,True)

def arr_path(group,mat,points,r=.025,sides=6,closed=False):
    v=[]; f=[]; count=len(points)
    for i,p in enumerate(points):
        a=Vector(points[(i-1)%count] if closed else points[max(0,i-1)])
        b=Vector(points[(i+1)%count] if closed else points[min(count-1,i+1)])
        t=(b-a).normalized(); u=t.cross(Vector((0,0,1)))
        if u.length<.01: u=t.cross(Vector((0,1,0)))
        u.normalize(); w=t.cross(u).normalized()
        for j in range(sides): v.append(tuple(Vector(p)+r*(math.cos(j*math.tau/sides)*u+math.sin(j*math.tau/sides)*w)))
    for i in range(count if closed else count-1):
        for j in range(sides): f.append((i*sides+j,i*sides+(j+1)%sides,((i+1)%count)*sides+(j+1)%sides,((i+1)%count)*sides+j))
    if not closed: f.extend([tuple(reversed(range(sides))),tuple((count-1)*sides+j for j in range(sides))])
    arr_add(group,mat,v,f,True)

def arr_sector(group,mat,r0,r1,a0,a1,y0,y1,n=4):
    v=[]
    for y in [y0,y1]:
        for r in [r0,r1]:
            for i in range(n+1):
                a=a0+(a1-a0)*i/n; v.append((r*math.sin(a),y,r*math.cos(a)))
    k=n+1; f=[]
    for i in range(n):
        f.extend([(i,i+1,k+i+1,k+i),(2*k+i,3*k+i,3*k+i+1,2*k+i+1),(i,2*k+i,2*k+i+1,i+1),(k+i,k+i+1,3*k+i+1,3*k+i)])
    f.extend([(0,k,3*k,2*k),(n,2*k+n,3*k+n,k+n)])
    arr_add(group,mat,v,f)

def arr_scroll(group,x,y,z,scale=.13,mirror=1):
    arr_path(group,arr_gold,[(x+mirror*scale*(1-t*.72)*math.cos(t*math.tau*1.2),y+scale*(1-t*.72)*math.sin(t*math.tau*1.2),z) for t in np.linspace(0,1,20)],.018,5)

def arr_frame(group,mat,x,y,z,w,h,r=.02):
    arr_path(group,mat,[(x-w/2,y-h/2,z),(x+w/2,y-h/2,z),(x+w/2,y+h/2,z),(x-w/2,y+h/2,z)],r,5,True)

# Foundation, with the only continuous upward surface BELOW the jointed paving.
arr_lathe('01 Terrasse',arr_grout,0,-.30,0,[(7.98,0),(7.98,.276)],128)
# Concentric stone courses, explicit joints. All paving top surfaces exactly y=0.
for ring,(r0,r1,n) in enumerate([(.586,1.55,32),(1.556,2.65,40),(2.656,3.85,48),(3.856,5.10,64),(5.106,6.35,72),(6.356,7.33,88),(7.336,8,96)]):
    for i in range(n):
        a0=i*math.tau/n+.0014; a1=(i+1)*math.tau/n-.0014
        mat=arr_trim if ring in [0,6] else (arr_dark if ring==4 and i%4==0 else arr_floor)
        arr_sector('01 Terrasse',mat,r0,r1,a0,a1,-.023,0,3)
# Compass rose tessellates the centre disc: every face at y=0, no underlay faces.
for i in range(16):
    a=i*math.tau/16; b=(i+1)*math.tau/16; mid=(a+b)/2
    p0=(0,0,0); p1=(.58*math.sin(a),0,.58*math.cos(a)); p2=(.58*math.sin(b),0,.58*math.cos(b)); p3=(.23*math.sin(mid),0,.23*math.cos(mid))
    arr_add('01 Terrasse',arr_gold if i%2==0 else arr_trim,[p0,p1,p3],[(0,1,2)])
    arr_add('01 Terrasse',arr_trim if i%2==0 else arr_gold,[p0,p3,p2],[(0,1,2)])
    arr_add('01 Terrasse',arr_dark,[p1,p2,p3],[(0,1,2)])

# Forty continuous parapet bays share the existing collision envelope at R7.65.
for i in range(40):
    a0=i*math.tau/40; a1=(i+1)*math.tau/40
    for r0,r1,y0,y1,mat in [(7.47,7.83,0,.16,arr_trim),(7.53,7.77,.16,.34,arr_stone),(7.49,7.81,.34,.40,arr_trim),(7.47,7.83,.975,1.045,arr_trim),(7.49,7.81,1.045,1.09,arr_gold)]:
        arr_sector('02 Balustrade',mat,r0,r1,a0,a1,y0,y1,3)
    for j in range(3):
        a=a0+(j+.5)*(a1-a0)/3; x=7.65*math.sin(a); z=7.65*math.cos(a)
        arr_lathe('02 Balustrade',arr_trim,x,.40,z,[(.095,0),(.095,.055),(.067,.09),(.055,.17),(.103,.28),(.09,.35),(.052,.42),(.047,.50),(.086,.535),(.086,.575)],10)
    if i%5==0:
        x=7.65*math.sin(a0); z=7.65*math.cos(a0)
        for y,w,h,mat in [(.19,.43,.38,arr_trim),(.68,.31,.60,arr_stone),(1.03,.43,.12,arr_trim)]: arr_box('02 Balustrade',mat,x,y,z,w,h,w,a0)
        arr_lathe('02 Balustrade',arr_gold,x,1.10,z,[(.16,0),(.16,.04),(.11,.07),(.08,.13),(.13,.19),(.08,.27),(.015,.31)],14)

# Portico: the existing two columns become fluted Ionic shafts and moulded capitals.
for x in [-2.6,2.6]:
    for y,w,h,mat in [(.075,.85,.15,arr_stone),(.19,.77,.08,arr_trim),(.245,.64,.03,arr_gold)]: arr_box('03 Portique',mat,x,y,-4,w,h,w)
    arr_lathe('03 Portique',arr_trim,x,.26,-4,[(.30,0),(.30,.08),(.24,.13),(.25,.18),(.215,.22)],32)
    arr_lathe('03 Portique',arr_stone,x,.48,-4,[(.215,0),(.215,.14),(.196,2.92),(.215,3.02)],48,.038)
    arr_lathe('03 Portique',arr_gold,x,3.44,-4,[(.223,0),(.223,.055),(.25,.09),(.25,.13)],24)
    arr_box('03 Portique',arr_trim,x,3.63,-4,.80,.20,.80)
    arr_box('03 Portique',arr_gold,x,3.75,-4,.83,.04,.83)
    for z in [-4.30,-3.70]:
        for side in [-1,1]:
            arr_path('03 Portique',arr_trim,[(x+side*(.18+.135*(1-t*.8)*math.cos(t*math.tau*1.30)),3.57+.135*(1-t*.8)*math.sin(t*math.tau*1.30),z) for t in np.linspace(0,1,23)],.037,6)
    for j in range(10):
        a=j*math.tau/10
        arr_path('03 Portique',arr_gold,[(x+.235*math.sin(a),3.49,-4+.235*math.cos(a)),(x+.29*math.sin(a),3.57,-4+.29*math.cos(a))],.014,5)

for y,w,h,d,mat in [(3.83,6.1,.13,.80,arr_trim),(4.01,6.1,.23,.72,arr_stone),(4.15,6.3,.07,.90,arr_gold),(4.22,6.42,.09,1.00,arr_trim)]:
    arr_box('03 Portique',mat,0,y,-4,w,h,d)
# Dentils are actual mouldings with shadowed negative space.
for i in range(29): arr_box('03 Portique',arr_trim,-2.94+i*.21,4.095,-3.535,.09,.10,.10)
# Solid pediment prism and sculpted front rim.
arr_add('03 Portique',arr_stone,[(-3.13,4.265,-4.34),(3.13,4.265,-4.34),(0,5.02,-4.34),(-3.13,4.265,-3.66),(3.13,4.265,-3.66),(0,5.02,-3.66)],[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)])
for z in [-4.38,-3.62]:
    arr_path('03 Portique',arr_trim,[(-3.25,4.26,z),(0,5.07,z),(3.25,4.26,z)],.09,6)
    arr_path('03 Portique',arr_gold,[(-3.06,4.27,z+.045),(0,4.99,z+.045),(3.06,4.27,z+.045)],.023,5)
# Central cartouche and heraldic lily, backed by dark marble.
arr_box('03 Portique',arr_dark,0,4.56,-3.61,.66,.43,.065)
arr_frame('03 Portique',arr_gold,0,4.56,-3.565,.70,.47,.025)
arr_path('03 Portique',arr_gold,[(0,4.36,-3.515),(0,4.70,-3.515),(0,4.75,-3.515)],.039,6)
for s in [-1,1]:
    arr_path('03 Portique',arr_gold,[(0,4.51,-3.515),(s*.16,4.64,-3.515),(s*.21,4.61,-3.515),(s*.16,4.49,-3.515),(s*.05,4.48,-3.515)],.025,6)
    arr_scroll('03 Portique',s*.56,4.48,-3.56,.14,s)
    for j in range(5):
        x=s*(.91+j*.30); y=4.43-j*.014
        arr_path('03 Portique',arr_gold,[(x,y,-3.59),(x+s*.08,y+.08,-3.59),(x+s*.16,y+.025,-3.59)],.018,5)

# The two cypresses retain their authored positions. Stone planters surround them.
for x in [-5,5]:
    arr_lathe('04 Jardinières',arr_grout,x,.10,-3,[(.61,0),(.61,.035)],32)
    arr_lathe('04 Jardinières',arr_stone,x,0,-3,[(.73,0),(.73,.08),(.67,.12),(.65,.34),(.78,.40),(.78,.47),(.66,.47),(.61,.14)],32)
    arr_lathe('04 Jardinières',arr_gold,x,.40,-3,[(.785,0),(.785,.025)],32)
    for j in range(12):
        a=j*math.tau/12
        arr_path('04 Jardinières',arr_trim,[(x+.672*math.sin(a),.14,-3+.672*math.cos(a)),(x+.716*math.sin(a),.27,-3+.716*math.cos(a)),(x+.735*math.sin(a),.38,-3+.735*math.cos(a))],.027,5)

# Lanterns sit on the parapet end piers, clear of the UI and movement zone.
for s in [-1,1]:
    a=s*math.pi/4; x=7.65*math.sin(a); z=7.65*math.cos(a)
    arr_lathe('05 Lanternes',arr_iron,x,1.09,z,[(.14,0),(.14,.05),(.07,.10),(.055,.48),(.15,.53)],16)
    arr_lathe('05 Lanternes',arr_gold,x,1.59,z,[(.22,0),(.25,.055),(.22,.09)],16)
    arr_lathe('05 Lanternes',arr_light,x,1.70,z,[(.065,0),(.065,.33),(.045,.40)],10)
    for j in range(6):
        a=j*math.tau/6; xx=x+.21*math.sin(a); zz=z+.21*math.cos(a)
        arr_path('05 Lanternes',arr_iron,[(xx,1.67,zz),(xx,2.12,zz)],.022,6)
    arr_lathe('05 Lanternes',arr_iron,x,2.08,z,[(.24,0),(.28,.05),(.18,.14),(.07,.25),(.035,.35)],12)
    arr_lathe('05 Lanternes',arr_gold,x,2.43,z,[(.055,0),(.06,.05),(.014,.13)],10)

# Keep semantic groups while batching each material into a single mesh per group.
for (group,matname,smooth),b in arr_batches.items():
    mesh=bpy.data.meshes.new(group+' '+matname); mesh.from_pydata([(x,-z,y) for x,y,z in b['verts']],[],b['faces']); mesh.update()
    bm=bmesh.new(); bm.from_mesh(mesh); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(mesh); bm.free()
    uv=mesh.uv_layers.new(name='UVMap')
    for p in mesh.polygons:
        p.use_smooth=smooth
        for li in p.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv=(v.x*.5,v.y*.5) if abs(p.normal.z)>.6 else ((v.x*.5,v.z*.5) if abs(p.normal.y)>.6 else (v.y*.5,v.z*.5))
    mesh.materials.append(b['mat']); obj=bpy.data.objects.new(group+' '+matname,mesh); arr_scene.collection.objects.link(obj); arr_objects.append(obj)

bpy.ops.object.select_all(action='DESELECT')
for obj in arr_objects: obj.select_set(True)
bpy.context.view_layer.objects.active=arr_objects[0]
bpy.ops.export_scene.gltf(filepath=str(ARR_OUT/'arrival.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_yup=True,export_animations=False,export_image_format='JPEG',export_jpeg_quality=90)
for obj in arr_objects: obj.data.calc_loop_triangles()
arr_stats={'asset':'arrival','url':'gltf/arrival/arrival.glb','bytes':(ARR_OUT/'arrival.glb').stat().st_size,'triangles':sum(len(o.data.loop_triangles) for o in arr_objects),'meshes':len(arr_objects),'floorHeight':0,'radius':8,'columnPositions':[[-2.6,0,-4],[2.6,0,-4]],'panelClearance':'original panel and navigation transforms preserved'}
(ARR_EVID/'asset-stats.json').write_text(json.dumps(arr_stats,indent=2))

arr_world=bpy.data.worlds.new('Arrival daylight'); arr_world.use_nodes=True
arr_bg=next(n for n in arr_world.node_tree.nodes if n.type=='BACKGROUND'); arr_bg.inputs[0].default_value=(.62,.73,.86,1); arr_bg.inputs[1].default_value=.7; arr_scene.world=arr_world
arr_sun_data=bpy.data.lights.new('Arrival sun','SUN'); arr_sun_data.energy=2.3; arr_sun_data.angle=.1
arr_sun=bpy.data.objects.new('Arrival sun',arr_sun_data); arr_scene.collection.objects.link(arr_sun); arr_sun.rotation_euler=(.55,-.4,-.5)
for name,pos,target in [('Accueil visiteur',(0,-2,1.65),(0,4,2.1)),('Accueil ensemble',(11,-12,9),(0,0,1.6))]:
    data=bpy.data.cameras.new(name); camera=bpy.data.objects.new(name,data); arr_scene.collection.objects.link(camera); camera.location=pos
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler(); data.lens=25 if name=='Accueil visiteur' else 35
    if name=='Accueil ensemble': arr_scene.camera=camera
arr_scene.render.resolution_x=1400; arr_scene.render.resolution_y=1000; arr_scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(ARR_EVID/'arrival-realistic.blend'),compress=True)
print(json.dumps(arr_stats))
