import bpy, json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/scene-fbx'
def snapshot():
    result={}
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH':continue
        ob.data.calc_loop_triangles()
        coords=[ob.matrix_world@Vector(c) for c in ob.bound_box]
        result[ob.name]={'triangles':len(ob.data.loop_triangles),'vertices':len(ob.data.vertices),
            'bounds':[min(v[i] for v in coords) for i in range(3)]+[max(v[i] for v in coords) for i in range(3)]}
    return result
bpy.ops.wm.open_mainfile(filepath=str(OUT/'scene-composee.blend'))
bpy.context.view_layer.update();source=snapshot()
source_inside=source['Interieur_Chateau']
report={}
for file in ['scene-complete.fbx','interieur-chateau.fbx']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(OUT/file),use_anim=False)
    bpy.context.view_layer.update();actual=snapshot()
    expected=source if file=='scene-complete.fbx' else {'Interieur_Chateau':source_inside}
    assert set(actual)==set(expected),('object mismatch',file,set(actual)^set(expected))
    maximum=0
    for name,record in expected.items():
        got=actual[name]
        assert record['triangles']==got['triangles'],('triangles changed',name)
        assert record['vertices']==got['vertices'],('vertices changed',name)
        error=max(abs(a-b) for a,b in zip(record['bounds'],got['bounds']))
        maximum=max(maximum,error)
        assert error<.002,('placement or scale changed',name,error)
    inside=bpy.data.objects['Interieur_Chateau']
    assert inside.type=='MESH'
    image_names=[]
    for img in bpy.data.images:
        if img.source!='FILE':continue
        assert len(img.pixels)>0,('texture missing',img.name,img.filepath)
        image_names.append(img.name)
    assert image_names, 'no imported textures'
    report[file]={'passed':True,'meshes':len(actual),'triangles':sum(o['triangles'] for o in actual.values()),
        'maxBoundsErrorMeters':maximum,'interior':actual['Interieur_Chateau'],'texturesLoaded':len(image_names),
        'checks':['All meshes present','Vertex and triangle counts preserved','World placement and scale preserved within 2 mm','Interior is one separate mesh','Embedded FBX textures loaded']}
    print('VERIFIED',file,len(actual),maximum,flush=True)
(OUT/'verification-blender.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
