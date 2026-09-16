import bpy,math,json
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update');OUT=ROOT/'artifacts/avatars/francois';report={}
for asset,m in bpy._natural_models.items():
    scale=.95 if asset=='courtFemale' else 1
    for ob in m['objects']:
        if not ob.get('hairDynamics'):continue
        d=ob['hairDynamics'].to_dict();center=[0,1.625*scale,.018*scale];radii=[.078*scale,.100*scale,.100*scale]
        distances=[math.sqrt(sum(((p[k]-center[k])/radii[k])**2 for k in range(3))) for p in d['points']]
        factor=min(1,min(distances)*.97)
        d['headCenter']=center;d['headRadii']=[r*factor for r in radii];ob['hairDynamics']=d
        report[asset]={'interiorColliderScale':factor,'minimumRestClearanceNormalized':min(distances)/factor}
code=(ROOT/'scripts/blender-refined-export.py').read_text(encoding='utf-8-sig')
start=code.index("    for ob in m['objects']:");end=code.index('    for ob in joined:\n',start)
code=code[:start]+"    joined=m['objects'];gaps=[.0033]\n"+code[end:]
code=code.replace('artifacts/avatars/refined','artifacts/avatars/francois').replace('renaissance-refined.blend','renaissance-francois.blend')
exec(compile(code,'francois-collision-export','exec'))
(OUT/'colliders.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
