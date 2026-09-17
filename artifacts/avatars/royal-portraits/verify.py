import bpy, numpy as np, json
from pathlib import Path
root=Path(r'C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update/artifacts/avatars/royal-portraits')
report=[]
for name in ['homme','femme']:
    path=root/(name+'-pose-royale.png')
    image=bpy.data.images.load(str(path),check_existing=False)
    width,height=image.size[:]
    assert (width,height)==(1600,2400)
    pixels=np.asarray(image.pixels[:],dtype=np.float32).reshape(height,width,4)
    for block in [pixels[:40,:40,:3],pixels[-40:,:40,:3],pixels[:40,-40:,:3],pixels[-40:,-40:,:3]]:
        assert np.all(block>=.999),'Background is not pure white'
    y,x=np.nonzero(np.any(pixels[:,:,:3]<.98,axis=2))
    bounds=[int(x.min()),int(y.min()),int(x.max()),int(y.max())]
    assert bounds[0]>40 and bounds[1]>80 and bounds[2]<width-40 and bounds[3]<height-80,'Cropped figure'
    report.append({'image':path.name,'resolution':[width,height],'background':'#FFFFFF','visibleFigureBounds':bounds,'fullBodyWithinFrame':True})
    bpy.data.images.remove(image)
(root/'verification.json').write_text(json.dumps(report,indent=2))
print('PORTRAITS_VERIFIED',json.dumps(report))
