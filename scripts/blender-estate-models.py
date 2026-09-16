"""Run through Blender MCP. Metric models, +Z up, front -Y (= glTF +Z)."""
import bpy, math, json
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT = Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
OUT = ROOT / 'public/gltf/estate'
OUT.mkdir(parents=True, exist_ok=True)
(ROOT / 'artifacts/blender').mkdir(parents=True, exist_ok=True)
# A dedicated scene preserves anything already open in Blender.
scene = bpy.data.scenes.new('Estate assets — Blender MCP')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
scene.render.fps = 24
scene.frame_start, scene.frame_end = 1, 97
groups = {}

def material(name, color, rough=.6, metal=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    p = m.node_tree.nodes.new('ShaderNodeBsdfPrincipled'); p.name='Principled BSDF'
    output = m.node_tree.nodes.new('ShaderNodeOutputMaterial')
    m.node_tree.links.new(p.outputs['BSDF'], output.inputs['Surface'])
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    return m

def textured(name, base, wood=False):
    m = material(name, base, .7)
    n = 512
    y, x = np.mgrid[0:n, 0:n].astype(np.float32) / n
    rng = np.random.default_rng(31 if wood else 52)
    noise = rng.random((n,n)).astype(np.float32)
    if wood:
        grain = np.sin(y*430 + 5*np.sin(x*12) + 2*np.sin(y*60+x*9))
        field = .86 + .075*grain + .05*np.sin(y*960+x*13) + .1*noise
    else:
        field = .87 + .06*np.sin(x*53+np.sin(y*61))*np.sin(y*49) + .13*noise
        field -= .14*(noise > .986)
    pixels = np.ones((n,n,4), dtype=np.float32)
    pixels[:,:,:3] = np.clip(np.array(base)[None,None,:]*field[:,:,None], 0, 1)
    img = bpy.data.images.new(name+' albedo 512', width=n, height=n)
    img.pixels.foreach_set(pixels.ravel())
    img.pack()
    tree = m.node_tree
    tex = tree.nodes.new('ShaderNodeTexImage'); tex.image = img
    tree.links.new(tex.outputs['Color'], tree.nodes.get('Principled BSDF').inputs['Base Color'])
    # Actual tangent normal texture, preserved in glTF (no procedural nodes at runtime).
    gy, gx = np.gradient(field)
    normal = np.ones((n,n,4), dtype=np.float32)
    normal[:,:,0] = .5-gx*.35; normal[:,:,1] = .5-gy*.35; normal[:,:,2] = 1
    normal_img = bpy.data.images.new(name+' normal 512', width=n, height=n)
    normal_img.colorspace_settings.name = 'Non-Color'
    normal_img.pixels.foreach_set(normal.ravel()); normal_img.pack()
    nt = tree.nodes.new('ShaderNodeTexImage'); nt.image=normal_img
    nm = tree.nodes.new('ShaderNodeNormalMap')
    tree.links.new(nt.outputs['Color'], nm.inputs['Color'])
    tree.links.new(nm.outputs['Normal'], tree.nodes.get('Principled BSDF').inputs['Normal'])
    return m

oak = textured('Weathered oak', (.48,.31,.16), True)
stone = textured('Warm limestone', (.73,.68,.57))
iron = material('Patinated green cast iron', (.055,.09,.074), .48, .7)
bronze = material('Aged brass fittings', (.30,.22,.10), .36, .75)
wetstone = material('Submerged limestone', (.18,.25,.20), .65)

def keep(obj, group, mat):
    obj.data.materials.append(mat)
    groups.setdefault(group, []).append(obj)
    return obj

def box(group, name, loc, size, mat, bevel=.015):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj=bpy.context.object; obj.name=name; obj.dimensions=size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod=obj.modifiers.new('Soft worn edges','BEVEL'); mod.width=bevel; mod.segments=2
        bpy.ops.object.modifier_apply(modifier=mod.name)
        mod=obj.modifiers.new('Weighted face normals','WEIGHTED_NORMAL')
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return keep(obj,group,mat)

def mesh(group, name, verts, faces, mat, smooth=True):
    data=bpy.data.meshes.new(name); data.from_pydata(verts,[],faces); data.update()
    obj=bpy.data.objects.new(name,data); scene.collection.objects.link(obj)
    for p in data.polygons: p.use_smooth=smooth
    return keep(obj,group,mat)

def lathe(group,name,profile,mat,segments=64,start=0,end=math.tau):
    verts=[]; faces=[]
    for i in range(segments+1):
        a=start+(end-start)*i/segments
        verts.extend((r*math.cos(a),r*math.sin(a),z) for r,z in profile)
    k=len(profile)
    for i in range(segments):
        for j in range(k-1):
            a=i*k+j; faces.append((a,a+k,a+k+1,a+1))
    if end-start < math.tau-.001:
        faces.extend([tuple(range(k-1,-1,-1)),tuple(segments*k+j for j in range(k))])
    obj=mesh(group,name,verts,faces,mat)
    uv=obj.data.uv_layers.new()
    for poly in obj.data.polygons:
        for li in poly.loop_indices:
            vi=obj.data.loops[li].vertex_index
            uv.data[li].uv=(vi//k/segments*4, profile[vi%k][1]*2)
    return obj

def tube(group,name,points,radius,mat,sides=8):
    verts=[]; faces=[]
    for i,p in enumerate(points):
        tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
        tangent.normalize(); normal=tangent.cross(Vector((1,0,0)))
        if normal.length < .1: normal=tangent.cross(Vector((0,1,0)))
        normal.normalize(); binormal=tangent.cross(normal)
        for j in range(sides):
            a=math.tau*j/sides; v=Vector(p)+radius*(math.cos(a)*normal+math.sin(a)*binormal)
            verts.append(tuple(v))
    for i in range(len(points)-1):
        for j in range(sides):
            a=i*sides+j; b=i*sides+(j+1)%sides
            faces.append((a,b,b+sides,a+sides))
    return mesh(group,name,verts,faces,mat)

# 2.1 m bench: spaced bevelled slats, curved arms, cast legs and brass fasteners.
for i in range(5):
    box('bench','Oak seat slat', (0,-.25+i*.12,.515),(2.1,.105,.065),oak,.012)
for i in range(4):
    obj=box('bench','Reclined oak back slat',(0,.28+i*.025,.69+i*.11),(2.1,.062,.09),oak,.009)
    obj.rotation_euler.x=-.15
for x in [-.76,.76]:
    for y in [-.23,.23]:
        tube('bench','Splayed cast leg',[(x,y*1.28,.055),(x,y,.26),(x,y*.82,.49)],.036,iron)
        box('bench','Foot plate',(x,y*1.28,.035),(.16,.13,.07),iron,.012)
    tube('bench','Back support',[(x,.21,.42),(x,.28,.73),(x,.36,1.045)],.032,iron)
    tube('bench','Curved armrest',[(x,-.25,.5),(x,-.28,.66),(x,-.20,.76),(x,0,.79),(x,.28,.77)],.038,iron)
    tube('bench','Underseat cradle',[(x,-.3,.46),(x,0,.44),(x,.29,.48)],.037,iron)
    # Side scroll, recognisable at seated viewing distance.
    pts=[]
    for i in range(25):
        a=i/24*math.tau*1.2; r=.10*(1-i/32)
        pts.append((x,.03+r*math.cos(a),.65+r*math.sin(a)))
    tube('bench','Cast scroll',pts,.012,iron,6)
    for i in range(5):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=.012,location=(x,-.25+i*.12,.55))
        keep(bpy.context.object,'bench',bronze)
box('bench','Cross brace',(0,.12,.25),(1.52,.05,.07),iron,.008)

# Same 8.74 m footprint and nozzle positions as the original scene/collisions.
lathe('basin','Stepped circular plinth',[(0,0),(4.30,0),(4.37,.06),(4.37,.14),(4.27,.2),(3.72,.2),(0,.2)],stone,96)
lathe('basin','Wet basin floor',[(0,.205),(3.84,.205),(3.84,.24),(0,.24)],wetstone,80)
profile=[(3.79,.18),(4.21,.18),(4.23,.26),(4.16,.3),(4.14,.52),(4.23,.56),(4.24,.64),(4.20,.70),(3.87,.70),(3.81,.64),(3.86,.57),(3.84,.29),(3.79,.18)]
for i in range(32):
    lathe('basin','Radial coping block %02d'%i,profile,stone,3,i*math.tau/32+.001,(i+1)*math.tau/32-.001)
lathe('basin','Moulded central pedestal',[(0,.2),(.66,.2),(.67,.28),(.54,.34),(.46,.42),(.38,.69),(.48,.74),(.51,.82),(.4,.88),(0,.88)],stone,48)
lathe('basin','Bronze central rose',[(0,.88),(.36,.88),(.39,.92),(.3,.97),(.1,.97),(.1,1.01),(0,1.01)],bronze,40)
for i in range(6):
    a=i*math.tau/6
    obj=lathe('basin','Brass lateral nozzle',[(0,.24),(.18,.24),(.19,.31),(.13,.34),(.09,.47),(.065,.50),(0,.50)],bronze,16)
    obj.location=(3.1*math.cos(a),3.1*math.sin(a),0)

def merge(group):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in groups[group]: obj.select_set(True)
    bpy.context.view_layer.objects.active=groups[group][0]
    bpy.ops.object.join()
    obj=bpy.context.object; obj.name=group
    scene.cursor.location=(0,0,0); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    groups[group]=[obj]
    return obj

for name in ['bench','basin']: merge(name)
print(json.dumps({'created':{k:len(v[0].data.polygons) for k,v in groups.items()}}))
