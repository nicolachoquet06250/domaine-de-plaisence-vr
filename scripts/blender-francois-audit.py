import bpy,json,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/francois'
scene=bpy._natural_scene;bpy.context.window.scene=scene;scene.frame_set(1)
report={'headLoweringMm':scene.get('headLoweringMillimeters'),'nativeParticles':[],'models':{}}
for ob in bpy._organic_emitters:
    ps=ob.particle_systems[0]
    was=ob.hide_get();ob.hide_set(False);bpy.context.view_layer.update()
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());eps=ev.particle_systems[0]
    tree=BVHTree.FromPolygons([v.co.copy() for v in ev.data.vertices],[tuple(p.vertices) for p in ev.data.polygons])
    mod=next(m for m in ev.modifiers if m.type=='PARTICLE_SYSTEM')
    roots=[ps.particles[i].hair_keys[0].co_object(ev,mod,p) for i,p in enumerate(eps.particles)]
    gaps=[tree.find_nearest(root)[3] for root in roots]
    report['nativeParticles'].append({'name':ob.name,'parents':len(ps.particles),'expected':ps.settings.count,'dynamics':ps.use_hair_dynamics,'rootSurfaceGapMax':max(gaps),'exampleRoot':list(roots[0])})
    ob.hide_set(was)
    assert ps.use_hair_dynamics and len(ps.particles)==ps.settings.count
for asset,m in bpy._natural_models.items():
    face=m['face'];keys=face.data.shape_keys.key_blocks
    report['models'][asset]={'beardConstruction':face.get('beardConstruction'),'visemes':[k.name for k in keys][1:],
        'finite':all(math.isfinite(c) for k in keys for v in k.data for c in v.co),
        'headBone':list(m['rig'].data.bones['Head'].head_local)}
(OUT/'anatomy-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
