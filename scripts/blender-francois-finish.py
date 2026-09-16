"""Microfibre PBR textures and matte beard on the continuous facial surface."""
import bpy,bmesh,math,json,struct,zlib
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/francois'
scene=bpy._natural_scene;bpy.context.window.scene=scene
def png(path,data):
    h,w,c=data.shape
    def chunk(kind,body):return struct.pack('!I',len(body))+kind+body+struct.pack('!I',zlib.crc32(kind+body)&0xffffffff)
    raw=b''.join(b'\0'+row.tobytes() for row in data)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))
for asset,m in bpy._natural_models.items():
    female=asset=='courtFemale';scale=.95 if female else 1
    ob=next(o for o in m['objects'] if 'Implantation continue' in o.name)
    # Soften the sculpting grooves while retaining every hairline boundary vertex.
    bm=bmesh.new();bm.from_mesh(ob.data)
    interior=[v for v in bm.verts if not v.is_boundary]
    for _ in range(3):bmesh.ops.smooth_vert(bm,verts=interior,factor=.38,use_axis_x=True,use_axis_y=True,use_axis_z=True)
    bm.to_mesh(ob.data);bm.free()
    layer=ob.data.uv_layers.new(name='GroomUV')
    for poly in ob.data.polygons:
        us=[(i%192)/192 for i in poly.vertices];seam=max(us)-min(us)>.8
        for li in poly.loop_indices:
            vi=ob.data.loops[li].vertex_index;u=(vi%192)/192
            if seam and u<.2:u+=1
            layer.data[li].uv=(u,vi//192/24)
    # Procedural texture is authored here, not sourced from the reference photographs.
    w,h=2048,512;x=np.arange(w,dtype=np.float32)[None,:]/w;y=np.arange(h,dtype=np.float32)[:,None]/h
    phase=x*TAU*590+(.5 if female else .18)*np.sin(y*8+x*TAU*3)
    fine=np.sin(phase)+.35*np.sin(phase*1.731+np.sin(y*21))
    noise=np.random.default_rng(42 if female else 43).random((h,w),dtype=np.float32)
    tone=np.clip(.92+.14*fine+.06*noise,.60,1.30)
    col=np.stack([tone*.167,tone*.098,tone*.058],axis=-1)
    colorpath=OUT/(asset+'-hair-color.png');png(colorpath,np.uint8(np.clip(col*255,0,255)))
    nx=.14*np.cos(phase);ny=.015*np.sin(y*20+phase);nz=np.sqrt(1-nx*nx-ny*ny)
    normal=np.stack([nx*.5+.5,ny*.5+.5,nz*.5+.5],axis=-1)
    normalpath=OUT/(asset+'-hair-normal.png');png(normalpath,np.uint8(normal*255))
    mat=ob.data.materials[0].copy();mat.name=asset+' Chevelure microfibres';ob.data.materials[0]=mat
    shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    shader.inputs['Roughness'].default_value=.62
    for path,color_space,target in [(colorpath,'sRGB','Base Color'),(normalpath,'Non-Color','Normal')]:
        tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=False);tex.image.colorspace_settings.name=color_space;tex.image.pack()
        if target=='Normal':
            node=mat.node_tree.nodes.new('ShaderNodeNormalMap');node.inputs['Strength'].default_value=.55
            mat.node_tree.links.new(tex.outputs['Color'],node.inputs['Color']);mat.node_tree.links.new(node.outputs['Normal'],shader.inputs['Normal'])
        else:mat.node_tree.links.new(tex.outputs['Color'],shader.inputs[target])
    if not female:
        face=m['face'];mat=face.data.materials[0].copy();mat.name='Barbe mate continue Francois Ier'
        shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        shader.inputs['Roughness'].default_value=.90;shader.inputs['Subsurface Weight'].default_value=0
        shader.inputs['Specular IOR Level'].default_value=.17
        idx=len(face.data.materials);face.data.materials.append(mat)
        colors=face.data.color_attributes['Complexion']
        for poly in face.data.polygons:
            if sum(colors.data[i].color[0] for i in poly.vertices)/len(poly.vertices)<.18:poly.material_index=idx
        # Round the lower beard softly without introducing any separate surface.
        base=face.data.shape_keys.key_blocks[0]
        for i,v in enumerate(base.data):
            h0=v.co.z/scale+.05;x0=v.co.x/scale;d0=-v.co.y/scale-.045
            weight=math.exp(-(x0/.045)**2)*math.exp(-((h0-1.530)/.013)**2)*max(0,min(1,(d0-.025)/.03))
            for key in face.data.shape_keys.key_blocks:key.data[i].co.z-=.0025*scale*weight
    # Warm dark brown on the bun, beard fibres and small nape strands.
    for item in m['objects']:
        for mat in item.data.materials:
            if 'chatain profond' not in mat.name:continue
            shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
            shader.inputs['Base Color'].default_value=(.019,.007,.0035,1);mat.diffuse_color=(.019,.007,.0035,1)
            shader.inputs['Roughness'].default_value=.77
    # The hairline treatment itself must survive the generic secondary-mesh optimisation.
    ob['keepDetail']=True
bpy.data.libraries.write(str(OUT/'renaissance-francois-work.blend'),{scene},fake_user=True,compress=True)
print('Fine hair textures packed, scalp grooves softened, beard material made matte')
