# Clear grass at the new gateway connection on the distant copy only.
bm=bmesh.new();bm.from_mesh(estate.data)
remove=[]
for face in bm.faces:
 center=face.calc_center_median()
 if abs(center.x)<3.6 and -31.1<center.y<-26.9 and -.2<center.z<.4:remove.append(face)
bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(estate.data);bm.free();estate.data.validate();estate.data.update()
estate.location-=Vector((100,95,0));export('estateExterior',[estate]);estate.location+=Vector((100,95,0))
bpy.data.libraries.write(str(EVID/'accueil-paysage.blend'),{scene},fake_user=True,compress=True)
(EVID/'asset-stats.json').write_text(json.dumps({'assets':stats,'trees':len(placements),'estateOffset':spec['offset'],'sourcePlacements':len(spec['placements'])},indent=2))
print('Grass cleared at the gateway:',len(remove))
