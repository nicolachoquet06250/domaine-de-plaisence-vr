"""Blender MCP castle authoring. Helpers accept metres in the application's Y-up space."""
import bpy, math, json, random, bmesh
import numpy as np
from pathlib import Path
from mathutils import Vector
CROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
COUT=CROOT/'public/gltf/castle'; COUT.mkdir(parents=True,exist_ok=True)
CEVID=CROOT/'artifacts/castle'; CEVID.mkdir(parents=True,exist_ok=True)
cscene=bpy.data.scenes.new('Chateau - Architecture et interieur'); bpy.context.window.scene=cscene
cscene.unit_settings.system='METRIC'; cscene.render.fps=30; cscene.frame_start=1; cscene.frame_end=49
cbatches={}; cobjects={}; csolid=[]; crng=random.Random(108)

def cmat(name,color,rough=.65,metal=0,alpha=1):
    m=bpy.data.materials.new('Chateau '+name); m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear(); p=nt.nodes.new('ShaderNodeBsdfPrincipled'); p.name='PBR'
    p.inputs['Base Color'].default_value=(*color,alpha); p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metal; p.inputs['Alpha'].default_value=alpha
    out=nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(p.outputs['BSDF'],out.inputs['Surface'])
    m.diffuse_color=(*color,alpha); m.use_backface_culling=True
    if alpha<1: m.surface_render_method='DITHERED'; m.use_backface_culling=False
    return m

def ctexture(name,kind,base,rough=.75,size=512):
    m=cmat(name,(1,1,1),rough); rng=np.random.default_rng(sum(map(ord,name)))
    y,x=np.mgrid[0:size,0:size]/size; noise=rng.random((size,size))-.5
    if kind=='stone':
        field=.94+.06*noise+.025*np.sin(x*math.tau*5)*np.cos(y*math.tau*7)
        mortar=(np.minimum((y*8)%1,1-(y*8)%1)<.015)| (np.minimum((x*4+(np.floor(y*8)%2)*.5)%1,1-(x*4+(np.floor(y*8)%2)*.5)%1)<.008)
        field-=mortar*.12
    elif kind=='slate':
        row=np.floor(y*14); xx=(x*7+(row%2)*.5)%1; yy=(y*14)%1
        field=.80+.10*np.sin(x*math.tau*7+y*math.tau*14)+.15*noise
        field-=((xx<.027)|(yy<.06))*.35
    elif kind=='marble':
        wave=np.sin(x*math.tau*3+y*math.tau*2+.6*np.sin(y*math.tau*5)+.24*np.sin(x*math.tau*11))
        field=.98-.18*np.exp(-(wave*14)**2)+.02*noise
    elif kind=='parquet':
        ix=np.floor(x*8); iy=np.floor(y*8); odd=(ix+iy)%2
        grain=np.sin((x*(1-odd)+y*odd)*math.tau*96+.6*np.sin(y*math.tau*8))
        field=.76+.10*grain+.14*np.sin((ix*7+iy*3)*2.7)+.05*noise
        field-=(((x*8)%1<.025)|((y*8)%1<.025))*.2
    elif kind=='wood': field=.79+.10*np.sin(x*math.tau*33+.9*np.sin(y*math.tau*2))+.04*noise
    else: field=.94+.04*np.cos(x*math.tau*10)*np.cos(y*math.tau*10)+.02*noise
    rgba=np.ones((size,size,4),dtype=np.float32); rgba[:,:,:3]=np.clip(np.array(base)*field[:,:,None],0,1)
    img=bpy.data.images.new('Chateau '+name+' color',width=size,height=size); img.pixels.foreach_set(rgba.ravel()); img.pack()
    nt=m.node_tree; tex=nt.nodes.new('ShaderNodeTexImage'); tex.image=img; nt.links.new(tex.outputs['Color'],nt.nodes['PBR'].inputs['Base Color'])
    normal=np.ones((size,size,4),dtype=np.float32)
    strength=.012 if kind=='marble' else .28
    normal[:,:,0]=.5-(np.roll(field,-1,1)-np.roll(field,1,1))*strength
    normal[:,:,1]=.5-(np.roll(field,-1,0)-np.roll(field,1,0))*strength
    im=bpy.data.images.new('Chateau '+name+' normal',width=size,height=size); im.colorspace_settings.name='Non-Color'; im.pixels.foreach_set(normal.ravel()); im.pack()
    tex=nt.nodes.new('ShaderNodeTexImage'); tex.image=im; nm=nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(tex.outputs['Color'],nm.inputs['Color']); nt.links.new(nm.outputs['Normal'],nt.nodes['PBR'].inputs['Normal'])
    return m

cstone=ctexture('Calcaire de taille','stone',(.83,.79,.69))
ctrim=cmat('Moulures ivoire',(.88,.84,.74),.65)
cslate=ctexture('Ardoises jointoyees','slate',(.22,.28,.32),.64)
cgold=cmat('Bronze dore patine',(.72,.45,.13),.26,.83)
ciron=cmat('Ferronnerie noire',(.047,.054,.052),.45,.72)
cwood=ctexture('Chene des portes','wood',(.28,.14,.06),.42)
cparquet=ctexture('Parquet Versailles','parquet',(.48,.29,.13),.52)
cmarble=ctexture('Marbre creme veine','marble',(.90,.86,.75),.3)
cdark=ctexture('Marbre noir','marble',(.13,.15,.15),.32)
cplaster=cmat('Stuc creme',(.86,.81,.70),.85)
cblue=ctexture('Soie bleu grise','silk',(.25,.39,.43),.86)
cred=ctexture('Velours bordeaux','silk',(.34,.085,.08),.88)
cglass=cmat('Verre clair reflets',(.77,.90,.94),.065,.18,.22)
cglass.node_tree.nodes['PBR'].inputs['IOR'].default_value=1.46
clamp=cmat('Bougies chaudes',(1,.75,.35),.32)
clamp.node_tree.nodes['PBR'].inputs['Emission Color'].default_value=(1,.61,.24,1)
clamp.node_tree.nodes['PBR'].inputs['Emission Strength'].default_value=3

def cadd(asset,mat,verts,faces,smooth=False):
    key=(asset,mat.name,smooth); batch=cbatches.setdefault(key,{'v':[],'f':[],'mat':mat})
    start=len(batch['v']); batch['v'].extend(verts); batch['f'].extend(tuple(start+i for i in face) for face in faces)

def cbox(asset,mat,x,y,z,w,h,d,solid=False):
    if min(w,h,d)<=0: return
    vv=[(x+sx*w/2,y+sy*h/2,z+sz*d/2) for sx,sy,sz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    cadd(asset,mat,vv,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)])
    if solid: csolid.append({'kind':'box','position':[x,y,z],'size':[w,h,d]})

def cpath(asset,mat,points,r=.035,sides=6,closed=False):
    vv=[]; ff=[]
    for i,p in enumerate(points):
        a=Vector(points[(i-1)%len(points)] if closed else points[max(i-1,0)]); b=Vector(points[(i+1)%len(points)] if closed else points[min(i+1,len(points)-1)])
        tangent=(b-a).normalized(); axis=tangent.cross(Vector((0,0,1)))
        if axis.length<.01: axis=tangent.cross(Vector((0,1,0)))
        axis.normalize(); other=tangent.cross(axis).normalized()
        for j in range(sides): vv.append(tuple(Vector(p)+r*(math.cos(j*math.tau/sides)*axis+math.sin(j*math.tau/sides)*other)))
    for i in range(len(points) if closed else len(points)-1):
        for j in range(sides):
            a=i*sides+j; b=i*sides+(j+1)%sides; c=((i+1)%len(points))*sides+(j+1)%sides; d=((i+1)%len(points))*sides+j
            ff.append((a,b,c,d))
    if not closed: ff.extend([tuple(reversed(range(sides))),tuple((len(points)-1)*sides+j for j in range(sides))])
    cadd(asset,mat,vv,ff,True)

def clathe(asset,mat,x,y,z,profile,n=16,flute=0):
    vv=[]; ff=[]; k=len(profile)
    for i in range(n):
        a=i*math.tau/n
        for r,h in profile:
            rr=r*(1+flute*math.cos(a*12)); vv.append((x+rr*math.cos(a),y+h,z+rr*math.sin(a)))
    for i in range(n):
        for j in range(k-1):
            a=i*k+j; b=((i+1)%n)*k+j; ff.append((a,a+1,b+1,b))
    ff.extend([tuple(i*k for i in range(n)),tuple(i*k+k-1 for i in reversed(range(n)))])
    cadd(asset,mat,vv,ff,True)

def cframe(asset,mat,x,y,z,w,h,r=.035):
    cpath(asset,mat,[(x-w/2,y-h/2,z),(x+w/2,y-h/2,z),(x+w/2,y+h/2,z),(x-w/2,y+h/2,z)],r,4,True)

def cflush(asset):
    result=[]
    for (a,name,smooth),b in list(cbatches.items()):
        if a!=asset: continue
        mesh=bpy.data.meshes.new(a+' '+name); mesh.from_pydata([(x,-z,y) for x,y,z in b['v']],[],b['f']); mesh.update()
        bm=bmesh.new(); bm.from_mesh(mesh); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(mesh); bm.free()
        uv=mesh.uv_layers.new(name='UVMap')
        for p in mesh.polygons:
            p.use_smooth=smooth
            for li in p.loop_indices:
                v=mesh.vertices[mesh.loops[li].vertex_index].co
                uv.data[li].uv=(v.x*.5,v.y*.5) if abs(p.normal.z)>.6 else ((v.x*.5,v.z*.5) if abs(p.normal.y)>.6 else (v.y*.5,v.z*.5))
        mesh.materials.append(b['mat']); obj=bpy.data.objects.new(a+' '+name,mesh); cscene.collection.objects.link(obj); result.append(obj)
        del cbatches[(a,name,smooth)]
    cobjects[asset]=result; return result

print('Castle builders and PBR materials ready')
