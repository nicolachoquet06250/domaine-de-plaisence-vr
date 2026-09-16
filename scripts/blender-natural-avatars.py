"""Renaissance character meshes: authored contour surfaces, no mesh primitives.

Run through blender-mcp.mjs. Keeps the proven skeleton/actions and retopologized
hands; rebuilds face, mouth, hair, tailored clothes and accessories from vertices.
Coordinates used by the authoring functions are X/right, Y/up, Z/front, metres.
"""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
OUT=ROOT/'artifacts/avatars/natural'; OUT.mkdir(parents=True,exist_ok=True)
source=bpy._natural_source
scene=bpy.data.scenes.new('Cour Renaissance - modeles naturels'); bpy.context.window.scene=scene
scene.render.fps=30; scene.unit_settings.system='METRIC'
bpy._natural_scene=scene
TAU=math.tau
def clamp(x,a=0,b=1): return max(a,min(b,x))
def gauss(x,c,w): return math.exp(-((x-c)/w)**2)
def smooth(x): x=clamp(x); return x*x*(3-2*x)
def coord(p): return Vector((p[0],-p[2],p[1]))*scale
def material(name,c,r=.6,m=0):
    a=bpy.data.materials.new('Atelier - '+name); a.diffuse_color=(*c,1); a.use_nodes=True
    p=next(n for n in a.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*c,1)
    p.inputs['Roughness'].default_value=r;p.inputs['Metallic'].default_value=m
    return a
skin=material('peau nuancee',(.48,.255,.17),.53)
ps=next(n for n in skin.node_tree.nodes if n.type=='BSDF_PRINCIPLED');ps.inputs['Subsurface Weight'].default_value=.065
vc=skin.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='Complexion';skin.node_tree.links.new(vc.outputs['Color'],ps.inputs['Base Color'])
lipmat=material('levres naturelles',(.34,.105,.082),.46)
oral=material('interieur buccal',(.028,.003,.006),.86)
teeth=material('email ivoire',(.72,.67,.56),.3)
tongue=material('muqueuse',(.40,.085,.10),.55)
white=material('blanc des yeux',(.62,.59,.51),.24)
iris=material('iris ambre',(.13,.077,.023),.27)
iris2=material('fibres iris',(.28,.18,.045),.29)
pupil=material('pupille et cils',(.009,.006,.004),.34)
hair=material('chatain profond',(.039,.014,.007),.69)
hairlight=material('reflets chatains',(.060,.024,.011),.68)
red=material('velours grenat',(.16,.014,.027),.78)
blue=material('velours bleu petrole',(.015,.064,.083),.77)
gold=material('broderie or vieilli',(.53,.29,.065),.4,.67)
linen=material('lin ivoire',(.72,.65,.50),.91)
silk=material('damas champagne',(.42,.29,.13),.57)
leather=material('cuir patine',(.033,.014,.010),.46)
for mat in [red,blue]:next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Sheen Weight'].default_value=.10
POSES={'sil':(1,.0007,0,0,0,0),'PP':(.94,.0001,.0016,0,0,0),'FF':(1,.0035,-.001,.0038,0,0),
 'TH':(1,.009,0,0,.014,.015),'DD':(1,.011,0,0,.016,0),'kk':(1.03,.015,0,0,.004,-.004),
 'CH':(.81,.012,.004,0,.006,0),'SS':(1.06,.005,-.001,0,.008,0),'nn':(1,.008,0,0,.012,0),
 'RR':(.87,.011,.003,0,.009,-.001),'aa':(1.06,.025,-.001,0,-.003,0),
 'E':(1.14,.012,-.002,0,.004,0),'I':(1.16,.005,-.002,0,.007,0),
 'O':(.72,.020,.006,0,0,0),'U':(.56,.008,.010,0,.001,0)}

def mesh_obj(name,vertices,faces,mats,indices=None,bone='Head',weights=None):
    me=bpy.data.meshes.new(asset+' '+name);me.from_pydata([coord(v) for v in vertices],[],faces);me.update()
    for m in mats:me.materials.append(m)
    if indices:
        for p,i in zip(me.polygons,indices):p.material_index=i
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    for p in me.polygons:p.use_smooth=True
    obj=bpy.data.objects.new(asset+' '+name,me);scene.collection.objects.link(obj);obj.parent=rig
    groups={b.name:obj.vertex_groups.new(name=b.name) for b in rig.data.bones}
    if weights is None:groups[bone].add(list(range(len(vertices))),1,'REPLACE')
    else:
        for i,w in enumerate(weights):
            for bn,value in w.items():
                if value>0:groups[bn].add([i],value,'REPLACE')
    mod=obj.modifiers.new('Humanoid deformation','ARMATURE');mod.object=rig
    if bone in ['Head','Neck']:obj['firstPersonHidden']=True
    objects.append(obj)
    return obj

def interpolate(rows,z):
    # Cubic Hermite cross-sections with clamped endpoint slopes.
    for i in range(len(rows)-1):
        if z<=rows[i+1][0]:break
    a,b=rows[i],rows[i+1];t=clamp((z-a[0])/(b[0]-a[0]));out=[]
    for k in range(1,len(a)):
        p=rows[max(0,i-1)];q=rows[min(len(rows)-1,i+2)]
        d0=(b[k]-p[k])/(b[0]-p[0]);d1=(q[k]-a[k])/(q[0]-a[0])
        out.append((2*t**3-3*t*t+1)*a[k]+(t**3-2*t*t+t)*d0*(b[0]-a[0])+(-2*t**3+3*t*t)*b[k]+(t**3-t*t)*d1*(b[0]-a[0]))
    return out

def strip(name,points,width,mat,bone='Head',cross=5):
    # Open, flattened ribbon following an authored path, with rounded transverse profile.
    vs=[];fs=[]
    for j,p in enumerate(points):
        tang=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])
        side=Vector((tang.y,-tang.x,0));side.normalize()
        w=width*(.04+.96*math.sin(math.pi*(j+.5)/len(points))**.6)
        for k in range(cross):
            u=-1+2*k/(cross-1);v=Vector(p)+side*w*u;v.z+=width*.3*(1-u*u);vs.append(v)
    for j in range(len(points)-1):
        for k in range(cross-1):a=j*cross+k;fs.append((a,a+1,a+cross+1,a+cross))
    return mesh_obj(name,vs,fs,[mat],bone=bone)

def garment(name,rows,mat,bone='Chest',n=64,nz=28,fold=.002,center=0,frontmat=None):
    vs=[];fs=[];mi=[];ww=[]
    for j in range(nz+1):
        h=rows[0][0]+(rows[-1][0]-rows[0][0])*j/nz
        values=interpolate(rows,h);rx,rz=values[:2];cx=values[2] if len(values)>2 else center
        for i in range(n):
            a=TAU*i/n;wave=fold*(math.sin(12*a+h*5)+.34*math.sin(23*a-h*8))
            x=cx+(rx+wave)*math.sin(a);z=(rz+wave)*math.cos(a)
            vs.append((x,h,z));w={bone:1}
            if bone=='Chest':
                t=smooth((h-1.05)/.29);w={'Hips':1-t,'Chest':t}
            if bone.startswith('UpperArm'):
                side=bone.split('.')[1];t=smooth((h-1.075)/.15);w={bone:t,'Forearm.'+side:1-t}
            if bone.startswith('Thigh'):
                side=bone.split('.')[1];t=smooth((h-.50)/.14);w={bone:t,'Shin.'+side:1-t}
            ww.append(w)
    for j in range(nz):
        for i in range(n):
            a=j*n+i;fs.append((a,j*n+(i+1)%n,(j+1)*n+(i+1)%n,a+n))
            mi.append(1 if frontmat and min(i,n-i)<n*.115 else 0)
    fs.extend([tuple(reversed(range(n))),tuple(nz*n+i for i in range(n))]);mi.extend([0,0])
    return mesh_obj(name,vs,fs,[mat]+([frontmat] if frontmat else []),mi,bone,ww)

def build_face():
    global headrows, front
    # Deliberately authored anatomical sections: neck, jaw angle, chin, cheek, temple, vault.
    headrows=[(1.42,.055,.049,.048),(1.48,.045,.045,.049),(1.515,.043,.054,.055),
      (1.532,.050,.065,.061),(1.551,.062 if female else .069,.074,.069),
      (1.58,.073 if female else .078,.077,.083),(1.61,.082 if female else .085,.075,.093),
      (1.637,.083,.074,.097),(1.66,.078,.073,.098),(1.69,.080,.077,.095),
      (1.72,.076,.069,.087),(1.744,.058,.050,.064),(1.758,.030,.026,.035),(1.763,.001,.001,.001)]
    def front(x,h):
        rx,f,b=interpolate(headrows,h);u=clamp(x/rx,-1,1)
        d=f*max(0,1-u*u)**.36
        # Cheekbones, orbit recess, brow ridge, nasal bridge and alae, philtrum, chin.
        for s in [-1,1]:
            d+=.008*gauss(x,s*.047,.025)*gauss(h,1.619,.018)
            d-=.008*gauss(x,s*.034,.021)*gauss(h,1.651,.012)
            d+=.004*gauss(x,s*.033,.024)*gauss(h,1.674,.009)
            d+=.006*gauss(x,s*.011, .006)*gauss(h,1.612,.007)
            d-=.003*gauss(x,s*.025,.006)*gauss(h,1.598,.013)
        d+=(.021 if female else .027)*gauss(x,0,.010)*gauss(h,1.640,.029)
        d+=(.022 if female else .026)*gauss(x,0,.011)*gauss(h,1.617,.009)
        d-=.004*gauss(x,0,.010)*gauss(h,1.605,.004)
        d+=.0025*(gauss(x,-.003,.002)+gauss(x,.003,.002))*gauss(h,1.598,.007)
        d+=.006*gauss(x,0,.024)*gauss(h,1.552,.012)
        return d
    n=112;nz=112;vs=[];fs=[]
    for j in range(nz+1):
        h=1.42+(1.763-1.42)*j/nz;rx,f,b=interpolate(headrows,h)
        for i in range(n):
            a=TAU*i/n;x=rx*math.sin(a);c=math.cos(a)
            z=front(x,h) if c>=0 else b*c
            vs.append((x,h,z))
    for j in range(nz):
        for i in range(n):
            ids=(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i)
            mid=sum((Vector(vs[k]) for k in ids),Vector())/4
            if (mid.x/.037)**2+((mid.y-1.584)/.019)**2<1 and mid.z>.05:continue
            fs.append(ids)
    fs.extend([tuple(reversed(range(n))),tuple(nz*n+i for i in range(n))])
    # Detect the actual mouth boundary and extend the SAME surface into lip and cavity loops.
    counts={}
    for f in fs:
        for a,b in zip(f,f[1:]+f[:1]):
            e=tuple(sorted((a,b)));counts[e]=counts.get(e,0)+1
    edges=[e for e,c in counts.items() if c==1];adj={}
    for a,b in edges:adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
    if any(len(a)!=2 for a in adj.values()):raise RuntimeError('Invalid mouth edge loop')
    ordered=[next(iter(adj))];previous=None
    while True:
        cur=ordered[-1];nxt=next(v for v in adj[cur] if v!=previous)
        if nxt==ordered[0]:break
        ordered.append(nxt);previous=cur
    N=len(ordered);angles=[math.atan2((vs[k][1]-1.584)/.019,vs[k][0]/.037) for k in ordered]
    spec=[];mi=[0]*len(fs);base=len(vs)
    def add(s):spec.append(s);vs.append((0,0,0));return len(vs)-1
    def ring(kind,t,mat,prev):
        row=[add((kind,t,i)) for i in range(N)]
        for i in range(N):fs.append((prev[i],prev[(i+1)%N],row[(i+1)%N],row[i]));mi.append(mat)
        return row
    prev=ordered
    for t in [.2,.4,.6,.8,1]:prev=ring('skin',t,0,prev)
    for t in [0,.25,.5,.75,1]:prev=ring('lip',t,1,prev)
    for t in [.1,.3,.6,1]:prev=ring('cavity',t,2,prev)
    fs.append(tuple(reversed(prev)));mi.append(2)
    # Dental arches are bent continuous quad patches with incisor scalloping, not cubes.
    for lower in [False,True]:
        rows=[]
        for j in range(5):rows.append([add(('teeth',(lower,-1+2*i/32,j/4),0)) for i in range(33)])
        for j in range(4):
            for i in range(32):fs.append((rows[j][i],rows[j][i+1],rows[j+1][i+1],rows[j+1][i]));mi.append(3)
    rows=[]
    for j in range(9):rows.append([add(('tongue',(j/8,-1+2*i/12),0)) for i in range(13)])
    for j in range(8):
        for i in range(12):fs.append((rows[j][i],rows[j][i+1],rows[j+1][i+1],rows[j+1][i]));mi.append(4)
    def evaluate(s,pose):
        width,opening,protrude,tuck,tup,tout=pose;kind,p,i=s
        if kind in ['skin','lip','cavity']:
            a=angles[i];c=math.cos(a);si=math.sin(a);sh=abs(si)**.75
            w=.024 if female else .0255
            x=w*width*c;h=1.584+opening*(.30 if si>0 else -.70)*sh
            cupid=.0017*math.exp(-((abs(c)-.30)/.24)**2)-.0004*math.exp(-(c/.14)**2)
            h+=cupid*.38*sh
            d=.080+protrude-.003*abs(c)**1.7
            if si<0:h+=tuck*sh;d-=tuck*sh
            if kind=='skin':
                target=Vector((x*1.12,h+(.004 if si>0 else -.0045)*sh,d-.001))
                q=Vector(vs[ordered[i]]).lerp(target,p)
                q.z=front(q.x,q.y)*(1-smooth(p))+target.z*smooth(p)
                return q
            if kind=='lip':
                x*=1.12-.12*p;h+=(.004 if si>0 else -.0045)*sh*(1-p);d+=.0015*math.sin(math.pi*p)*sh
            else:x*=1-.26*p;h-=.003*p;d-=.044*p
        elif kind=='teeth':
            lower,u,t=p;x=.023*u;h=1.584+(-.002-opening*.65-t*.004 if lower else .004-t*.0055)
            h+=.00035*math.cos(u*math.pi*8)*math.sin(t*math.pi/2)
            d=.071-.010*u*u+.001*math.sin(t*math.pi)
        else:
            t,u=p;x=.014*u*math.sin(math.pi*(.05+t*.9));d=.032+t*.038+t**6*tout
            h=1.571-opening*.45+t*t*tup+.0025*(1-u*u)*math.sin(math.pi*t)
        return Vector((x,h,d))
    for i,s in enumerate(spec):vs[base+i]=evaluate(s,POSES['sil'])
    weights=[]
    for x,h,d in vs:
        t=smooth((h-1.48)/.046);weights.append({'Head':t,'Neck':1-t})
    face=mesh_obj('Visage Head',vs,fs,[skin,lipmat,oral,teeth,tongue],mi,weights=weights)
    colors=face.data.color_attributes.new(name='Complexion',type='FLOAT_COLOR',domain='POINT')
    for i,(x,h,d) in enumerate(vs):
        blush=sum(gauss(x,s*.047,.022)*gauss(h,1.613,.021) for s in [-1,1])*smooth(d/.065)
        c=(.53+.035*blush,.295-.020*blush,.205-.012*blush) if female else (.43+.024*blush,.225-.015*blush,.147-.007*blush)
        if not female and h<1.60 and d>.03:
            stubble=.10*smooth((1.60-h)/.025)*(1-gauss(x,0,.022)*gauss(h,1.584,.01))
            c=tuple(v*(1-stubble) for v in c)
        colors.data[i].color=(*c,1)
    face.shape_key_add(name='Basis')
    for name,pose in POSES.items():
        key=face.shape_key_add(name='viseme_'+name)
        for i,(x,h,d) in enumerate(vs[:base]):
            # The chin and perioral skin follow the jaw, avoiding a pasted-on moving mouth.
            jaw=smooth((1.588-h)/.032)*smooth((h-1.512)/.025)*smooth(d/.055)
            key.data[i].co=coord((x,h-(pose[1]-POSES['sil'][1])*.36*jaw,d-pose[1]*.10*jaw))
        for i,s in enumerate(spec):key.data[base+i].co=coord(evaluate(s,pose))
        key.value=0
    face['visemeSet']='Oculus-15';face['mouthGeometry']='continuous skin/lips/cavity; curved dental arches; tongue; distributed jaw deformation'
    # Almond eye apertures are custom patches embedded into the recessed orbital contour.
    for sg in [-1,1]:
        ex=sg*.033;ey=1.654
        def eyeedge(a):
            c=math.cos(a);s=math.sin(a)
            x=ex+.015*c;h=ey+(.0044 if s>0 else .0033)*s+sg*.001*c
            return Vector((x,h,front(x,h)+.0012))
        ev=[];ef=[];em=[];ns=64
        for j in range(7):
            r=j/6
            for i in range(ns):
                p=eyeedge(TAU*i/ns);p=Vector((ex,ey,0)).lerp(p,r);p.z=front(p.x,p.y)+.0012+.0008*(1-r*r)
                ev.append(p)
        for j in range(6):
            for i in range(ns):a=j*ns+i;ef.append((a,j*ns+(i+1)%ns,(j+1)*ns+(i+1)%ns,a+ns));em.append(0)
        mesh_obj('Oeil Head '+str(sg),ev,ef,[white])
        for upper in [True,False]:
            lv=[];lf=[]
            for j in range(5):
                t=j/4
                for i in range(33):
                    a=math.pi*i/32*(1 if upper else -1);p=eyeedge(a)
                    p.x+=(p.x-ex)*t*.16;p.y+=(.0055 if upper else -.005)*math.sin(math.pi*i/32)*t
                    p.z=p.z*(1-t)+front(p.x,p.y)*t+.0005*math.sin(math.pi*t)
                    lv.append(p)
            for j in range(4):
                for i in range(32):k=j*33+i;lf.append((k,k+1,k+34,k+33))
            lid=mesh_obj('Paupiere Head',lv,lf,[skin])
            col=lid.data.color_attributes.new(name='Complexion',type='FLOAT_COLOR',domain='POINT')
            for v in col.data:v.color=(.51,.27,.19,1) if female else (.43,.225,.147,1)
            if upper:strip('Cils Head',[eyeedge(math.pi*i/40)+Vector((0,0,.0006)) for i in range(41)],.00045,pupil)
        # Radial iris fibres clipped to the aperture; no exposed eyeball spheres.
        iv=[];ifs=[];ims=[]
        for j,r in enumerate([0,.0022,.0026,.0044,.0049]):
            for i in range(48):
                a=TAU*i/48;x=ex+r*math.cos(a);h=ey+r*math.sin(a)
                h=clamp(h,ey-.0030,ey+.0040);iv.append((x,h,front(x,h)+.0027-.0005*(r/.0049)**2))
        for j in range(4):
            for i in range(48):k=j*48+i;ifs.append((k,j*48+(i+1)%48,(j+1)*48+(i+1)%48,k+48));ims.append(0 if j==0 or j==3 else 1+i%3//2)
        mesh_obj('Iris Head',iv,ifs,[pupil,iris,iris2],ims)
        pts=[]
        for i in range(33):
            t=i/32;x=sg*(.015+.043*t);h=1.676+.004*math.sin(t*math.pi)-.003*t
            pts.append((x,h,front(x,h)+.001))
        strip('Sourcil Head',pts,.0015 if female else .0022,hair)
        # Recessed nostril crease on the nasal wing, with tapered ends.
        pts=[]
        for i in range(17):
            a=math.pi*i/16;x=sg*(.007+.005*i/16);h=1.609+.001*math.sin(a)
            pts.append((x,h,front(x,h)+.00035))
        strip('Narine Head',pts,.00065,oral)
        # Ear concha: a shaped open quad patch with helix folds, attached behind the jaw.
        ev=[];ef=[]
        for j in range(9):
            r=j/8
            for i in range(40):
                a=TAU*i/40
                ev.append((sg*(.080+.015*r*math.sin(a)+.006*math.sin(math.pi*r)),1.626+.027*r*math.cos(a),.002+.013*math.sin(math.pi*r)-.007*r*math.cos(a)))
        for j in range(8):
            for i in range(40):k=j*40+i;ef.append((k,j*40+(i+1)%40,(j+1)*40+(i+1)%40,k+40))
        ear=mesh_obj('Oreille Head',ev,ef,[skin]);c=ear.data.color_attributes.new(name='Complexion',type='FLOAT_COLOR',domain='POINT')
        for v in c.data:v.color=(.49,.245,.17,1) if female else (.42,.20,.13,1)
    return face

def build_hair():
    # Swept, broad locks lofted as sculpted ribbons, not tubular strands.
    # A continuous occipital/temporal drape gives the locks volume in profile.
    dv=[];df=[];dn=64;dk=14
    for j in range(dk+1):
        t=j/dk
        for i in range(dn+1):
            a=.86+(TAU-1.72)*i/dn
            wave=.002*math.sin(a*17+t*4)*math.sin(math.pi*t)
            rx=.090+.004*math.sin(math.pi*t)+wave
            depth=.099+.006*math.sin(math.pi*t)+wave
            h=1.678-t*(.118 if female else .145)+.003*math.sin(a*9)*t*t
            dv.append((rx*math.sin(a),h,depth*math.cos(a)))
    for j in range(dk):
        for i in range(dn):
            q=j*(dn+1)+i;df.append((q,q+1,q+dn+2,q+dn+1))
    mesh_obj('Volume coiffure Head',dv,df,[hair])
    hv=[];hf=[];n=96;k=24
    for j in range(k+1):
        t=j/k
        for i in range(n):
            a=TAU*i/n;back=(1-math.cos(a))/2
            end=1.704-.115*back**.6
            h=1.761*(1-t)+end*t;rx,f,b=interpolate(headrows,clamp(h,1.42,1.761))
            ripple=.0015*math.sin(18*a+t*7)*math.sin(math.pi*t)
            hv.append(((rx+.007+ripple)*math.sin(a),h+.005,(f+.008 if math.cos(a)>0 else b+.009)*math.cos(a)))
    for j in range(k):
        for i in range(n):q=j*n+i;hf.append((q,j*n+(i+1)%n,(j+1)*n+(i+1)%n,q+n))
    mesh_obj('Coiffure sculptee Head',hv,hf,[hair])
    for sg in [-1,1]:
        for lock in range(8):
            pts=[]
            for j in range(33):
                t=j/32
                x=sg*(.006+.087*math.sin(t*1.32));h=1.754-.092*t-lock*.0016-.003*math.sin(t*4+lock*.4)
                d=front(x,clamp(h,1.42,1.76))+.008+lock*.0009
                pts.append((x,h,d))
            strip('Meche balayee Head',pts,.0055,hair if lock%3 else hairlight,cross=7)
        for lock in range(6):
            pts=[]
            for j in range(37):
                t=j/36;x=sg*(.087+.007*math.sin(t*8+lock*.8));h=1.683-t*(.115 if female else .14)
                d=.021-lock*.018+.005*math.sin(t*9+lock)
                pts.append((x,h,d))
            strip('Ondulation laterale Head',pts,.010,hair if lock%3 else hairlight,cross=7)
    if female:
        # Broad French hood crescent, curved in depth and trimmed with stitched edging.
        vs=[];fs=[]
        for j in range(7):
            t=j/6
            for i in range(65):
                a=math.pi*i/64
                vs.append(((.103+t*.022)*math.cos(a),1.64+(.132+t*.016)*math.sin(a),-.016-t*.045))
        for j in range(6):
            for i in range(64):q=j*65+i;fs.append((q,q+1,q+66,q+65))
        mesh_obj('Coiffe francaise Head',vs,fs,[blue])
        strip('Liseret coiffe Head',[(.104*math.cos(a),1.64+.133*math.sin(a),-.012) for a in [math.pi*i/64 for i in range(65)]],.002,gold)
    else:
        # Asymmetric tailored cap, constructed from measured cloth sections.
        garment('Toque souple Head',[(1.728,.088,.080,0),(1.74,.116,.096,-.012),(1.759,.137,.102,-.021),(1.778,.122,.087,-.027),(1.79,.072,.054,-.025),(1.794,.002,.002,-.025)],red,'Head',64,16,.0014)
        strip('Bord toque Head',[(.106*math.sin(a)-.009,1.744,.090*math.cos(a)) for a in [TAU*i/80 for i in range(81)]],.0025,gold)
        # Feather is one thin vane with a curved spine and serrated outline.
        vv=[];ff=[]
        for j in range(33):
            t=j/32;x=-.087-.098*t;h=1.77+.115*t;w=.018*math.sin(math.pi*t)**.8
            for u in [-1,0,1]:vv.append((x+u*w,h+u*w*.6,.002+.012*math.sin(t*3)-abs(u)*.002))
        for j in range(32):
            for i in range(2):q=j*3+i;ff.append((q,q+1,q+4,q+3))
        mesh_obj('Plume Head',vv,ff,[linen])

def build_clothes():
    cloth=blue if female else red
    garment('Pourpoint taille',[(1.01,.139,.101),(1.06,.140,.105),(1.14,.148,.110),(1.23,.174,.118),(1.33,.206,.121),(1.40,.214,.103),(1.438,.176,.079),(1.46,.062,.052)],cloth,n=72,nz=36,fold=.0018)
    garment('Col de lin Head',[(1.438,.067,.057),(1.445,.079,.065),(1.461,.082,.067),(1.478,.064,.056),(1.484,.058,.051)],linen,'Neck',64,12,.0015)
    garment('Ceinture brodee',[(1.032,.146,.109),(1.043,.147,.110),(1.055,.145,.109)],gold,'Hips',64,5,0)
    for sg,suffix in [(1,'L'),(-1,'R')]:
        garment('Manche '+suffix,[(.89,.035,.037,sg*.32),(.95,.042,.044,sg*.316),(1.03,.046,.051,sg*.31),(1.12,.053,.058,sg*.294),(1.22,.071,.076,sg*.272),(1.31,.085,.087,sg*.248),(1.38,.079,.078,sg*.233),(1.429,.043,.048,sg*.211)],cloth,'UpperArm.'+suffix,48,38,.002)
        garment('Poignet '+suffix,[(.881,.039,.040,sg*.32),(.895,.044,.043,sg*.32),(.916,.042,.042,sg*.32)],linen,'Forearm.'+suffix,40,8,.001)
        if not female:
            garment('Haut de chausses '+suffix,[(.51,.051,.053,sg*.1),(.57,.064,.067,sg*.1),(.72,.082,.085,sg*.1),(.86,.089,.091,sg*.1),(1.027,.079,.087,sg*.089)],cloth,'Thigh.'+suffix,48,28,.003)
        garment('Bas '+suffix,[(.105,.034,.033,sg*.10),(.20,.035,.034,sg*.1),(.34,.047,.047,sg*.10),(.44,.047,.045,sg*.10),(.56,.053,.053,sg*.10)],linen,'Shin.'+suffix,40,20,.0003)
        # Soft leather shoe, transverse sections following toe, instep, heel.
        rows=[(-.073,.015,.032),(-.055,.043,.073),(0,.049,.118),(.06,.055,.094),(.14,.058,.060),(.193,.045,.043),(.209,.003,.027)]
        vv=[];ff=[];n=40;nz=32
        for j in range(nz+1):
            d=rows[0][0]+(rows[-1][0]-rows[0][0])*j/nz;w,h=interpolate(rows,d)
            for i in range(n):
                a=TAU*i/n;vv.append((sg*.1+w*math.sin(a),.003+(h-.003)*(.5+.5*math.cos(a))**.65,d))
        for j in range(nz):
            for i in range(n):q=j*n+i;ff.append((q,j*n+(i+1)%n,(j+1)*n+(i+1)%n,q+n))
        mesh_obj('Soulier '+suffix,vv,ff,[leather],bone='Foot.'+suffix)
        strip('Couture manche '+suffix,[(sg*(.32-.09*t),.94+.45*t,.047+.035*math.sin(t*math.pi)) for t in [i/48 for i in range(49)]],.0018,gold,'UpperArm.'+suffix)
    if female:
        garment('Robe plis continus',[(.065,.399,.309),(.12,.416,.324),(.30,.378,.297),(.54,.311,.251),(.77,.238,.184),(.94,.172,.126),(1.044,.140,.104)],cloth,'Hips',112,52,.0055,frontmat=silk)
        for sg in [-1,1]:
            pts=[]
            for i in range(49):
                t=i/48;h=.09+.94*t;rx,rz=interpolate([(.065,.399,.309),(.12,.416,.324),(.30,.378,.297),(.54,.311,.251),(.77,.238,.184),(.94,.172,.126),(1.044,.140,.104)],h)
                pts.append((sg*rx*.64,h,rz*.775+.003))
            strip('Galon de robe',pts,.003,gold,'Hips')
        # Repeated embroidered foliage lies on the front damask panel.
        for row in range(8):
            h=.19+row*.098;dep=.337-(h-.10)*.252
            for sg in [-1,1]:
                pts=[(sg*.019*math.sin(math.pi*t),h+.037*t,dep-.009*t) for t in [i/16 for i in range(17)]]
                strip('Feuille brodee',pts,.0016,gold,'Hips')
    else:
        garment('Basques pourpoint',[(.95,.159,.112),(1.00,.154,.113),(1.046,.145,.107)],cloth,'Hips',64,10,.001)
        for sg in [-1,1]:
            strip('Passementerie pourpoint',[(sg*.032,1.075+.31*t,.112+.010*math.sin(t*math.pi)) for t in [i/40 for i in range(41)]],.002,gold,'Chest')
    # Gold collar ribbon follows the torso; flat metal links are authored quad bands.
    pts=[(.144*math.cos(a),1.426-.151*math.sin(a),.098+.039*math.sin(a)) for a in [math.pi*i/64 for i in range(65)]]
    strip('Chaine de cour',pts,.004,gold,'Chest')
    vv=[];ff=[]
    for j,r in enumerate([0,.013,.019,.021]):
        for i in range(40):a=TAU*i/40;vv.append((r*math.cos(a),1.263+r*1.3*math.sin(a),.148+.004*math.sin(j*math.pi/3)))
    for j in range(3):
        for i in range(40):q=j*40+i;ff.append((q,j*40+(i+1)%40,(j+1)*40+(i+1)%40,q+40))
    mesh_obj('Medaille',vv,ff,[gold],bone='Chest')

reports={}; models={}
for asset,female,scale in [('courtMale',False,1),('courtFemale',True,.95)]:
    oldrig=next(o for o in source.objects if o.type=='ARMATURE' and o.name.startswith(asset))
    rig=oldrig.copy();rig.data=oldrig.data.copy();rig.name=asset+' Natural Rig';scene.collection.objects.link(rig);rig.location=(0,0,0)
    objects=[]
    # Reuse the existing organic, welded hand topology and established XR grip metadata.
    for old in source.objects:
        if old.parent!=oldrig or 'Head' in old.name or not (' Peau.' in old.name or ' Ongles' in old.name):continue
        obj=old.copy();obj.data=old.data.copy();obj.parent=rig;obj.name=asset+' '+('Mains' if ' Peau.' in old.name else 'Ongles');scene.collection.objects.link(obj)
        for mod in obj.modifiers:
            if mod.type=='ARMATURE':mod.object=rig
        if 'Mains' in obj.name:
            obj.data.materials.clear();obj.data.materials.append(skin)
            c=obj.data.color_attributes.new(name='Complexion',type='FLOAT_COLOR',domain='POINT')
            for v in c.data:v.color=(.53,.295,.205,1) if female else (.43,.225,.147,1)
        objects.append(obj)
    face=build_face();build_hair();build_clothes()
    models[asset]={'rig':rig,'objects':objects,'face':face}
    reports[asset]={'vertices':sum(len(o.data.vertices) for o in objects),'objects':len(objects),'visemes':list(POSES),'method':'custom anatomical contour meshes, quad patches and tailored lofts; no primitive operators; existing retopologized hands and rig reused'}
    rig.location.x=-.49 if not female else .49
bpy._natural_models=models
scene.frame_start=0;scene.frame_end=90;scene.frame_set(0)
bpy.data.libraries.write(str(OUT/'renaissance-natural-work.blend'),{scene},fake_user=True,compress=True)
(OUT/'construction.json').write_text(json.dumps(reports,indent=2))
print(json.dumps(reports))
