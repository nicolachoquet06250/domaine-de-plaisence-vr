import bpy,json,re
from pathlib import Path
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/unity-domain-import';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'artifacts/scene-fbx/scene-composee.blend'))
materials=set(m for o in bpy.context.scene.objects if o.type=='MESH' for m in o.data.materials if m)
report=[]
def texture(tex):
    return Path(bpy.path.abspath(tex.image.filepath)).name if tex and tex.image else None
for m in sorted(materials,key=lambda x:x.name):
    w=PrincipledBSDFWrapper(m,is_readonly=True)
    shader=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    base=list(w.base_color)
    if shader.inputs['Base Color'].is_linked and shader.inputs['Base Color'].links[0].from_node.type=='TEX_IMAGE':base=[1,1,1]
    masked=any(n.type=='MATH' and n.operation in {'GREATER_THAN','LESS_THAN'} for n in m.node_tree.nodes)
    report.append({'name':m.name,'baseColor':base,'metallic':w.metallic,'roughness':w.roughness,'masked':masked,'cutoff':.5,
        'alpha':w.alpha,'emission':list(w.emission_color),'emissionStrength':w.emission_strength,
        'baseTexture':texture(w.base_color_texture),'normalTexture':texture(w.normalmap_texture),
        'normalStrength':w.normalmap_strength,'alphaTexture':texture(w.alpha_texture),
        'roughnessTexture':texture(w.roughness_texture),'metallicTexture':texture(w.metallic_texture),
        'emissionTexture':texture(w.emission_color_texture),'doubleSided':not m.use_backface_culling,
        'graph':[(l.from_node.type,l.from_socket.name,l.to_node.type,l.to_socket.name) for l in m.node_tree.links]})
(OUT/'materials-source.json').write_text(json.dumps({'materials':report},indent=2),encoding='utf-8')
print('MATERIALS',len(report))
