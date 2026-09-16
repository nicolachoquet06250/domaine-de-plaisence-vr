# Ground retains the original 70 x 90 m footprint and exact top elevation.
gbox('ground','Continuous lawn',(0,6,-.30),(70,90,.6),grass,0)

# UV variants remain unit-sized: existing scene transforms and colliders stay valid.
for asset,wx,wy in [('path',1,1),('pathLong',7,54),('pathCross',45,7),('pathTerrace',45,6)]:
    obj=gbox(asset,'Compacted pale gravel',(0,0,0),(1,1,.08),gravel,0)
    uv=obj.data.uv_layers.active
    for poly in obj.data.polygons:
        for li in poly.loop_indices:
            v=obj.data.vertices[obj.data.loops[li].vertex_index].co
            uv.data[li].uv=(v.x*wx*1.6,v.y*wy*1.6)

# Courses of masonry with recessed joints, bevelled coping and moulded pilasters.
gbox('gardenBorder','Recessed mortar core',(0,0,.35),(10,.37,.70),limestone,.01)
for row in range(3):
    for i in range(14):
        left=-5+i*10/14
        gbox('gardenBorder','Limestone ashlar',(left+10/28,0,.125+row*.205),(10/14-.012,.405,.195),limestone,.008)
for i in range(10):
    gbox('gardenBorder','Weathered coping',(i-4.5,0,.77),(.99,.53,.13),limestone,.02)
for x in [-4.88,0,4.88]:
    gbox('gardenBorder','Pilaster plinth',(x,0,.065),(.68,.68,.13),limestone,.014)
    gbox('gardenBorder','Pilaster shaft',(x,0,.49),(.56,.56,.74),limestone,.012)
    gbox('gardenBorder','Capital lower moulding',(x,0,.9),(.65,.65,.09),limestone,.015)
    gbox('gardenBorder','Capital cap',(x,0,.985),(.73,.73,.08),limestone,.02)

# Fluted Medici urn, rolled rim, foot mouldings and handles, identical size envelope.
gbox('urn','Vase square pedestal',(0,0,.065),(.52,.52,.13),limestone,.015)
profile=[(0,.12),(.23,.12),(.25,.17),(.23,.21),(.15,.24),(.12,.30),(.13,.35),(.21,.4),(.28,.44),(.37,.57),(.41,.71),(.42,.75),(.46,.78),(.46,.83),(.43,.86),(.38,.82),(.36,.74),(.31,.66),(0,.66)]
glathe('urn','Fluted limestone vessel',profile,limestone,48,.012)
glathe('urn','Planting soil',[(0,.745),(.35,.745),(.35,.75),(0,.75)],soil,24)
for sign in [-1,1]:
    vv=[]; ff=[]
    for i in range(19):
        a=i*math.tau/18
        for j in range(6):
            b=j*math.tau/6; r=.13+.026*math.cos(b)
            vv.append((sign*(.40+r*math.cos(a)),.026*math.sin(b),.65+r*math.sin(a)))
    for i in range(18):
        for j in range(6):
            a=i*6+j; b=i*6+(j+1)%6; ff.append((a,b,b+6,a+6))
    gmesh('urn','Carved scroll handle',vv,ff,limestone)
ul=GLeaves(); up=GPetals()
for i in range(12):
    a=i*2.39996; r=.23*math.sqrt((i+.5)/12)
    grose(ul,up,r*math.cos(a),r*math.sin(a),.98+.07*math.sin(i*2),.9,100+i)
for i in range(36):
    a=i*2.4; r=.29+.035*math.sin(i*3)
    ul.leaf((r*math.cos(a),r*math.sin(a),.91-.18*(i%6)/6),.15,.075,a,-.6,(.70,.82,.63))
ul.finish('urn','Rose foliage and trailing leaves'); up.finish('urn','Layered rose flowers',petal_mat)
print('Created ground, scale-aware gravel, masonry and planted Medici urn.')
