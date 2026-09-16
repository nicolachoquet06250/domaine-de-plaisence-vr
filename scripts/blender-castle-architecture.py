def cextrude(asset,mat,outline,z,depth):
    n=len(outline); vv=[(x,y,z+sg*depth/2) for sg in [-1,1] for x,y in outline]
    faces=[tuple(reversed(range(n))),tuple(n+i for i in range(n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)); cadd(asset,mat,vv,faces)

def carch(cx,bottom,width,height):
    r=width/2; spring=bottom+height-r
    return [(cx-r,bottom),(cx+r,bottom)]+[(cx+r*math.cos(i*math.pi/20),spring+r*math.sin(i*math.pi/20)) for i in range(21)]

def cwindow(x,bottom,z,w,h,sg=1,door=False):
    r=w/2; spring=bottom+h-r; outward=z+sg*.28
    line=[(x-r,bottom,outward),(x-r,spring,outward)]+[(x+r*math.cos(math.pi-i*math.pi/20),spring+r*math.sin(math.pi-i*math.pi/20),outward) for i in range(21)]+[(x+r,bottom,outward)]
    cpath('palace',ctrim,line,.115,6)
    cpath('palace',cgold,[(a,b,c+sg*.045) for a,b,c in line],.021,5)
    if not door:
        cextrude('palaceGlass',cglass,carch(x,bottom+.025,w-.055,h-.035),z,.012)
        cbox('palace',cwood,x,bottom+h/2,z+sg*.02,.07,h,.07)
        for yy in [bottom+h*.34,bottom+h*.67]: cbox('palace',cwood,x,yy,z+sg*.02,w,.065,.075)
        cbox('palace',ctrim,x,bottom-.1,z+sg*.22,w+.5,.18,.72)
        cbox('palace',ctrim,x,bottom-.24,z+sg*.23,w+.27,.1,.52)
        csolid.append({'kind':'box','position':[x,bottom+h/2,z],'size':[w,h,.22]})
    else:
        # Glazed arched transom above the moving rectangular leaves.
        transom=[(x-r,bottom+2.9),(x+r,bottom+2.9)]+[(x+r*math.cos(i*math.pi/20),spring+r*math.sin(i*math.pi/20)) for i in range(21)]
        cextrude('palaceGlass',cglass,transom,z,.012)
        cbox('palace',cgold,x,bottom+2.9,z+sg*.06,w,.075,.09)
        for i in range(1,6):
            a=i*math.pi/6
            cpath('palace',cgold,[(x,bottom+2.9,z+sg*.065),(x+r*.94*math.cos(a),spring+r*.94*math.sin(a),z+sg*.065)],.022,5)
    # Voussoirs, keystone, lintel cornice and carved shell on the first floor.
    for i in range(9):
        a=math.pi*(i+.5)/9
        cpath('palace',cstone,[(x+(r+.11)*math.cos(a),spring+(r+.11)*math.sin(a),outward),(x+(r+.26)*math.cos(a),spring+(r+.26)*math.sin(a),outward)],.055,4)
    cbox('palace',ctrim,x,bottom+h+.08,outward,.28,.35,.27)
    if not door:
        cbox('palace',ctrim,x,bottom+h+.34,z+sg*.23,w+.65,.12,.63)
        for i in range(7):
            a=i*math.pi/6
            cpath('palace',cgold,[(x,bottom+h+.40,z+sg*.39),(x+.22*math.cos(a),bottom+h+.40+.18*math.sin(a),z+sg*.39)],.016,5)

def cwall(lo,hi,z,centres,height=10.4,sg=1,entry=False):
    for low,high,bottom,h in [(.64,5.04,1.35,2.95),(5.04,height,5.95,3.05)]:
        holes=[]
        for x in centres:
            door=entry and x==0 and low<1
            holes.append((x,3.2 if door else 1.7,.64 if door else bottom,4.55 if door else h,door))
        cursor=lo
        for x,w,y,h,door in holes:
            r=w/2; left=x-r; right=x+r
            cbox('palace',cstone,(cursor+left)/2,(low+high)/2,z,left-cursor,high-low,.44,True)
            cbox('palace',cstone,x,(low+y)/2,z,w,y-low,.44,True)
            cbox('palace',cstone,x,(y+h+high)/2,z,w,high-y-h,.44,True)
            spring=y+h-r
            for j in range(16):
                a=-r+w*j/16; b=-r+w*(j+1)/16
                ya=spring+math.sqrt(max(0,r*r-a*a)); yb=spring+math.sqrt(max(0,r*r-b*b))
                cextrude('palace',cstone,[(x+a,ya),(x+b,yb),(x+b,y+h),(x+a,y+h)],z,.44)
            cwindow(x,y,z,w,h,sg,door); cursor=right
        cbox('palace',cstone,(cursor+hi)/2,(low+high)/2,z,hi-cursor,high-low,.44,True)

def cturned_wall(lo,hi,x,centres):
    sizes={k:len(b['v']) for k,b in cbatches.items()}; start=len(csolid)
    cwall(lo,hi,x,centres,12.0,1 if x>0 else -1)
    for k,b in cbatches.items():
        for i in range(sizes.get(k,0),len(b['v'])):
            u,y,z=b['v'][i]; b['v'][i]=(z,y,-u)
    for item in csolid[start:]:
        u,y,z=item['position']; w,h,d=item['size']; item['position']=[z,y,-u]; item['size']=[d,h,w]

# True hollow envelope: wall piers and arch spandrels, never a solid building box.
for sg in [-1,1]:
    cwall(-14,14,sg*6,[-11.5,-8.6,-5.7,0,5.7,8.6,11.5],10.4,sg,sg==1)
    for x in [-17.5,17.5]: cwall(x-3.5,x+3.5,sg*7,[x-1.7,x+1.7],12.0,sg)
# Central end-wall bays are solid masonry behind the four fireplaces.
for x in [-21,21]: cturned_wall(-7,7,x,[-3.7,3.7])
# Short returns between the projecting pavilions and the main wing.
for x in [-14,14]:
    for z in [-6.5,6.5]: cbox('palace',cstone,x,6.3,z,.44,11.4,1,True)

# Basement, two continuous side salon floors, upper galleries around stair void.
cbox('palace',cstone,0,.25,0,42,.5,12,True)
# Structural backing stops below the finish; the actual inlay is tiled below.
cbox('palaceInterior',cmarble,0,.55,0,9.3,.10,11.6,True)
csolid.append({'kind':'box','position':[0,.62,0],'size':[9.3,.04,11.6]})
for x in [-12.725,12.725]:
    cbox('palaceInterior',cparquet,x,.57,0,16.15,.14,11.6,True)
    cbox('palaceInterior',cparquet,x,4.91,0,16.15,.26,11.6,True)
    cbox('palaceInterior',cplaster,x,4.745,0,16.15,.03,11.6)
for x in [-17.5,17.5]:
    for z in [-6.275,6.275]:
        cbox('palaceInterior',cparquet,x,.57,z,6.6,.14,.95,True)
        cbox('palaceInterior',cparquet,x,4.91,z,6.6,.26,.95,True)
        cbox('palaceInterior',cplaster,x,4.745,z,6.6,.03,.95)
cbox('palaceInterior',cmarble,0,4.91,3.94,9.3,.26,3.68,True)
# Rear upper slab omitted: no access from the intermediate stair landing.
cbox('palaceInterior',cplaster,0,10.26,0,28,.24,11.65)
for x in [-17.5,17.5]: cbox('palaceInterior',cplaster,x,11.86,0,6.6,.24,13.5)

# Terraced approach, treads rise 16 cm; 3.2 m entrance stays unobstructed.
for i in range(4):
    front=9.5-i*.64; top=(i+1)*.16
    # Follow the stepped facade footprint, avoiding coplanar pavilion floors.
    for lo,hi,back in [(-14,14,5.8),(-21+i*.11,-14,7.0),(14,21-i*.11,7.0)]:
        cbox('palace',ctrim,(lo+hi)/2,top/2,(front+back)/2,hi-lo,top,front-back,True)
for sg in [-1,1]:
    for y,thick,depth in [(.85,.26,.70),(5.0,.22,.65),(5.2,.10,.78),(9.95,.18,.73),(10.2,.24,.88),(10.43,.12,1.0)]:
        # Base string course skips the entrance.
        if y<1 and sg==1:
            for x in [-7.95,7.95]: cbox('palace',ctrim,x,y,sg*6,12.6,thick,depth)
        else: cbox('palace',ctrim,0,y,sg*6,28.2,thick,depth)
    for x in [-17.5,17.5]:
        for y in [.8,5.0,5.22,11.6,11.86,12.1]:
            cbox('palace',ctrim,x,y,sg*7,7.3,.16,.74)
            cbox('palace',ctrim,x+(3.45 if x>0 else -3.45),y,0,.65,.16,14.35)
    # Quoin courses and facade pilasters.
    for x in [-20.7,-14.3,-3.6,3.6,14.3,20.7]:
        zz=7 if abs(x)>14 else 6
        for i in range(20 if abs(x)>14 else 17): cbox('palace',ctrim,x,1.13+i*.53,sg*(zz+.24),.56 if i%2 else .72,.43,.21)
    for x in [-10,-6.6,6.6,10]:
        cbox('palace',ctrim,x,7.23,sg*6.25,.25,4.0,.20)
        cbox('palace',cgold,x,9.32,sg*6.37,.4,.08,.1)
    for x in [-12.7,-9.3,-6.0,-2.4,2.4,6.,9.3,12.7]:
        cbox('palace',ctrim,x,10.0,sg*6.48,.14,.32,.22)

def croof(x,z,w,d,y,h):
    # Broken mansard profile, closed and watertight.
    vv=[]; ff=[]
    for yy,ww,dd in [(y,w,d),(y+h*.76,w*.72,d*.57),(y+h,w*.61,d*.42)]:
        vv.extend([(x-ww/2,yy,z-dd/2),(x+ww/2,yy,z-dd/2),(x+ww/2,yy,z+dd/2),(x-ww/2,yy,z+dd/2)])
    for ring in range(2):
        for i in range(4): ff.append((ring*4+i,ring*4+(i+1)%4,(ring+1)*4+(i+1)%4,(ring+1)*4+i))
    ff.extend([(0,3,2,1),(8,9,10,11)]); cadd('palace',cslate,vv,ff)
    for dx in [-1,1]:
        for dz in [-1,1]: cpath('palace',ciron,[(x+dx*w/2,y,z+dz*d/2),(x+dx*w*.36,y+h*.76,z+dz*d*.285),(x+dx*w*.305,y+h,z+dz*d*.21)],.047,6)
    cpath('palace',cgold,[(x-w*.305,y+h+.03,z-d*.21),(x+w*.305,y+h+.03,z-d*.21),(x+w*.305,y+h+.03,z+d*.21),(x-w*.305,y+h+.03,z+d*.21)],.045,6,True)

croof(0,0,28.8,12.9,10.5,3.1)
for x in [-17.5,17.5]: croof(x,0,7.9,14.8,12.16,3.6)
croof(0,0,8.7,12.9,12.0,4.0)
for x in [-11.4,-7.8,7.8,11.4]:
    for dx in [-.63,.63]: cbox('palace',ctrim,x+dx,11.6,5.15,.22,1.72,.75)
    for yy in [10.78,12.42]: cbox('palace',ctrim,x,yy,5.15,1.48,.12,.75)
    cbox('palace',ciron,x,11.6,5.43,1.1,1.55,.04)
    cextrude('palaceGlass',cglass,carch(x,10.95,1.0,1.25),5.55,.015)
    cframe('palace',cgold,x,11.56,5.59,1.1,1.3,.045)
    cextrude('palace',ctrim,[(x-.98,12.47),(x+.98,12.47),(x,13.12)],5.15,.9)
    cpath('palace',cgold,[(x-.98,12.49,5.63),(x,13.14,5.63),(x+.98,12.49,5.63)],.035,5)
for x in [-18.6,-11.4,-6.5,6.5,11.4,18.6]:
    yy=15.1 if abs(x)>14 else 13.8
    cbox('palace',cstone,x,yy,-2.8,.80,2.1,.93)
    for dy in [-.9,.75,1.0]: cbox('palace',ctrim,x,yy+dy,-2.8,1.04,.16,1.17)
    for dx in [-.22,.22]: clathe('palace',ciron,x+dx,yy+1.1,-2.8,[(.11,0),(.11,.28)],10)

# Grand portico: profiled Ionic columns, volutes, dentils and gilded pediment.
for x in [-3.25,3.25]:
    cbox('palace',ctrim,x,.79,7.0,.82,.30,.82,True)
    clathe('palace',ctrim,x,.94,7.,[(.40,0),(.40,.1),(.31,.17),(.29,.26),(.25,.36),(.235,4.30),(.33,4.38),(.35,4.53)],24,.055)
    cbox('palace',ctrim,x,5.58,7.,.86,.18,.86)
    for sg in [-1,1]:
        cpath('palace',cgold,[(x+sg*.27+.19*(1-i/45)*math.cos(i*.28),5.35+.19*(1-i/45)*math.sin(i*.28),7.43) for i in range(36)],.025,6)
cbox('palace',ctrim,0,5.91,6.82,8.3,.43,1.5)
cbox('palace',cgold,0,6.13,7.58,8.3,.065,.065)
for x in range(-18,19): cbox('palace',ctrim,x*.215,5.67,7.45,.09,.20,.19)
cextrude('palace',ctrim,[(-4.4,6.2),(4.4,6.2),(0,8.28)],6.90,1.20)
cpath('palace',cgold,[(-4.38,6.24,7.54),(0,8.29,7.54),(4.38,6.24,7.54)],.06,7)
cpath('palace',ctrim,[(-4.48,6.24,7.53),(0,8.39,7.53),(4.48,6.24,7.53)],.11,6)
# Heraldic shield, crown, laurel leaves and paired scrolls as actual relief.
cextrude('palace',cgold,[(-.44,7.42),(.44,7.42),(.38,6.91),(0,6.65),(-.38,6.91)],7.6,.13)
for sg in [-1,1]:
    cpath('palace',cgold,[(sg*(.40+.43*math.sin(i*math.pi/24)),6.74+i*.034,7.64) for i in range(25)],.033,6)
    for i in range(9):
        yy=6.80+i*.08; xx=sg*(.48+.32*math.sin(i*math.pi/10))
        cextrude('palace',cgold,[(xx,yy),(xx+sg*.21,yy+.06),(xx+sg*.06,yy+.19)],7.65,.04)
    cpath('palace',cgold,[(sg*(1.0+.38*math.cos(i*.22)*(1-i/60)),7.0+.28*math.sin(i*.22)*(1-i/60),7.58) for i in range(45)],.03,6)
for x in [-.3,0,.3]:
    cpath('palace',cgold,[(x,7.43,7.69),(x,7.68,7.69)],.055,7)
    clathe('palace',cgold,x,7.66,7.69,[(.02,0),(.075,.05),(.02,.1)],10)
for x in [-17.5,0,17.5]:
    yy=16.05 if x==0 else 15.8
    clathe('palace',cgold,x,yy,0,[(.22,0),(.14,.18),(.23,.34),(.15,.55),(.065,.64),(.045,1.18),(0,1.36)],16)

# Balcony balusters on the terrace with an open centre approach.
baluster=[(.105,0),(.105,.08),(.06,.14),(.095,.26),(.08,.42),(.045,.53),(.07,.61)]
for sg in [-1,1]:
    # End caps stop at x=13.68, 10 cm clear of the pavilion return wall.
    for yy,hh,dd in [(.74,.20,.40),(.86,.07,.36),(1.48,.10,.36),(1.57,.09,.44)]:
        cbox('palace',ctrim,sg*9.4,yy,7.31,8.1,hh,dd)
    for yy in [.885,1.525]: cbox('palace',cgold,sg*9.4,yy,7.52,8.1,.026,.025)
    for i in range(16):
        xx=sg*(5.68+i*.495)
        clathe('palace',ctrim,xx,.895,7.31,[(r,h*.9) for r,h in baluster],12,.06)
        clathe('palace',cgold,xx,1.12,7.31,[(.091,0),(.091,.035)],12)
    for x in [5.35,9.4,13.45]:
        xx=sg*x
        cbox('palace',ctrim,xx,1.17,7.31,.38,.98,.38,True)
        for yy in [.86,1.48,1.67]: cbox('palace',ctrim,xx,yy,7.31,.46,.08,.46)
        cframe('palace',cgold,xx,1.18,7.51,.27,.47,.018)
        clathe('palace',ctrim,xx,1.71,7.31,[(.14,0),(.12,.07),(.18,.19),(.12,.30),(.045,.35),(0,.41)],12)
        for side in [-1,1]:
            cpath('palace',cgold,[(xx+side*(.035+.075*math.cos(j*.3)*(1-j/35)),1.18+.12*math.sin(j*.3)*(1-j/35),7.535) for j in range(24)],.012,5)
print('Hollow facade, glazed openings, mansard roofs and carved gilding generated')
