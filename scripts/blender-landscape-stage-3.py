# Import only the original exterior asset placements; interior files are never loaded.
spec=json.loads((EVID/'exterior-placements.json').read_text());cache={};exterior=[]
for placement in spec['placements']:
 asset=placement['asset']
 if asset not in cache:
  previous=set(scene.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/placement['path']));loaded=[o for o in scene.objects if o not in previous];prototypes=[]
  for o in loaded:
   if o.type!='MESH':continue
   bpy.context.view_layer.objects.active=o
   if len(o.data.polygons)>200:
    mod=o.modifiers.new('Simplification pour vue lointaine','DECIMATE');mod.ratio=.4 if asset=='palace' else .17 if asset in ['parterre','ground','cypress'] else .3
    bpy.ops.object.modifier_apply(modifier=mod.name)
   if asset=='palaceGlass':
    for m in o.data.materials:
     if m and m.use_nodes:
      p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
      if p:p.inputs['Transmission Weight'].default_value=0;p.inputs['Base Color'].default_value=(.08,.13,.15,1);p.inputs['Metallic'].default_value=.5;p.inputs['Roughness'].default_value=.25
   prototypes.append((o.data,o.matrix_world.copy()))
  cache[asset]=prototypes
  for o in loaded:bpy.data.objects.remove(o,do_unlink=True)
 m=placement['matrix'];world=Matrix(tuple(tuple(m[col*4+row] for col in range(4)) for row in range(4)));world=C@world@C.inverted()
 for data,local in cache[asset]:
  o=bpy.data.objects.new(placement['id'],data);scene.collection.objects.link(o);o.matrix_world=world@local;exterior.append(o)
estate=combine(exterior,'Domaine - exterieurs uniquement');export('estateExterior',[estate]);estate.location+=Vector((100,95,0))

# Entrance pillars and open iron leaves, aligned with the existing avenue.
v=[];f=[]
def box(v,f,x,y,z,w,h,d):
 off=len(v);v.extend((x+sx*w/2,y+sy*h/2,z+sz*d/2) for sx,sy,sz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
 f.extend(tuple(off+i for i in face) for face in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)])
for x in [95.7,104.3]:
 box(v,f,x,1.65,-65,.85,3.3,.85);box(v,f,x,3.35,-65,1.1,.22,1.1);box(v,f,x,.15,-65,1.1,.3,1.1)
mesh('gateway','Piliers de l entree',v,f,stone,False)
v=[];f=[]
for x in [95.9,104.1]:
 for j in range(9):box(v,f,x,1.3,-65+j*.37,.06,2.4,.055)
 for y in [.35,2.1]:box(v,f,x,y,-63.5,.07,.08,3.2)
mesh('gateway','Portail ouvert en fer forge',v,f,iron,False);export('gateway',parts['gateway'])

# Only the complete landscape scene is saved, preserving every existing .blend.
scene.world=bpy.data.worlds.new('Lumiere paysage');scene.world.use_nodes=True
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.6,.73,.87,1);bg.inputs[1].default_value=.65
light=bpy.data.lights.new('Soleil paysage','SUN');light.energy=2.2;o=bpy.data.objects.new('Soleil paysage',light);scene.collection.objects.link(o);o.rotation_euler=(.5,-.45,-.7)
data=bpy.data.cameras.new('Vue paysage');camera=bpy.data.objects.new('Vue paysage',data);scene.collection.objects.link(camera);camera.location=(0,-2,1.65);camera.rotation_euler=(Vector((100,123,8))-camera.location).to_track_quat('-Z','Y').to_euler();data.lens=30;scene.camera=camera
bpy.data.libraries.write(str(EVID/'accueil-paysage.blend'),{scene},fake_user=True,compress=True)
(EVID/'asset-stats.json').write_text(json.dumps({'assets':stats,'trees':len(placements),'estateOffset':spec['offset'],'sourcePlacements':len(spec['placements'])},indent=2))
print(json.dumps(stats))

print('Landscape stage 3 complete',flush=True)
