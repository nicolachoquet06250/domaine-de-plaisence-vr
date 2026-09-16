# Deliberate clear sight corridor towards the distant facade; no trees inside the estate.
rng=random.Random(90811);placements=[];tiles={};attempt=0
while len(placements)<132 and attempt<20000:
 attempt+=1;x=rng.uniform(-60,159);z=rng.uniform(-165,48);r=math.hypot(x,z)
 if r<19 or (57<x<143 and -154<z<-49) or pathdistance(x,z)<9:continue
 t=max(0,min(1,(x*100+z*(-123))/(100**2+123**2)))
 if math.hypot(x-100*t,z+123*t)<17:continue
 if any(math.hypot(x-p['x'],z-p['z'])<11 for p in placements):continue
 variant=rng.randrange(3);scale=rng.uniform(.72,1.13);lod=0 if r<47 else 1;angle=rng.random()*math.tau
 pos={'x':x,'z':z,'height':height(x,z),'variant':variant+1,'scale':scale,'yaw':angle,'lod':lod};placements.append(pos)
 key=(int((x+70)//60),int((z+180)//60))
 for source in models[(variant,lod)]:
  o=source.copy();o.data=source.data;scene.collection.objects.link(o);o.hide_render=False;o.hide_set(False)
  o.matrix_world=Matrix.Translation((x,-z,pos['height']))@Matrix.Rotation(-angle,4,'Z')@Matrix.Diagonal((scale,scale,scale,1));tiles.setdefault(key,[]).append(o)
forest=[]
for key,objects in tiles.items():forest.append(combine(objects,'Bois de chenes secteur '+str(key)))
export('forest',forest)
(EVID/'forest-placements.json').write_text(json.dumps(placements,indent=2))
export('terrain',parts['terrain']);export('path',parts['path'])


print('Landscape stage 2 complete',flush=True)
