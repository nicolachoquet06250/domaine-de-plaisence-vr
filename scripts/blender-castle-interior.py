# Compartments flank the central vestibule; doorways are genuine 3.2 m gaps.
for x in [-4.65,4.65]:
    for floor in [.64,5.04]:
        top=5.04 if floor<1 else 10.14
        cbox('palaceInterior',cplaster,x,(floor+top)/2,-1.75,.24,top-floor,7.9,True)
        cbox('palaceInterior',cplaster,x,(floor+top)/2,5.60,.24,top-floor,.4,True)
        for jamb in [2.1875,5.4125]:
            cbox('palaceInterior',ctrim,x,floor+1.75,jamb,.25,3.5,.025)
        cbox('palaceInterior',cplaster,x,(floor+3.5+top)/2,3.8,.24,top-floor-3.5,3.2,True)
        for sg in [-1,1]:
            xx=x+sg*.15
            for z in [2.16,5.44]:
                cbox('palaceInterior',ctrim,xx,floor+1.79,z,.16,3.68,.16)
                cbox('palaceInterior',cgold,xx+sg*.045,floor+1.79,z,.04,3.6,.035)
            cbox('palaceInterior',ctrim,xx,floor+3.62,3.8,.18,.20,3.55)
            for z in [-4.7,-2.5,-.3]:
                cbox('palaceInterior',cblue,xx,floor+2.5,z,.025,2.35,1.75)
                # Rotated moulding frames, viewed from both rooms.
                for zz in [z-.91,z+.91]: cbox('palaceInterior',cgold,xx+sg*.025,floor+2.5,zz,.04,2.5,.045)
                for yy in [floor+1.25,floor+3.75]: cbox('palaceInterior',cgold,xx+sg*.025,yy,z,.04,.045,1.86)
                cbox('palaceInterior',ctrim,xx,floor+.56,z,.08,.91,1.77)
            for yy,hh in [(floor+.12,.20),(floor+1.12,.12),(top-.20,.23),(top-.05,.08)]:
                cbox('palaceInterior',ctrim,xx,yy,-1.85,.16,hh,7.65)

# Edge-to-edge stone and brass inlay: every square centimetre has ONE top face.
xs=sorted(set([-4.65,4.65,-4.4275,-4.3725,4.3725,4.4275]+[i+.5 for i in range(-4,4)]))
zs=sorted(set([-5.8,5.8,-5.5275,-5.4725,5.4725,5.5275]+[i+.5 for i in range(-5,5)]))
for xa,xb in zip(xs,xs[1:]):
    for za,zb in zip(zs,zs[1:]):
        x=(xa+xb)/2; z=(za+zb)/2
        gold=(4.3725<abs(x)<4.4275 and abs(z)<5.5275) or (5.4725<abs(z)<5.5275 and abs(x)<4.4275)
        mat=cgold if gold else (cdark if abs(x)<4.3725 and abs(z)<5.4725 and (math.floor(x+.5)+math.floor(z+.5))%2==0 else cmarble)
        cbox('palaceInterior',mat,x,.62,z,xb-xa,.04,zb-za)

def cstairs(x,start,end,y0,y1,w):
    count=14; rise=(y1-y0)/count; run=(end-start)/count
    for i in range(count):
        top=y0+(i+1)*rise; z=start+(i+.5)*run
        # Constant-thickness blocks give the soffit the same inverted stair profile.
        cbox('palaceInterior',cmarble,x,top-.12,z,w,.24,abs(run))
        cbox('palaceInterior',ctrim,x,top-.045,z-run*.51,w+.04,.07,.035)
    csolid.append({'kind':'ramp','from':[x,y0,start],'to':[x,y1,end],'width':w})
    for sg in [-1,1]:
        xx=x+sg*(w/2-.07)
        cpath('palaceInterior',cgold,[(xx,y0+1.02,start),(xx,y1+1.02,end)],.055,8)
        cpath('palaceInterior',ciron,[(xx,y0+.24,start),(xx,y1+.24,end)],.025,6)
        for i in range(count+1):
            t=i/count; yy=y0+(y1-y0)*t; zz=start+(end-start)*t
            cpath('palaceInterior',ciron,[(xx,yy+.05,zz),(xx,yy+1.01,zz)],.021,5)
            if i%2==0:
                cpath('palaceInterior',cgold,[(xx,yy+.47+.19*math.sin(j*math.tau/16),zz+.115*math.cos(j*math.tau/16)) for j in range(16)],.014,5,True)
        # Thin solid rail envelope, sloped with the flight.
        csolid.append({'kind':'rail','from':[xx,y0,start],'to':[xx,y1,end],'width':.10,'height':1.04})

cstairs(0,2.1,-2.1,.64,2.84,2.4)
cbox('palaceInterior',cmarble,0,2.73,-3.94,9.06,.22,3.68,True)
for x in [-3.15,3.15]: cstairs(x,-2.1,2.1,2.84,5.04,2.2)
# Balustrade only across the gap between the two arriving flights.
for i in range(11):
    x=-1.65+i*.33
    cpath('palaceInterior',ciron,[(x,5.04,2.15),(x,6.08,2.15)],.025,6)
cpath('palaceInterior',cgold,[(-1.78,6.10,2.15),(1.78,6.10,2.15)],.06,8)
csolid.append({'kind':'box','position':[0,5.56,2.15],'size':[3.56,1.04,.1]})
for x in [-4.30,4.30]:
    # Both ends and the post caps retain clearance from wall panelling.
    for z in [-5.48,-2.28]: cbox('palaceInterior',ctrim,x,3.34,z,.18,1.0,.18)
    cpath('palaceInterior',cgold,[(x,3.85,-5.48),(x,3.85,-2.28)],.05,6)
    for i in range(10):
        z=-5.35+i*.325
        cpath('palaceInterior',ciron,[(x,2.85,z),(x,3.83,z)],.021,5)

def csupport(x,z,top):
    bottom=.64; h=top-bottom
    cbox('palaceInterior',cmarble,x,bottom+.09,z,.58,.18,.58)
    clathe('palaceInterior',ctrim,x,bottom+.18,z,[(.28,0),(.28,.07),(.22,.14),(.18,.22),(.16,h-.48),(.23,h-.40),(.26,h-.30)],24,.055)
    for y in [bottom+.30,top-.19]: clathe('palaceInterior',cgold,x,y,z,[(.23,0),(.23,.035)],16)
    cbox('palaceInterior',ctrim,x,top-.06,z,.62,.12,.62)
    for sg in [-1,1]:
        cpath('palaceInterior',cgold,[(x+sg*.17+.10*(1-i/30)*math.cos(i*.32),top-.20+.10*(1-i/30)*math.sin(i*.32),z+.265) for i in range(24)],.015,5)
    csolid.append({'kind':'box','position':[x,bottom+h/2,z],'size':[.58,h,.58]})
for x in [-3.15,3.15]:
    for i in [4,10]:
        z=-2.1+(i+.5)*.3; top=2.84+(i+1)*2.2/14-.24
        csupport(x,z,top)
for x in [-3.65,3.65]: csupport(x,-4.85,2.62)

# Salon panelling, ceiling coffers, crown mouldings and gilded wall mirrors.
for sx in [-1,1]:
    # Join both fireplace surrounds to the solid end wall; retain a clear bay
    # around each neighbouring window at z = +/-3.7 m.
    cbox('palaceInterior',cplaster,sx*20.3825,6.19,0,.835,11.10,2.60,True)
    for floor in [.64,5.04]:
        ceiling=4.77 if floor<1 else 10.13
        for z in [-5.73,5.73]:
            inward=1 if z<0 else -1
            for yy,hh,dd in [(floor+.14,.22,.13),(floor+1.07,.12,.18),(ceiling-.26,.24,.25),(ceiling-.08,.12,.40)]:
                cbox('palaceInterior',ctrim,sx*9.65,yy,z,9.9,hh,dd)
            cbox('palaceInterior',cgold,sx*9.65,ceiling-.39,z+inward*.12,9.9,.045,.035)
            for x in [sx*5.7,sx*8.6,sx*11.5]:
                cbox('palaceInterior',cblue,x,floor+.58,z+inward*.035,2.0,.68,.045)
                cframe('palaceInterior',cgold,x,floor+.58,z+inward*.075,2.08,.76,.021)
        for x in [sx*7.1,sx*10.8,sx*14.7,sx*18.5]:
            for z in [-3.6,0,3.6]:
                # Coffers lie horizontally, with two stepped profile strips.
                for dx in [-1.35,1.35]: cbox('palaceInterior',ctrim,x+dx,ceiling-.05,z,.13,.12,2.8)
                for dz in [-1.4,1.4]: cbox('palaceInterior',ctrim,x,ceiling-.05,z+dz,2.83,.12,.13)
                for dx in [-1.24,1.24]: cbox('palaceInterior',cgold,x+dx,ceiling-.115,z,.025,.03,2.54)
                for dz in [-1.27,1.27]: cbox('palaceInterior',cgold,x,ceiling-.115,z+dz,2.50,.03,.025)
        # Fireplace set at the pavilion end wall, with actual recessed hearth.
        x=sx*19.95
        for zz in [-.93,.93]: cbox('palaceInterior',cmarble,x,floor+.65,zz,.42,1.30,.22,True)
        cbox('palaceInterior',cmarble,x,floor+1.37,0,.64,.2,2.45,True)
        cbox('palaceInterior',cdark,x+sx*.08,floor+.63,0,.15,1.2,1.65)
        cbox('palaceInterior',cmarble,x-sx*.2,floor+.09,0,1.0,.18,2.6,True)
        # Mirror is polished metal with environment highlights, without an extra render pass.
        cbox('palaceInterior',ciron,x+sx*.18,floor+2.53,0,.04,1.75,1.8)
        for zz in [-.97,.97]: cbox('palaceInterior',cgold,x-sx*.03,floor+2.53,zz,.09,1.95,.11)
        for yy in [floor+1.56,floor+3.50]: cbox('palaceInterior',cgold,x-sx*.03,yy,0,.09,.12,2.02)
    # A pair of upholstered settees per ground-floor salon.
    for z in [-3.5,3.5]:
        x=sx*15.6
        cbox('palaceInterior',cwood,x,1.00,z,2.9,.14,.93,True)
        cbox('palaceInterior',cred,x,1.16,z,2.78,.22,.85)
        cbox('palaceInterior',cred,x,1.6,z+(.4 if z<0 else -.4),2.8,.88,.13)
        for dx in [-1.27,1.27]:
            for dz in [-.32,.32]: clathe('palaceInterior',cgold,x+dx,.64,z+dz,[(.065,0),(.05,.30),(.07,.36)],10)
            cbox('palaceInterior',cwood,x+dx,1.47,z,.10,.10,.86)
        cframe('palaceInterior',cgold,x,1.58,z+(.49 if z<0 else -.49),2.86,.92,.035)
    # Central marquetry table leaves generous circulation either side.
    clathe('palaceInterior',cwood,sx*12.4,.64,0,[(.58,0),(.58,.12),(.16,.24),(.12,.72),(.30,.81)],16)
    clathe('palaceInterior',cmarble,sx*12.4,1.45,0,[(1.0,0),(1.0,.09)],32)
    csolid.append({'kind':'box','position':[sx*12.4,1.04,0],'size':[2,.8,2]})

def cchandelier(x,y,z,r):
    cpath('palaceInterior',cgold,[(x,y,z),(x,y+.95,z)],.028,7)
    clathe('palaceInterior',cgold,x,y-.3,z,[(0,0),(.14,.12),(.22,.28),(.13,.43),(.08,.6)],14)
    for i in range(8):
        a=i*math.tau/8; dx=math.cos(a); dz=math.sin(a)
        cpath('palaceInterior',cgold,[(x,y,z),(x+dx*r*.45,y-.15,z+dz*r*.45),(x+dx*r,y+.08,z+dz*r)],.028,6)
        clathe('palaceInterior',cgold,x+dx*r,y+.08,z+dz*r,[(.12,0),(.13,.05),(.045,.1)],12)
        clathe('palaceInterior',clamp,x+dx*r,y+.18,z+dz*r,[(.035,0),(.035,.24),(0,.33)],10)
        clathe('palaceInterior',cglass,x+dx*r*.72,y-.4,z+dz*r*.72,[(0,0),(.045,.13),(0,.25)],6)
cchandelier(0,8.15,0,1.05)
for x in [-10.6,10.6]:
    for floor in [.64,5.04]: cchandelier(x,floor+2.9,0,.64)
print('Walkable marble stairs, upper gallery, panelled salons and furniture generated')
