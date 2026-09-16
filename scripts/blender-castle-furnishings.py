"""Room furniture, generated in Blender and merged by shared PBR material."""
A='palaceInterior'
clinen=cmat('Lin ivoire',(.83,.79,.68),.94)
cceramic=cmat('Porcelaine emaillee',(.91,.92,.86),.18)
cmirror=cmat('Argent poli des miroirs',(.82,.86,.88),.07,.98)
cfurnishings=[]

def cellipsoid(mat,x,y,z,rx,ry,rz,n=12,rings=6):
    vv=[]; ff=[]
    for j in range(rings+1):
        p=math.pi*j/rings
        for i in range(n):
            a=math.tau*i/n; vv.append((x+rx*math.sin(p)*math.cos(a),y+ry*math.cos(p),z+rz*math.sin(p)*math.sin(a)))
    for j in range(rings):
        for i in range(n):
            k=j*n+i; q=j*n+(i+1)%n; ff.append((k,q,q+n,k+n))
    cadd(A,mat,vv,ff,True)

def csoftbox(mat,x,y,z,w,h,d,r=.06):
    # Rounded rectangular footprint, bevelled top/bottom, 16 segments per ring.
    r=min(r,w*.4,h*.4,d*.4)
    vv=[]; ff=[]
    for yy,inset in [(y-h/2,r*.45),(y-h/2+r*.4,0),(y+h/2-r*.4,0),(y+h/2,r*.45)]:
        for sx,sz,angle in [(1,1,0),(-1,1,math.pi/2),(-1,-1,math.pi),(1,-1,3*math.pi/2)]:
            for j in range(4):
                a=angle+j*math.pi/6
                vv.append((x+sx*(w/2-r)+(r-inset)*math.cos(a),yy,z+sz*(d/2-r)+(r-inset)*math.sin(a)))
    for j in range(3):
        for i in range(16): ff.append((j*16+i,j*16+(i+1)%16,(j+1)*16+(i+1)%16,(j+1)*16+i))
    ff.extend([tuple(reversed(range(16))),tuple(range(48,64))]); cadd(A,mat,vv,ff,True)

def cscroll(x,y,z,s=.3):
    for sg in [-1,1]:
        cpath(A,cgold,[(x+sg*(s*.4+s*.52*(1-i/27)*math.cos(i*.36)),y+s*.46*(1-i/27)*math.sin(i*.36),z) for i in range(20)],.016,5)
    # Acanthus leaf relief, central rosette and paired petals.
    for sg in [-1,1]:
        for i in range(3):
            xx=x+sg*(.07+i*.07)*s/.3
            cextrude(A,cgold,[(xx,y),(xx+sg*.05,y+.12),(xx+sg*.11,y+.10),(xx+sg*.08,y-.015)],z,.025)
    cellipsoid(cgold,x,y+.04,z,.045,.065,.025,10,5)

def cleg(x,y,z,h=.45):
    clathe(A,cwood,x,y,z,[(.065,0),(.08,.04),(.042,.12),(.055,h-.09),(.085,h)],12)
    clathe(A,cgold,x,y+.025,z,[(.08,0),(.08,.035)],12)

def cknob(x,y,z):
    cellipsoid(cgold,x,y,z,.043,.043,.045,10,5)

def cbed(x,y,z,blue=False):
    fabric=cblue if blue else cred
    for dx in [-1.02,1.02]:
        for dz in [-1.38,1.38]: cleg(x+dx,y,z+dz,.44)
    csoftbox(cwood,x,y+.45,z,2.4,.22,3.25)
    csoftbox(clinen,x,y+.68,z,2.24,.31,3.08,.13)
    csoftbox(fabric,x,y+.855,z+.30,2.27,.09,2.30,.09)
    # Piping and folded cover keep their own surface, no coplanar overlays.
    csoftbox(clinen,x,y+.925,z-.69,2.24,.07,.35,.04)
    for dx in [-.55,.55]:
        cellipsoid(clinen,x+dx,y+.96,z-1.03,.49,.17,.35)
    for zz,hh in [(z-1.60,1.95),(z+1.60,1.02)]:
        csoftbox(cwood,x,y+hh/2+.23,zz,2.52,hh,.15)
        csoftbox(fabric,x,y+hh/2+.28,zz+.095,2.22,hh-.26,.10)
        cframe(A,cgold,x,y+hh/2+.28,zz+.16,2.28,hh-.20,.038)
        cscroll(x,y+hh+.16,zz+.14,.60)
        for dx in [-1.21,1.21]:
            clathe(A,cwood,x+dx,y,zz,[(.085,0),(.085,hh+.24),(.12,hh+.30),(.045,hh+.44)],12)
            cellipsoid(cgold,x+dx,y+hh+.47,zz,.075,.10,.075,12,6)
    # Upholstery buttons.
    for dx in [-.73,0,.73]:
        for yy in [1.08,1.52]: cknob(x+dx,y+yy,z-1.425)
    csolid.append({'kind':'box','position':[x,y+.60,z],'size':[2.52,1.2,3.4]})
    cfurnishings.append({'type':'bed','position':[x,y,z]})

def ccabinet(x,y,z,w=1.02,h=.78,d=.64,drawers=2):
    for dx in [-w*.39,w*.39]:
        for dz in [-d*.35,d*.35]: cleg(x+dx,y,z+dz,.20)
    csoftbox(cwood,x,y+.19+h*.45,z,w,h*.90,d)
    csoftbox(cmarble,x,y+h+.22,z,w+.10,.095,d+.10,.045)
    for i in range(drawers):
        yy=y+.28+(i+.5)*(h-.10)/drawers; hh=(h-.10)/drawers-.035
        csoftbox(cwood,x,yy,z+d/2+.02,w-.13,hh,.055,.025)
        cframe(A,cgold,x,yy,z+d/2+.055,w-.20,hh-.04,.012)
        for dx in [-w*.23,w*.23]:
            cpath(A,cgold,[(x+dx+.055*math.cos(j*math.tau/12),yy+.04*math.sin(j*math.tau/12),z+d/2+.10) for j in range(12)],.011,5,True)
    cscroll(x,y+h+.11,z+d/2+.07,min(.30,w*.20))
    csolid.append({'kind':'box','position':[x,y+(h+.25)/2,z],'size':[w,h+.25,d]})

def clampstand(x,y,z):
    clathe(A,cgold,x,y,z,[(.15,0),(.15,.045),(.055,.10),(.045,.30),(.09,.36)],12)
    clathe(A,clinen,x,y+.33,z,[(.24,0),(.15,.29)],16)
    clathe(A,cgold,x,y+.33,z,[(.245,0),(.245,.025)],16)

def cbowl(x,y,z,rx,rz,h,mat=cceramic):
    # Continuous outer shell, thick rim, inner wall and closed recessed bottom.
    profile=[(.15,.00),(.64,.04),(.83,h*.32),(1,h*.86),(1,h),(.89,h+.01),(.83,h*.84),(.68,h*.26),(.35,.13),(0,.13)]
    vv=[]; ff=[]; n=32; k=len(profile)
    for i in range(n):
        a=math.tau*i/n
        for r,yy in profile: vv.append((x+rx*r*math.cos(a),y+yy,z+rz*r*math.sin(a)))
    for i in range(n):
        for j in range(k-1): ff.append((i*k+j,((i+1)%n)*k+j,((i+1)%n)*k+j+1,i*k+j+1))
    ff.append(tuple(reversed([i*k for i in range(n)]))); cadd(A,mat,vv,ff,True)

def cfaucet(x,y,z,large=False):
    h=.36 if large else .20
    cpath(A,cgold,[(x,y,z),(x,y+h*.8,z),(x,y+h,z+.06),(x,y+h,z+.20),(x,y+h-.07,z+.23)],.025,8)
    for dx in [-.17,.17]:
        clathe(A,cgold,x+dx,y,z,[(.055,0),(.035,.09)],12)
        cpath(A,cgold,[(x+dx-.06,y+.095,z),(x+dx+.06,y+.095,z)],.018,6)
        cpath(A,cgold,[(x+dx,y+.095,z-.06),(x+dx,y+.095,z+.06)],.018,6)

def cbath(x,y,z):
    for dx in [-.43,.43]:
        for dz in [-.77,.77]:
            # Cast bronze lion-paw feet with individual toes.
            cellipsoid(cgold,x+dx,y+.266,z+dz,.11,.238,.13,12,6)
            for toe in [-1,0,1]: cellipsoid(cgold,x+dx+toe*.043,y+.084,z+dz+.08,.035,.077,.075,8,4)
    cbowl(x,y+.23,z,.72,1.32,.65)
    cpath(A,cgold,[(x+.73*math.cos(i*math.tau/40),y+.80,z+1.33*math.sin(i*math.tau/40)) for i in range(40)],.024,6,True)
    cfaucet(x,y+.89,z-1.17,True)
    cscroll(x,y+.62,z+1.255,.36)
    csolid.append({'kind':'box','position':[x,y+.48,z],'size':[1.46,.96,2.70]})
    cfurnishings.append({'type':'bathtub','position':[x,y,z]})

def ctoilet(x,y,z):
    clathe(A,cceramic,x,y,z,[(.24,0),(.25,.06),(.16,.17),(.20,.34)],20)
    cbowl(x,y+.23,z,.32,.42,.23)
    # Open seat ring, with the bowl visible through it.
    cpath(A,clinen,[(x+.29*math.cos(i*math.tau/28),y+.505,z+.385*math.sin(i*math.tau/28)) for i in range(28)],.045,8,True)
    csoftbox(cceramic,x,y+.68,z-.49,.63,.58,.23,.07)
    csoftbox(cceramic,x,y+.995,z-.49,.67,.08,.27,.04)
    cknob(x+.23,y+.84,z-.35)
    cframe(A,cgold,x,y+.72,z-.365,.48,.34,.012)
    csolid.append({'kind':'box','position':[x,y+.53,z-.08],'size':[.70,1.06,1.1]})
    cfurnishings.append({'type':'toilet','position':[x,y,z]})

def cbust(x,y,z):
    clathe(A,cmarble,x,y,z,[(.34,0),(.34,.10),(.24,.19),(.23,.92),(.32,1.02),(.34,1.10)],16,.04)
    for yy in [.12,1.02]: clathe(A,cgold,x,y+yy,z,[(.33,0),(.33,.025)],16)
    if y>5:
        # Historical portrait busts are separate editable manifest assets.
        csolid.append({'kind':'box','position':[x,y+.55,z],'size':[.68,1.10,.68]})
        return
    cellipsoid(ctrim,x,y+1.34,z,.33,.25,.18)
    clathe(A,ctrim,x,y+1.42,z,[(.095,0),(.08,.17)],12)
    cellipsoid(ctrim,x,y+1.78,z,.16,.23,.17,16,10)
    cellipsoid(ctrim,x,y+1.76,z+.164,.035,.07,.06,10,6)
    for sg in [-1,1]:
        cellipsoid(ctrim,x+sg*.158,y+1.79,z,.036,.068,.027,10,6)
        cpath(A,cdark,[(x+sg*.042,y+1.83,z+.154),(x+sg*.10,y+1.83,z+.14)],.009,5)
    for i in range(11):
        a=math.pi*i/10
        cellipsoid(ctrim,x+.151*math.cos(a),y+1.89+.08*math.sin(a),z-.015,.055,.061,.13,10,5)
    for i in range(5):
        cpath(A,ctrim,[(x-.25+i*.09,y+1.42,z+.12),(x-.16+i*.065,y+1.18,z+.17)],.025,5)
    csolid.append({'kind':'box','position':[x,y+.55,z],'size':[.68,1.10,.68]})

for sg in [-1,1]:
    y=5.04; x=sg*10.0; z=-2.85
    cbed(x,y,z,sg>0)
    for dx in [-1.95,1.95]:
        ccabinet(x+dx,y,z-1.0)
        clampstand(x+dx,y+1.05,z-1.0)
        cfurnishings.append({'type':'nightstand','position':[x+dx,y,z-1.0]})
    # Matching chest and a carved oval mirror, facing the circulation aisle.
    ccabinet(sg*7.0,y,-4.95,1.60,1.10,.65,3)
    cellipsoid(cmirror,sg*7.0,y+2.03,-5.19,.51,.68,.023,24,12)
    cpath(A,cgold,[(sg*7.0+.56*math.cos(i*math.tau/36),y+2.03+.74*math.sin(i*math.tau/36),-5.14) for i in range(36)],.045,7,True)
    cscroll(sg*7.0,y+2.81,-5.12,.42)
    # Wardrobe at the rear of the pavilion, away from windows and door swings.
    wx=sg*15.6
    csoftbox(cwood,wx,y+1.29,-5.18,1.8,2.58,.74)
    for dx in [-.44,.44]:
        cframe(A,cgold,wx+dx,y+1.31,-4.795,.77,2.28,.025)
        cknob(wx+dx*.20,y+1.29,-4.745)
    csoftbox(ctrim,wx,y+2.62,-5.18,1.98,.14,.88)
    cscroll(wx,y+2.78,-4.77,.62)
    csolid.append({'kind':'box','position':[wx,y+1.38,-5.18],'size':[1.98,2.76,.88]})
    # Bathroom partition with a generous open doorway at the front.
    px=sg*14.4
    cbox(A,cplaster,px,y+1.65,-1.6,.16,3.30,7.65,True)
    for zz in [-5.425,2.225]:
        cbox(A,ctrim,px,y+1.68,zz,.28,3.36,.13)
    for yy in [y+.15,y+3.22]: cbox(A,ctrim,px,yy,-1.6,.25,.16,7.65)
    for side in [-1,1]:
        for zz in [-4.35,-2.15,.05]:
            xx=px+side*.105
            cbox(A,cblue,xx,y+1.79,zz,.025,2.08,1.66)
            for dz in [-.88,.88]: cbox(A,cgold,xx+side*.03,y+1.79,zz+dz,.03,2.2,.04)
            for yy in [y+.69,y+2.89]: cbox(A,cgold,xx+side*.03,yy,zz,.03,.04,1.8)
    cbath(sg*17.8,y,-3.55)
    ctoilet(sg*19.55,y,3.2)
    vanity_start={key:len(batch['v']) for key,batch in cbatches.items()}
    ccabinet(sg*17.2,y,4.60,1.35,.65,.76,2)
    cbowl(sg*17.2,y+.94,4.60,.50,.32,.17)
    cfaucet(sg*17.2,y+1.1,4.32)
    # Drawer fronts and taps face the room, with the supply against the wall.
    for key,batch in cbatches.items():
        for i in range(vanity_start.get(key,0),len(batch['v'])):
            vx,vy,vz=batch['v'][i]; batch['v'][i]=(2*sg*17.2-vx,vy,9.2-vz)
    # Freestanding towel stand and neatly folded linen.
    for dx in [-.42,.42]:
        clathe(A,cgold,sg*16.1+dx,y,-2.6,[(.15,0),(.15,.06),(.025,.10),(.025,1.16)],12)
    cpath(A,cgold,[(sg*16.1-.42,y+1.16,-2.6),(sg*16.1+.42,y+1.16,-2.6)],.03,6)
    csoftbox(clinen,sg*16.1,y+.96,-2.56,.52,.39,.10,.03)
    # Ground-floor writing bureau, upholstered stool and classical sculpture.
    gx=sg*8.3
    ccabinet(gx,.64,-3.5,1.75,.66,.82,2)
    for dx in [-.28,.28]:
        for dz in [-.24,.24]: cleg(gx+dx,.64,-2.3+dz,.43)
    csoftbox(cblue,gx,1.13,-2.3,.70,.14,.63)
    csolid.append({'kind':'box','position':[gx,.94,-2.3],'size':[.70,.60,.63]})
    cbust(sg*6.1,.64,-4.25)
    cbust(sg*12.8,5.04,1.0)

(CEVID/'furnishings.json').write_text(json.dumps(cfurnishings,indent=2))
print('Two furnished bedrooms and bathrooms; carved furniture, porcelain fixtures and classical busts generated')
