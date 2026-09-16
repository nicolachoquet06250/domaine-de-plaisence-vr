# One-off rotation matching the room-facing vanity in the generation source.
for obj in cobjects['palaceInterior']:
    for v in obj.data.vertices:
        p=v.co
        if 5.0399<=p.z<6.50 and abs(p.y+4.60)<.56:
            for sg in [-1,1]:
                cx=sg*17.2
                if abs(p.x-cx)<.80: p.x=2*cx-p.x; p.y=-9.2-p.y; break
    obj.data.update()
cstats['palaceInterior']=cexport('palaceInterior',cobjects['palaceInterior'])
(CEVID/'asset-stats.json').write_text(json.dumps(cstats,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(CEVID/'chateau-plaisance.blend'),compress=True)
print('Vanity fronts now face the room')
