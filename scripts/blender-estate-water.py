"""Continue the persistent Blender MCP authoring namespace from models.py."""
watermat=material('Basin water — jade reflections',(.075,.23,.21),.16,.32)
streammat=material('Aerated water',(.40,.66,.65),.17,.28)
foam=material('Sparkling spray',(.72,.86,.83),.28,.12)

def animate_shapes(obj, samples, duration, label):
    obj.shape_key_add(name='Basis')
    keys=[]
    for i,coords in enumerate(samples):
        key=obj.shape_key_add(name='%s_%02d'%(label,i))
        key.data.foreach_set('co',np.array(coords,dtype=np.float32).ravel())
        keys.append(key)
    count=len(keys)
    for i,key in enumerate(keys):
        for step in range(int(count*4/duration)+1):
            key.value=1 if step%count==i else 0
            key.keyframe_insert(data_path='value',frame=1+step*duration*24/count)
    action=obj.data.shape_keys.animation_data.action
    action.name=label
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for point in curve.keyframe_points: point.interpolation='LINEAR'
    for key in keys: key.value=0
    keys[0].value=1

# A tessellated surface with travelling concentric and crossed capillary waves.
verts=[]; faces=[]; nr=25; na=80
for ring in range(nr):
    r=.02+(3.79-.02)*ring/(nr-1)
    for j in range(na):
        a=j*math.tau/na; verts.append((r*math.cos(a),r*math.sin(a),.36))
for ring in range(nr-1):
    for j in range(na):
        a=ring*na+j; b=ring*na+(j+1)%na
        faces.append((a,a+na,b+na,b))
# Radial then angular winding points upwards.
obj=mesh('water','Basin_Water_Surface',verts,faces,watermat)
samples=[]
for phase in range(8):
    t=phase*math.tau/8
    samples.append([(x,y,.36+.013*math.sin(math.hypot(x,y)*16-t)+.007*math.sin(x*12+y*9+t*2)) for x,y,z in verts])
animate_shapes(obj,samples,4,'Basin_Ripples_Loop')

def make_jet(central):
    group='centralJet' if central else 'lateralJet'
    # Central water rises from the brass rose, then splits and falls into the basin.
    def point(t, branch=0):
        if central:
            a=branch*math.tau/7
            return (math.cos(a)*.95*t*t,math.sin(a)*.95*t*t,1.01+15.7*t-16.35*t*t)
        return (-2.15*t,0,.5+8.3*t-8.44*t*t)
    paths=3 if central else 1
    for b in range(paths):
        tube(group,'Continuous water arc',[point(i/40,b) for i in range(41)],.028 if central else .025,streammat,6)
    obj=merge(group)
    base=[tuple(v.co) for v in obj.data.vertices]
    samples=[]
    for phase in range(8):
        t=math.tau*phase/8
        samples.append([(x+.008*math.sin(z*11-t),y+.008*math.cos(z*9-t),z) for x,y,z in base])
    animate_shapes(obj,samples,1,'Central_Stream_Loop' if central else 'Lateral_Stream_Loop')
    # One merged spray mesh; no per-droplet objects or simulation at runtime.
    vv=[]; ff=[]; count=54 if central else 24
    offsets=[(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1.8),(0,0,-1.8)]
    def droplets(phase):
        coords=[]
        for i in range(count):
            t=(i/count+phase)%1
            x,y,z=point(t,i%7)
            if not central: y+=.06*math.sin(i*2.4)*t
            size=(.013+.014*((i*7)%11)/11)*min(1,t*18,(1-t)*18)
            for dx,dy,dz in offsets: coords.append((x+dx*size,y+dy*size,z+dz*size))
        return coords
    vv=droplets(0)
    for i in range(count):
        s=i*6
        for a,b in [(0,2),(2,1),(1,3),(3,0)]:
            ff.append((s+a,s+b,s+4)); ff.append((s+b,s+a,s+5))
    drops=mesh(group,group+'_spray',vv,ff,foam)
    animate_shapes(drops,[droplets(i/12) for i in range(12)],1,group+'_Droplets_Loop')
    obj.name=group+'_stream'

make_jet(False)
make_jet(True)
scene.frame_set(1)
print('Created Blender morph animation clips for ripples, streams and spray.')
