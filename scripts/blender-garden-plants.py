def ghedge(asset,name,points,width=.36,height=.45,closed=False):
    vv=[]; ff=[]; uv=[]; length=0
    cross=[(-.5,0),(.5,0),(.5,.62),(.43,.85),(.24,.98),(-.24,.98),(-.43,.85),(-.5,.62)]
    for i,(x,y) in enumerate(points):
        before=Vector(points[(i-1)%len(points)] if closed else points[max(0,i-1)])
        after=Vector(points[(i+1)%len(points)] if closed else points[min(len(points)-1,i+1)])
        tangent=(after-before).normalized(); side=Vector((-tangent.y,tangent.x))
        if i: length+=math.dist(points[i-1],points[i])
        for j,(u,v) in enumerate(cross):
            wobble=.008*math.sin(i*2.43+j*1.71)
            vv.append((x+side.x*(u*width+wobble),y+side.y*(u*width+wobble),.045+v*height+wobble))
            uv.append((length*3,j*.21))
    rings=len(points)
    for i in range(rings if closed else rings-1):
        for j in range(8):
            a=i*8+j; b=i*8+(j+1)%8; c=((i+1)%rings)*8+(j+1)%8; d=((i+1)%rings)*8+j
            ff.append((a,d,c,b))
    if not closed: ff.extend([tuple(range(7,-1,-1)),tuple((rings-1)*8+j for j in range(8))])
    obj=gmesh(asset,name,vv,ff,hedge_mat,uv)
    return obj

def line(a,b,step=.34):
    count=max(2,math.ceil(math.dist(a,b)/step)+1)
    return [(a[0]+(b[0]-a[0])*i/(count-1),a[1]+(b[1]-a[1])*i/(count-1)) for i in range(count)]

gbox('parterre','Fine gravel planting bed',(0,0,.027),(14,14,.05),gravel,0)
for sign in [-1,1]:
    for i in range(14):
        gbox('parterre','Limestone edging',(sign*6.93,i-6.5,.09),(.14,.987,.18),limestone,.008)
        gbox('parterre','Limestone edging',(i-6.5,sign*6.93,.09),(.987,.14,.18),limestone,.008)
    for half in [-1,1]:
        ghedge('parterre','Outer clipped hedge',line((sign*6.48,half*3.62-2.9),(sign*6.48,half*3.62+2.9)))
        ghedge('parterre','Outer clipped hedge',line((half*3.62-2.9,sign*6.48),(half*3.62+2.9,sign*6.48)))

leaf_detail=GLeaves(); roses=GLeaves(); rose_petals=GPetals()
for sx in [-1,1]:
    for sy in [-1,1]:
        cx=sx*3.6; cy=sy*3.6
        corners=[(cx+1.92,cy),(cx,cy+1.92),(cx-1.92,cy),(cx,cy-1.92)]
        pts=[]
        for i in range(4): pts.extend(line(corners[i],corners[(i+1)%4])[:-1])
        ghedge('parterre','Diamond clipped boxwood',pts,.31,.43,True)
        pts=[]
        for i in range(64):
            a=i*math.tau/64; r=1.02+.17*math.cos(a*4); pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
        ghedge('parterre','Continuous four-lobed embroidery',pts,.30,.37,True)
        for i in range(14):
            a=i*2.39996; r=.68*math.sqrt((i+.5)/14)
            grose(roses,rose_petals,cx+r*math.cos(a),cy+r*math.sin(a),.56+.075*math.sin(i*2.3),1.1,i+int((sx+1)*8+(sy+1)*4))
        # Each corner gets an irregular clipped sphere, with real peripheral leaves.
        vv=[]; ff=[]; uv=[]; segments=14; rings=9
        for i in range(rings+1):
            t=math.pi*i/rings
            for j in range(segments+1):
                a=math.tau*j/segments; rr=math.sin(t)*(.48+.023*math.sin(a*5+t*8))
                vv.append((sx*5.7+rr*math.cos(a),sy*5.7+rr*math.sin(a),.65+.56*math.cos(t))); uv.append((j/segments*3,i/rings*3))
        for i in range(rings):
            for j in range(segments):
                a=i*(segments+1)+j; ff.append((a,a+1,a+segments+2,a+segments+1))
        gmesh('parterre','Clipped topiary sphere',vv,ff,hedge_mat,uv)
        for i in range(70):
            a=i*2.39996; zz=1-2*(i+.5)/70; rr=math.sqrt(1-zz*zz)
            leaf_detail.leaf((sx*5.7+rr*.49*math.cos(a),sy*5.7+rr*.49*math.sin(a),.65+zz*.56),.075,.045,a,.3,(.75+grng.random()*.35,1,.7))

pts=[]
for i in range(96):
    a=i*math.tau/96; r=1.45+.45*math.cos(a*4); pts.append((r*math.cos(a),r*math.sin(a)))
ghedge('parterre','Centre quatrefoil embroidery',pts,.29,.37,True)
for i in range(14):
    a=i*2.39996; r=.51*math.sqrt((i+.5)/14)
    grose(roses,rose_petals,r*math.cos(a),r*math.sin(a),.51+.07*math.sin(i*2),1.1,40+i)
# Fine leaf silhouettes break the edges without thousands of overlapping spheres.
for obj in list(gparts['parterre']):
    if obj.data.materials[0]!=hedge_mat: continue
    for i in range(0,len(obj.data.vertices),19):
        v=obj.data.vertices[i].co
        if v.z>.20:
            leaf_detail.leaf(tuple(v),.072,.038,grng.random()*math.tau,.3+grng.random()*.5,(.72+grng.random()*.4,1,.72))
leaf_detail.finish('parterre','Boxwood silhouette leaves')
roses.finish('parterre','Rose foliage'); rose_petals.finish('parterre','Garden rose petals',petal_mat)

# A tapered, irregular cypress silhouette, with small branch sprays at its surface.
glathe('cypress','Ridged cypress trunk',[(0,0),(.17,0),(.14,.3),(.10,.8),(.07,1.4),(0,1.6)],bark_mat,10)
vv=[]; ff=[]; uv=[]; sides=22; rings=20
def cypress_radius(t,a):
    return max(.015,.62*math.sin(math.pi*t)**.72)*(1+.10*math.sin(a*5+t*19)+.05*math.sin(a*11-t*25))
for i in range(rings+1):
    t=i/rings
    for j in range(sides+1):
        a=j*math.tau/sides; r=cypress_radius(t,a)
        vv.append((r*math.cos(a),r*math.sin(a),.42+4.58*t)); uv.append((j/sides*4,t*9))
for i in range(rings):
    for j in range(sides):
        a=i*(sides+1)+j; ff.append((a,a+1,a+sides+2,a+sides+1))
gmesh('cypress','Dense irregular cypress crown',vv,ff,hedge_mat,uv)
needles=GLeaves()
for i in range(500):
    t=.025+.95*(i+.5)/500; a=i*2.39996; r=cypress_radius(t,a)
    for k in range(2):
        needles.leaf((r*math.cos(a),r*math.sin(a),.42+4.58*t),.11+.05*grng.random(),.024,a+k*.8,.8,(.66,.86,.64))
needles.finish('cypress','Fine evergreen branch sprays')
print('Created complete parterre with continuous hedges, layered roses and detailed cypress.')
