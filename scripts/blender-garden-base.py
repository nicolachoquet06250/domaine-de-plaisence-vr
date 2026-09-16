"""Garden authoring, run with Blender MCP. Meters, Z up; glTF exports Y up."""
import bpy, math, json, random
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
GOUT=ROOT/'public/gltf/garden'; GOUT.mkdir(parents=True,exist_ok=True)
EVIDENCE=ROOT/'artifacts/garden'; EVIDENCE.mkdir(parents=True,exist_ok=True)
garden_scene=bpy.data.scenes.new('Garden - source assets')
bpy.context.window.scene=garden_scene
garden_scene.unit_settings.system='METRIC'
gparts={}; grng=random.Random(2047)

def gm(name,color,roughness=.8):
    m=bpy.data.materials.new('Garden '+name); m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    p=nt.nodes.new('ShaderNodeBsdfPrincipled'); p.name='PBR'
    p.inputs['Base Color'].default_value=(*color,1); p.inputs['Roughness'].default_value=roughness
    out=nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(p.outputs['BSDF'],out.inputs['Surface'])
    m.diffuse_color=(*color,1); m.use_backface_culling=True
    return m

def gtexture(name,kind,base,size=512):
    m=gm(name,(1,1,1),.88)
    y,x=np.mgrid[0:size,0:size].astype(np.float32)/size
    rng=np.random.default_rng(sum(map(ord,kind)))
    fine=rng.random((size,size)).astype(np.float32)
    # Periodic multi-frequency detail avoids seams without large bitmaps.
    coarse=np.sin(x*math.tau*3+np.sin(y*math.tau*2))*np.sin(y*math.tau*4)
    mid=np.sin(x*math.tau*31+np.sin(y*math.tau*11))*np.sin(y*math.tau*37)
    field=.86+.10*coarse+.07*mid+.14*(fine-.5)
    if kind=='grass':
        field=.82+.015*coarse+.018*mid+.20*fine
        # Sparse cut blades in a tile; normals carry close-view structure.
        for i in range(2600):
            px=int(rng.integers(size)); py=int(rng.integers(size)); length=int(rng.integers(4,13))
            for k in range(length):
                field[(py+k)%size,(px+k//4)%size] += .18*(1-k/length)
    elif kind=='gravel':
        field=np.full((size,size),.55,dtype=np.float32)
        for i in range(3700):
            px=int(rng.integers(size)); py=int(rng.integers(size)); rad=int(rng.integers(2,7)); value=rng.uniform(.65,1.08)
            for dy in range(-rad,rad+1):
                for dx in range(-rad,rad+1):
                    d=(dx*dx+dy*dy)/(rad*rad)
                    if d<1: field[(py+dy)%size,(px+dx)%size]=value*(.73+.27*math.sqrt(1-d))
        field+=fine*.08
    elif kind=='hedge':
        field=.65+.13*mid+.14*fine
        for i in range(850):
            px=int(rng.integers(size)); py=int(rng.integers(size)); rx=int(rng.integers(3,9)); ry=int(rng.integers(4,12))
            value=rng.uniform(.65,1.25)
            for dy in range(-ry,ry+1):
                for dx in range(-rx,rx+1):
                    d=(dx/rx)**2+(dy/ry)**2
                    if d<1: field[(py+dy)%size,(px+dx)%size]=value*(.8+.2*math.sqrt(1-d))
    elif kind=='leaf':
        field=.85+.1*np.sin(y*math.pi)+.04*fine
        field+=.18*np.exp(-((x-.5)*75)**2)
        field+=.08*(np.cos((y+np.abs(x-.5)*.7)*math.tau*11)>.96)
    elif kind=='bark':
        field=.7+.20*np.sin(x*math.tau*18+np.sin(y*math.tau*2))+.12*fine
    rgba=np.ones((size,size,4),dtype=np.float32)
    rgba[:,:,:3]=np.clip(np.array(base)[None,None,:]*field[:,:,None],0,1)
    img=bpy.data.images.new(name+' color',width=size,height=size)
    img.pixels.foreach_set(rgba.ravel()); img.file_format='JPEG'; img.pack()
    nt=m.node_tree; t=nt.nodes.new('ShaderNodeTexImage'); t.image=img
    nt.links.new(t.outputs['Color'],nt.nodes['PBR'].inputs['Base Color'])
    dy=(np.roll(field,-1,axis=0)-np.roll(field,1,axis=0))*.5
    dx=(np.roll(field,-1,axis=1)-np.roll(field,1,axis=1))*.5
    strength=1.9 if kind in ['gravel','hedge','bark'] else 1
    normal=np.ones((size,size,4),dtype=np.float32)
    normal[:,:,0]=.5-dx*strength; normal[:,:,1]=.5-dy*strength; normal[:,:,2]=1
    im=bpy.data.images.new(name+' normal',width=size,height=size); im.colorspace_settings.name='Non-Color'
    im.pixels.foreach_set(normal.ravel()); im.pack()
    t=nt.nodes.new('ShaderNodeTexImage'); t.image=im
    nm=nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(t.outputs['Color'],nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'],nt.nodes['PBR'].inputs['Normal'])
    return m

grass=gtexture('Clipped meadow','grass',(.34,.43,.20),1024)
gravel=gtexture('Crushed limestone','gravel',(.73,.66,.52))
limestone=gtexture('Weathered limestone','stone',(.76,.72,.63))
hedge_mat=gtexture('Boxwood leaf clusters','hedge',(.24,.36,.12))
leaf_mat=gtexture('Living leaf','leaf',(.31,.44,.16),256)
bark_mat=gtexture('Cypress bark','bark',(.32,.25,.17),256)
soil=gtexture('Garden loam','soil',(.24,.18,.12),256)
petal_mat=gm('Rose petals',(1,1,1),.66)
for mat in [leaf_mat,petal_mat]:
    mat.use_backface_culling=False
    attr=mat.node_tree.nodes.new('ShaderNodeVertexColor'); attr.layer_name='Tint'
    if mat==petal_mat: mat.node_tree.links.new(attr.outputs['Color'],mat.node_tree.nodes['PBR'].inputs['Base Color'])
    else:
        tex=next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image.colorspace_settings.name!='Non-Color')
        mix=mat.node_tree.nodes.new('ShaderNodeMixRGB'); mix.blend_type='MULTIPLY'; mix.inputs[0].default_value=1
        mat.node_tree.links.new(tex.outputs['Color'],mix.inputs[1]); mat.node_tree.links.new(attr.outputs['Color'],mix.inputs[2])
        mat.node_tree.links.new(mix.outputs[0],mat.node_tree.nodes['PBR'].inputs['Base Color'])

def gmesh(asset,name,verts,faces,mat,uv=None,colors=None,smooth=True):
    data=bpy.data.meshes.new(name); data.from_pydata(verts,[],faces); data.update()
    obj=bpy.data.objects.new(name,data); garden_scene.collection.objects.link(obj); data.materials.append(mat)
    for p in data.polygons: p.use_smooth=smooth
    layer=data.uv_layers.new(name='UVMap')
    for p in data.polygons:
        for li in p.loop_indices:
            vi=data.loops[li].vertex_index; v=data.vertices[vi].co
            if uv: layer.data[li].uv=uv[vi]
            elif abs(p.normal.z)>.5: layer.data[li].uv=(v.x*2,v.y*2)
            elif abs(p.normal.y)>.5: layer.data[li].uv=(v.x*2,v.z*2)
            else: layer.data[li].uv=(v.y*2,v.z*2)
    if colors:
        attr=data.color_attributes.new(name='Tint',type='FLOAT_COLOR',domain='POINT')
        for i,c in enumerate(colors): attr.data[i].color=(*c,1)
    gparts.setdefault(asset,[]).append(obj); return obj

def gbox(asset,name,loc,scale,mat,bevel=.015):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    obj=bpy.context.object; obj.name=name; obj.dimensions=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=obj.modifiers.new('Worn edge bevel','BEVEL'); mod.width=bevel; mod.segments=1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.data.materials.append(mat)
    # Project real metric UVs, including sides, instead of stretching cube UVs.
    uv=obj.data.uv_layers.active; uv.name='UVMap'
    for p in obj.data.polygons:
        for li in p.loop_indices:
            v=obj.data.vertices[obj.data.loops[li].vertex_index].co+obj.location
            uv.data[li].uv=(v.x*2,v.y*2) if abs(p.normal.z)>.5 else ((v.x*2,v.z*2) if abs(p.normal.y)>.5 else (v.y*2,v.z*2))
    gparts.setdefault(asset,[]).append(obj); return obj

def glathe(asset,name,profile,mat,segments=32,flute=0):
    vv=[]; ff=[]; uv=[]
    for i in range(segments+1):
        a=i*math.tau/segments
        for r,z in profile:
            rr=r+flute*math.cos(a*12)*max(0,math.sin((z-.2)*math.pi))
            vv.append((rr*math.cos(a),rr*math.sin(a),z)); uv.append((a*r*2,z*2))
    k=len(profile)
    for i in range(segments):
        for j in range(k-1):
            a=i*k+j; ff.append((a,a+k,a+k+1,a+1))
    return gmesh(asset,name,vv,ff,mat,uv)

class GLeaves:
    def __init__(self): self.v=[]; self.f=[]; self.uv=[]; self.c=[]
    def leaf(self,center,length,width,angle,tilt,tint=(1,1,1)):
        c=Vector(center); along=Vector((math.cos(angle)*math.cos(tilt),math.sin(angle)*math.cos(tilt),math.sin(tilt)))
        across=Vector((-math.sin(angle),math.cos(angle),0)); up=across.cross(along)*-.08*length
        s=len(self.v)
        self.v.extend([tuple(c-along*length*.5),tuple(c+across*width*.5),tuple(c+along*length*.5),tuple(c-across*width*.5),tuple(c+up)])
        self.f.extend((s+i,s+(i+1)%4,s+4) for i in range(4))
        self.uv.extend([(0.5,0),(0,.5),(.5,1),(1,.5),(.5,.5)])
        self.c.extend([tint]*5)
    def finish(self,asset,name,mat=leaf_mat): return gmesh(asset,name,self.v,self.f,mat,self.uv,self.c)

class GPetals(GLeaves):
    def leaf(self,center,length,width,angle,tilt,tint=(1,1,1)):
        c=Vector(center); along=Vector((math.cos(angle)*math.cos(tilt),math.sin(angle)*math.cos(tilt),math.sin(tilt)))
        across=Vector((-math.sin(angle),math.cos(angle),0)); up=along.cross(across)
        outline=[(-.5,0),(-.20,-.46),(.32,-.50),(.52,0),(.32,.50),(-.20,.46)]
        s=len(self.v)
        for u,v in outline:
            self.v.append(tuple(c+along*u*length+across*v*width+up*(abs(v)*.10*length)))
            self.uv.append((v+.5,u+.5))
        self.v.append(tuple(c-up*.08*length)); self.uv.append((.5,.5))
        self.f.extend((s+i,s+(i+1)%6,s+6) for i in range(6))
        self.c.extend([tint]*7)

def grose(leaves,petals,x,y,z,scale=1,seed=0):
    rng=random.Random(seed)
    for i in range(12):
        a=i*2.39996; r=.08+.1*rng.random()
        leaves.leaf((x+r*math.cos(a),y+r*math.sin(a),z-.09-rng.random()*.13),.15*scale,.07*scale,a,rng.uniform(-.2,.7),(.8,.95,.65))
    # Layered folded petals give an actual cup silhouette from all sides.
    palette=[(.78,.30,.36),(.92,.67,.51),(.91,.82,.66),(.59,.31,.52)]
    tint=palette[seed%len(palette)]
    for layer,count in [(0,7),(1,6),(2,5)]:
        r=(.064-layer*.016)*scale
        for i in range(count):
            a=i*math.tau/count+layer*.7
            petals.leaf((x+r*math.cos(a),y+r*math.sin(a),z+layer*.026*scale),(.10-layer*.018)*scale,.074*scale,a,-.4+layer*.35,tint)

print('Garden material library and mesh builders ready.')
