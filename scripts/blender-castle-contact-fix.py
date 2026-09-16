# One-off equivalent of the updated bathtub feet in the authoring source.
# Apply only to the already-exported refinement, not during a fresh regeneration.
changed=0
for obj in cobjects['palaceInterior']:
    if obj.type!='MESH' or not any(m==cgold for m in obj.data.materials): continue
    for v in obj.data.vertices:
        p=v.co
        if not 5.0399<=p.z<=5.405: continue
        if any(abs(p.x-(sg*17.8+dx))<.15 and abs(p.y-(3.55+dz))<.18 for sg in [-1,1] for dx in [-.43,.43] for dz in [-.77,.77]):
            p.z=5.04+(p.z-5.04)*1.4; changed+=1
    obj.data.update()
cstats['palaceInterior']=cexport('palaceInterior',cobjects['palaceInterior'])
(CEVID/'asset-stats.json').write_text(json.dumps(cstats,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(CEVID/'chateau-plaisance.blend'),compress=True)
print('Bathtub support contact corrected:',changed)
