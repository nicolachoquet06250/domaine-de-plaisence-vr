"""Authored portrait sculptures and skinned Valois court costumes. Y-up input metres."""
import bpy, math, json, bmesh
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
RFROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
RFOUT=RFROOT/'public/gltf/avatars'; RFOUT.mkdir(parents=True,exist_ok=True)
RFBUST=RFROOT/'public/gltf/castle'; RFEVID=RFROOT/'artifacts/avatars'; RFEVID.mkdir(parents=True,exist_ok=True)
rfscene=bpy.data.scenes.new('Portraits royaux et cour Renaissance'); bpy.context.window.scene=rfscene
rfscene.render.fps=30; rfscene.unit_settings.system='METRIC'
rfbatch={}; rfmodels={}; rfstats={}; rfbone='Head'
def rfmat(name,col,rough=.65,metal=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*col,1); m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'); p.inputs['Base Color'].default_value=(*col,1)
    p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    return m
skin=rfmat('Peau',(.56,.31,.20),.70); lips=rfmat('Levres',(.35,.115,.085),.66)
nails=rfmat('Ongles naturels satines',(.60,.37,.28),.42)
hair=rfmat('Cheveux chatains',(.055,.026,.013),.78); eye=rfmat('Sclerotique',(.77,.73,.63),.34)
iris=rfmat('Iris noisette',(.12,.065,.025),.38); pupil=rfmat('Pupille',(.009,.008,.006),.32)
gold=rfmat('Or brode et bijoux',(.66,.39,.085),.32,.78); linen=rfmat('Lin et perles',(.85,.81,.69),.87)
velvet=rfmat('Velours cramoisi',(.23,.025,.038),.87); blue=rfmat('Velours bleu nuit',(.025,.075,.115),.86)
leather=rfmat('Souliers cuir brun',(.055,.025,.018),.60); silk=rfmat('Soie champagne',(.61,.45,.23),.62)
stone=rfmat('Marbre statuaire ivoire',(.76,.74,.68),.54); cavity=rfmat('Creux sculptes',(.60,.58,.53),.77)

def rfadd(asset,mat,v,f,bone=None):
    part=' Head' if asset.startswith('court') and (bone or rfbone) in ['Head','Neck'] else ''
    b=rfbatch.setdefault((asset,mat.name+part),{'v':[],'f':[],'w':[],'mat':mat,'head':bool(part)}); start=len(b['v'])
    b['v'].extend(v); b['f'].extend(tuple(start+i for i in face) for face in f)
    b['w'].extend([bone or rfbone]*len(v))

def rfsphere(a,m,x,y,z,rx,ry,rz,n=18,k=12,bone=None):
    v=[]; f=[]
    for j in range(k+1):
        p=math.pi*j/k
        for i in range(n):
            t=math.tau*i/n; v.append((x+rx*math.sin(p)*math.cos(t),y+ry*math.cos(p),z+rz*math.sin(p)*math.sin(t)))
    for j in range(k):
        for i in range(n): f.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    rfadd(a,m,v,f,bone)

def rfloft(a,m,x,z,rings,n=24,bone=None,pleat=0):
    v=[]; f=[]
    for ring in rings:
        y,rx,rz=ring[:3]; cx=ring[3] if len(ring)>3 else x
        for i in range(n):
            t=math.tau*i/n; wave=1+pleat*math.cos(12*t)
            v.append((cx+rx*math.cos(t)*wave,y,z+rz*math.sin(t)*wave))
    for j in range(len(rings)-1):
        for i in range(n): f.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    f.extend([tuple(reversed(range(n))),tuple((len(rings)-1)*n+i for i in range(n))]); rfadd(a,m,v,f,bone)

def rftube(a,m,points,r=.008,n=7,bone=None):
    v=[];f=[]
    for i,p in enumerate(points):
        tangent=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])).normalized()
        axis=tangent.cross(Vector((0,0,1)))
        if axis.length<.001: axis=tangent.cross(Vector((0,1,0)))
        axis.normalize(); oth=tangent.cross(axis)
        for j in range(n): v.append(tuple(Vector(p)+r*(axis*math.cos(j*math.tau/n)+oth*math.sin(j*math.tau/n))))
    for i in range(len(points)-1):
        for j in range(n): f.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
    f.extend([tuple(reversed(range(n))),tuple((len(points)-1)*n+j for j in range(n))]); rfadd(a,m,v,f,bone)

def rfhand(asset,sg,suffix,rig,factor):
    """Continuous remeshed anatomy. u=thumbward, v=fingers, w=dorsal.

    Mirrored palms face the body; fingers are model -Y, thumbs model +Z.
    Dimensions are metres; all five digits join the palm before decimation.
    """
    bone='Hand.'+suffix; temp=asset+'_hand_'+suffix; hand_scale=1.18
    def xyz(p):
        u,v,w=p; return (sg*(.32+w*hand_scale),.89-v*hand_scale,.018+u*hand_scale)
    def surface(rings,n=20,material=skin,target=temp):
        vv=[];ff=[]
        for center,across,dorsal,ru,rw in rings:
            for i in range(n):
                t=math.tau*i/n
                vv.append(xyz(Vector(center)+Vector(across)*(ru*math.cos(t))+Vector(dorsal)*(rw*math.sin(t))))
        for j in range(len(rings)-1):
            for i in range(n):ff.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
        ff.extend([tuple(reversed(range(n))),tuple((len(rings)-1)*n+i for i in range(n))])
        rfadd(target,material,vv,ff,bone)
    surface([((-.002,v,0),(1,0,0),(0,0,1),ru,rw) for v,ru,rw in [(-.02,.020,.014),(0,.023,.015),(.024,.029,.018),(.05,.037,.017),(.075,.036,.014),(.085,.031,.010),(.09,.025,.003)]],32)
    # Thenar pad merges the opposed thumb into the palm instead of a glued tube.
    p=xyz((.019,.040,-.006));rfsphere(temp,skin,*p,.017*hand_scale,.030*hand_scale,.023*hand_scale,24,16,bone)
    landmarks={}
    def digit(name,path,radius):
        rings=[]
        for j in range(21):
            t=j/20;center=Vector(path(t));tangent=Vector(path(min(1,t+.001)))-Vector(path(max(0,t-.001)));tangent.normalize()
            across=Vector((1,0,0)) if name!='thumb' else Vector((tangent.y,-tangent.x,0)).normalized()
            dorsal=across.cross(tangent).normalized()
            taper=(1-.25*t)*(1 if t<.84 else math.sqrt(max(.001,1-((t-.84)/.16)**2)))
            bulge=1+.055*math.exp(-((t-.38)/.085)**2)+.035*math.exp(-((t-.68)/.07)**2)
            rings.append((center,across,dorsal,radius*taper*bulge,radius*.80*taper*bulge))
        surface(rings,16)
        # A thin curved nail, rounded free edge, sitting on the dorsal fingertip.
        t=.80;center=Vector(path(t));tangent=(Vector(path(t+.001))-Vector(path(t-.001))).normalized()
        across=Vector((1,0,0)) if name!='thumb' else Vector((tangent.y,-tangent.x,0)).normalized()
        dorsal=across.cross(tangent).normalized(); center+=dorsal*(radius*.8*(1-.25*t)-.0005)
        nv=[xyz(center)];nf=[];n=24
        for j in range(1,7):
            for i in range(n):
                angle=math.tau*i/n;rho=j/6
                nv.append(xyz(center+across*(radius*.49*rho*math.cos(angle))+tangent*((.010 if name!='pinky' else .007)*rho*math.sin(angle))))
        for i in range(n):nf.append((0,1+i,1+(i+1)%n))
        for j in range(5):
            for i in range(n):a=1+j*n+i;b=1+j*n+(i+1)%n;nf.append((a,b,b+n,a+n))
        rfadd(asset,nails,nv,nf,bone)
        landmarks[name+'Tip']=[c*factor for c in xyz(path(1))]
    specs=[('index',.024,.076,.071,.0085),('middle',.005,.082,.082,.009),('ring',-.015,.079,.077,.008),('pinky',-.033,.071,.059,.0065)]
    for name,u,base,length,radius in specs:
        digit(name,lambda t,u=u,base=base,length=length:(u+u*.10*t,base+length*t,-.001-.020*t*t),radius)
    digit('thumb',lambda t:(.020+.055*math.sin(t*1.1),.033+.060*t,-.008-.009*t),.014)
    # Fuse intersections, round the webbing and retain a strict close-view budget.
    key=next(key for key in rfbatch if key[0]==temp);batch=rfbatch.pop(key)
    mesh=bpy.data.meshes.new(temp);mesh.from_pydata(batch['v'],[],batch['f']);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    obj=bpy.data.objects.new(temp,mesh);rfscene.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    remesh=obj.modifiers.new('Continuous palm and finger webs','REMESH');remesh.mode='VOXEL';remesh.voxel_size=.0017;remesh.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=remesh.name)
    smooth=obj.modifiers.new('Soften anatomy','SMOOTH');smooth.factor=.35;smooth.iterations=3;bpy.ops.object.modifier_apply(modifier=smooth.name)
    obj.data.calc_loop_triangles();dec=obj.modifiers.new('VR hand budget','DECIMATE');dec.ratio=min(1,3500/len(obj.data.loop_triangles));bpy.ops.object.modifier_apply(modifier=dec.name)
    # Conform the nail surface to the final skin, avoiding clipping and thick discs.
    tree=BVHTree.FromPolygons([v.co for v in obj.data.vertices],[p.vertices for p in obj.data.polygons])
    nb=rfbatch[(asset,nails.name)]
    for i,weight in enumerate(nb['w']):
        if weight!=bone:continue
        point=Vector(nb['v'][i]);hit,normal,_,_=tree.ray_cast(point+Vector((sg*.05,0,0)),Vector((-sg,0,0)),.10)
        if hit is not None:nb['v'][i]=tuple(hit+normal*.00035)
    rfadd(asset,skin,[tuple(v.co) for v in obj.data.vertices],[tuple(p.vertices) for p in obj.data.polygons],bone)
    owned_mesh=obj.data;bpy.data.objects.remove(obj,do_unlink=True);bpy.data.meshes.remove(owned_mesh)
    landmarks['wrist']=[c*factor for c in xyz((0,0,0))]
    landmarks['dorsalKnuckle']=[c*factor for c in xyz((.005,.082,.012))]
    landmarks['indexKnuckle']=[c*factor for c in xyz((.024,.076,0))]
    rig.data.bones[bone]['handAnatomy']=landmarks
    rig.data.bones[bone]['xrGrip']={'modelToGripQuaternion':[0.0,1.0,0.0,0.0],
        'wristToGripModel':[-sg*.009*hand_scale*factor,-.055*hand_scale*factor,0.0],
        'uniformHandScale':hand_scale}

def rfhead(a,x,y,z,s=1,portrait=None,marble=False):
    """One continuous face with orbital depressions, cheekbones, bridge and nasal tip."""
    mat=stone if marble else skin; detail=stone if marble else hair; n=48;k=32; v=[];f=[]
    lady=portrait=='courtLady'
    nose=.95 if portrait=='francois' else .32 if lady else .65
    for j in range(k+1):
        p=math.pi*j/k; yy=math.cos(p); width=(.90+.10*max(0,yy))*(1-(.28 if lady else .13)*max(0,-yy))
        for i in range(n):
            t=math.tau*i/n; xx=math.sin(p)*math.cos(t)*width; zz=math.sin(p)*math.sin(t)
            if zz>0:
                front=min(1,zz*3)
                bridge=.021*math.exp(-(xx/.17)**2-((yy-.03)/.43)**2)
                tip=.029*math.exp(-(xx/.20)**2-((yy+.17)/.13)**2)
                sockets=sum(-.010*math.exp(-((xx-sg*.39)/.22)**2-((yy-.19)/.17)**2) for sg in [-1,1])
                cheeks=sum((.012 if lady else .008)*math.exp(-((xx-sg*.53)/.24)**2-((yy+.13)/.25)**2) for sg in [-1,1])
                chin=.007*math.exp(-(xx/.40)**2-((yy+.76)/.15)**2)
                depth=.084*zz+front*(nose*(bridge+tip)+sockets+cheeks+chin)
            else: depth=.094*zz
            v.append((x+(.087 if lady else .091)*s*xx,y+(.126 if lady else .132)*s*yy,z+s*depth))
    for j in range(k):
        for i in range(n):f.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    rfadd(a,mat,v,f)
    for sg in [-1,1]:
        rfsphere(a,mat,x+sg*.085*s,y-.009*s,z,.015*s,.028*s,.018*s,18,12)
        rftube(a,mat,[(x+sg*(.086+.008*math.sin(t*math.pi))*s,y+(.018-.05*t)*s,z+.013*s) for t in [i/12 for i in range(13)]],.003*s,6)
        ex=x+sg*.035*s; ey=y+.024*s; ez=z+.071*s
        rfsphere(a,stone if marble else eye,ex,ey,ez,.019*s,.007*s,.006*s,24,14)
        rfsphere(a,cavity if marble else iris,ex,ey,ez+.0082*s,.006*s,.006*s,.0018*s,16,10)
        if not marble:rfsphere(a,pupil,ex,ey,ez+.010*s,.0027*s,.0027*s,.001*s,12,8)
        for upper in [-1,1]:
            rftube(a,mat,[(ex+.0195*s*math.cos(i*math.pi/16),ey+upper*.0065*s*math.sin(i*math.pi/16),ez+.004*s) for i in range(17)],.0017*s,8)
        rftube(a,detail,[(ex+u*(.021 if lady else .024)*s,y+(.045+(.008 if lady else .004)*math.sin((u+1)*math.pi/2))*s,z+.071*s) for u in [-1,-.5,0,.5,1]],(.0014 if lady else .002)*s,8)
        rfsphere(a,cavity if marble else lips,x+sg*(.007 if lady else .010)*s,y-.029*s,z+(.091 if lady else .102)*s,.003*s,.0015*s,.001*s,10,6)
    for sign in [-1,1]:
        rftube(a,stone if marble else lips,[(x+u*(.023 if lady else .027)*s,y+(-.052+sign*(.004 if lady else .003)*math.sin((u+1)*math.pi/2)+.0018*math.cos(u*math.pi*2))*s,z+(.082-.006*abs(u))*s) for u in [-1,-.75,-.5,-.25,0,.25,.5,.75,1]],(.0033 if lady else .0028)*s,6)
    rftube(a,cavity if marble else lips,[(x+u*.022*s,y-.052*s,z+(.084-.006*abs(u))*s) for u in [-1,-.5,0,.5,1]],.001*s,5)

def rfhair(a,x,y,z,s=1,long=False,marble=False,lady=False):
    m=stone if marble else hair
    # Continuous scalp cap: crown, temples AND occiput, with a front hairline.
    v=[];f=[];n=48;k=18
    for j in range(k+1):
        for i in range(n):
            phi=math.tau*i/n; back=(1-math.cos(phi))/2
            end=.82+1.82*(back**.55);p=(j/k)*end
            ripple=1+.018*math.sin(phi*24+p*4)
            v.append((x+s*.097*math.sin(p)*math.sin(phi)*ripple,y+s*.140*math.cos(p),z+s*.104*math.sin(p)*math.cos(phi)*ripple))
    for j in range(k):
        for i in range(n):f.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    rfadd(a,m,v,f)
    # Grooves flow over the back, never leave exposed scalp between separate tubes.
    for i in range(32):
        phi=math.tau*(i+.5)/32;back=(1-math.cos(phi))/2;end=.82+1.82*(back**.55)
        pts=[]
        for j in range(16):
            p=.16+(end-.16)*j/15
            pts.append((x+s*.099*math.sin(p)*math.sin(phi),y+s*.142*math.cos(p),z+s*.106*math.sin(p)*math.cos(phi)))
        rftube(a,m,pts,.0025*s,5)
    if lady:
        # Court lady: swept sides, braided nape chignon and French hood, no royal wig.
        rfsphere(a,m,x,y-.054*s,z-.124*s,.068*s,.061*s,.044*s,28,18)
        for j in range(5):
            pts=[]
            for i in range(49):
                t=math.tau*i/48;r=.037+j*.006
                pts.append((x+s*r*math.cos(t),y+s*(-.052+r*.85*math.sin(t)),z+s*(-.165+.003*math.sin(t*14+j))))
            rftube(a,m,pts,.0045*s,6)
        for sg in [-1,1]:
            for j in range(4):
                pts=[(x+s*sg*(.087+.003*math.sin(t*9+j)),y+s*(.077-.19*t),z+s*(.045-.14*t+.004*j)) for t in [i/20 for i in range(21)]]
                rftube(a,m,pts,.006*s,7)
        return
    # Bobbed nape for the Valois; full shoulder-length rear curls for Louis XIV.
    for i in range(23):
        phi=math.pi*.48+math.pi*1.04*i/22;pts=[]
        for j in range(23):
            t=j/22;rx=.091+.01*t;rz=.092+.018*t
            wave=.004*math.sin(t*(23 if long else 7)+i)
            pts.append((x+s*(rx*math.sin(phi)+wave),y+s*(.024-t*(.235 if long else .16)),z+s*(rz*math.cos(phi)+wave)))
        rftube(a,m,pts,(.012 if long else .007)*s,7)
    for sg in [-1,1]:
        for j in range(12):
            angle=(j/11)*math.pi*.88
            pts=[]
            for i in range(14):
                t=i/13; px=sg*(.007+.090*math.sin(t*math.pi*.64)); py=.13*math.cos(t*math.pi*.64)
                pz=-.015+.080*math.cos(angle)
                pts.append((x+s*px,y+s*(py+.004*math.sin(t*12+j)),z+s*pz))
            rftube(a,m,pts,.007*s,6)
        if long:
            for j in range(16):
                xx=sg*(.082+(j%4)*.012); zz=-.058+(j//4)*.034
                pts=[(x+s*(xx+.007*math.sin(t*27+j)),y+s*(.075-(.26+.025*math.sin(j))*t),z+s*(zz+.012*math.cos(t*27+j))) for t in [i/36 for i in range(37)]]
                rftube(a,m,pts,.009*s,9)

def rfbeard(a,x,y,z,s=1,marble=False):
    m=stone if marble else hair
    # Continuous U-shaped beard follows cheeks and chin; no detached vertical locks.
    vv=[];ff=[];count=32
    for j in range(7):
        t=j/6
        for i in range(count+1):
            u=-1+2*i/count; upper=-.050-.040*(1-abs(u)); bottom=-.135+.061*abs(u)
            vv.append((x+.076*s*u,y+s*(upper*(1-t)+bottom*t),z+s*((.072-.015*abs(u))*(1-t)+(.066-.022*abs(u))*t+.002*math.sin(i*2.1))))
    for j in range(6):
        for i in range(count):k=j*(count+1)+i;ff.append((k,k+1,k+count+2,k+count+1))
    rfadd(a,m,vv,ff)
    for sg in [-1,1]:
        for j in range(12):
            u=sg*(j+.5)/12; upper=-.050-.040*(1-abs(u)); bottom=-.135+.061*abs(u)
            rftube(a,m,[(x+s*(.076*u+.0015*math.sin(t*12+j)),y+s*(upper*(1-t)+bottom*t),z+s*((.075-.015*abs(u))*(1-t)+(.069-.022*abs(u))*t)) for t in [i/8 for i in range(9)]],.002*s,6)
        rftube(a,m,[(x+sg*.003*s,y-.037*s,z+.105*s),(x+sg*.024*s,y-.041*s,z+.095*s),(x+sg*.043*s,y-.038*s,z+.079*s)],.006*s,8)

def rfcap(a,x,y,z,s=1,marble=False):
    m=stone if marble else velvet
    rfsphere(a,m,x-.025*s,y+.13*s,z-.007*s,.15*s,.042*s,.113*s,32,14)
    rfloft(a,m,x,z,[(y+.10*s,.111*s,.095*s),(y+.125*s,.115*s,.097*s)],28)
    for i in range(11):
        t=i*math.pi/10
        rfsphere(a,stone if marble else gold,x+.122*s*math.cos(t),y+.145*s,z+.08*s*math.sin(t),.006*s,.006*s,.006*s,10,6)
    rftube(a,stone if marble else linen,[(x-.10*s,y+.15*s,z),(x-.16*s,y+.22*s,z-.01*s),(x-.23*s,y+.235*s,z-.025*s)],.007*s,6)
    for i in range(9):
        t=i/8
        rftube(a,stone if marble else linen,[(x-s*(.10+.13*t),y+s*(.15+.085*t),z-s*.025*t),(x-s*(.135+.125*t),y+s*(.185+.080*t),z-s*.025*t)],.003*s,5)

def rfchain(a,x,y,z,w=.15,h=.13,marble=False,bone=None):
    for i in range(19):
        t=math.pi*i/18
        f=2.0 if marble else 1
        rfsphere(a,stone if marble else gold,x+w*math.cos(t),y-h*math.sin(t),z+.02*math.sin(t),.007*f,.011*f,.005*f,12,8,bone)

def rfflush(asset,rig=None):
    objs=[]
    for (a,name),b in list(rfbatch.items()):
        if a!=asset:continue
        mesh=bpy.data.meshes.new(asset+' '+name);mesh.from_pydata([(x,-z,y) for x,y,z in b['v']],[],b['f']);mesh.update()
        bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
        mesh.materials.append(b['mat'])
        for p in mesh.polygons:p.use_smooth=True
        obj=bpy.data.objects.new(asset+' '+name,mesh);rfscene.collection.objects.link(obj);objs.append(obj)
        if b.get('head'):obj['firstPersonHidden']=True
        if rig:
            groups={name:obj.vertex_groups.new(name=name) for name in rig.data.bones.keys()}
            scale=.95 if asset=='courtFemale' else 1
            for i,bone_name in enumerate(b['w']):
                y=b['v'][i][1]/scale; weights={bone_name:1.0}
                if bone_name=='Chest':
                    t=max(0,min(1,(y-1.06)/.29));weights={'Hips':1-t,'Chest':t}
                elif bone_name.startswith(('UpperArm.','Forearm.')):
                    suffix=bone_name.split('.')[1];t=max(0,min(1,(y-1.06)/.16))
                    weights={f'UpperArm.{suffix}':t,f'Forearm.{suffix}':1-t}
                for weight_name,weight in weights.items():
                    if weight>0:groups[weight_name].add([i],weight,'REPLACE')
            mod=obj.modifiers.new('Court humanoid skin','ARMATURE');mod.object=rig;obj.parent=rig
        del rfbatch[(a,name)]
    rfmodels[asset]=objs
    return objs

def rfexport(a,objects,out,animate=False):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.gltf(filepath=str(out/(a+'.glb')),export_format='GLB',use_selection=True,use_active_scene=True,export_yup=True,
        export_animations=animate,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_nla_strips=True,export_anim_single_armature=True,
        export_materials='EXPORT',export_skins=True,export_extras=True)
    for o in objects:
        if o.type=='MESH':o.data.calc_loop_triangles()
    rfstats[a]={'bytes':(out/(a+'.glb')).stat().st_size,'triangles':sum(len(o.data.loop_triangles) for o in objects if o.type=='MESH')}

def rfbust(asset,king):
    global rfbone
    rfbone='Head'; s=2.45; cy=.79
    rfloft(asset,stone,0,0,[(0,.21,.16),(.08,.21,.16),(.16,.28,.17),(.38,.48,.23),(.48,.43,.20),(.53,.19,.12)],40)
    rfloft(asset,stone,0,0,[(.42,.13,.12),(.65,.11,.11)],32)
    head_start={key:len(batch['v']) for key,batch in rfbatch.items()}
    rfhead(asset,0,cy,0,s,king,True)
    rfhair(asset,0,cy,0,s,king=='louis',True)
    if king=='francois':
        rfbeard(asset,0,cy,0,s,True);rfcap(asset,0,cy,0,s,True)
        # Puffed and slashed doublet, flat broad shoulders from Clouet's portrait.
        for sg in [-1,1]:
            rfsphere(asset,stone,sg*.35,.36,-.005,.18,.20,.19,24,16)
            for j in range(7):
                xx=sg*(.19+j*.043)
                rftube(asset,stone,[(xx,.24,.17),(xx+sg*.025,.40,.185),(xx,.50,.09)],.016,7)
        rfchain(asset,0,.49,.23,.28,.23,True)
        rfsphere(asset,stone,0,.23,.265,.048,.058,.025,24,16)
    else:
        # Bernini's royal head is turned, distinct from the frontal Valois portrait.
        angle=math.radians(-14)
        for key,batch in rfbatch.items():
            for i in range(head_start.get(key,0),len(batch['v'])):
                vx,vy,vz=batch['v'][i];batch['v'][i]=(vx*math.cos(angle)+vz*math.sin(angle),vy,-vx*math.sin(angle)+vz*math.cos(angle))
        # Swept Baroque mantle with real folds, edge thickness and lace cravat.
        v=[];f=[];nx=48;ny=16
        for j in range(ny+1):
            t=j/ny
            for i in range(nx+1):
                u=-1+2*i/nx; edge=1-.20*abs(u); wave=math.sin(u*12+t*5)
                v.append((u*.53,(.07+t*.43)*edge+.035*math.sin(u*4+t*7),.15+.09*(1-u*u)+.045*wave*math.sin(t*math.pi)))
        for j in range(ny):
            for i in range(nx):q=j*(nx+1)+i;f.append((q,q+1,q+nx+2,q+nx+1))
        rfadd(asset,stone,v,f)
        for j in range(5):
            yy=.42+j*.026
            rftube(asset,stone,[(u*.085,yy-.03*abs(u),.245+.013*math.sin(u*12+j)) for u in [i/10 for i in range(-10,11)]],.012,7)
        for sg in [-1,1]:
            for j in range(6):
                x=sg*(.26+j*.04)
                rftube(asset,stone,[(x,.40,.18),(x+sg*.025,.32,.20),(x+sg*.012,.25,.17)],.012,7)
    objs=rfflush(asset);rfexport(asset,objs,RFBUST)
    # Separate exhibition position after export, coordinates of GLB remain local.
    for o in objs:o.location.x=-1.8 if king=='francois' else 1.8

def rfrig(asset,female=False):
    factor=.95 if female else 1
    specs=[('Root',(0,0,0),(0,.15,0),None),('Hips',(0,.92,0),(0,1.08,0),'Root'),('Spine',(0,1.08,0),(0,1.27,0),'Hips'),('Chest',(0,1.27,0),(0,1.44,0),'Spine'),('Neck',(0,1.44,0),(0,1.52,0),'Chest'),('Head',(0,1.52,0),(0,1.76,0),'Neck')]
    for sg,suffix in [(1,'L'),(-1,'R')]:
        specs.extend([(f'UpperArm.{suffix}',(sg*.22,1.41,0),(sg*.29,1.13,0),'Chest'),(f'Forearm.{suffix}',(sg*.29,1.13,0),(sg*.32,.89,.018),f'UpperArm.{suffix}'),(f'Hand.{suffix}',(sg*.32,.89,.018),(sg*.32,.715,.018),f'Forearm.{suffix}'),(f'Thigh.{suffix}',(sg*.10,.94,0),(sg*.10,.51,.014),'Hips'),(f'Shin.{suffix}',(sg*.10,.51,.014),(sg*.10,.12,0),f'Thigh.{suffix}'),(f'Foot.{suffix}',(sg*.10,.12,0),(sg*.10,.07,.17),f'Shin.{suffix}')])
    arm=bpy.data.armatures.new(asset+' skeleton');rig=bpy.data.objects.new(asset+' Rig',arm);rfscene.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
    for name,head,tail,parent in specs:
        b=arm.edit_bones.new(name);b.head=(head[0]*factor,-head[2]*factor,head[1]*factor);b.tail=(tail[0]*factor,-tail[2]*factor,tail[1]*factor)
        if parent:b.parent=arm.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
    rig['armIK']={'elbowMin':5,'elbowMax':145,'shoulderMax':155,'wristSwing':70,'wristTwist':80,'forearmTwist':90}
    for suffix in ['L','R']:
        fore=rig.pose.bones['Forearm.'+suffix];fore.use_ik_limit_x=True
        fore.ik_min_x=math.radians(-145);fore.ik_max_x=math.radians(-5)
        fore.lock_ik_y=True;fore.lock_ik_z=True
        fore['axialRollLimitDegrees']=90
        upper=rig.pose.bones['UpperArm.'+suffix];upper['shoulderConeDegrees']=155
        wrist=rig.pose.bones['Hand.'+suffix];wrist['swingLimitDegrees']=70;wrist['twistLimitDegrees']=80
    return rig,factor

def rfavatar(asset,female=False):
    global rfbone
    rig,factor=rfrig(asset,female);cloth=blue if female else velvet
    rfbone='Chest'
    rfloft(asset,cloth,0,0,[(1.02,.146,.107),(1.06,.147,.11),(1.13,.157,.115),(1.24,.183,.126),(1.33,.210,.128),(1.39,.220,.117),(1.425,.208,.102),(1.449,.150,.081),(1.46,.073,.061)],40,pleat=.010)
    rfbone='Neck';rfloft(asset,skin,0,0,[(1.42,.058,.053),(1.55,.05,.048)],24)
    # White linen collar pleats rather than a large later-century ruff.
    rfloft(asset,linen,0,0,[(1.435,.080,.070),(1.46,.091,.075),(1.482,.07,.065)],40,pleat=.10)
    rfbone='Head';rfhead(asset,0,1.625,0,portrait='courtLady' if female else None);rfhair(asset,0,1.625,0,lady=female)
    if female:
        # French hood: arc framing the crown, pearl band and back veil.
        rftube(asset,cloth,[(.104*math.cos(t),1.64+.126*math.sin(t),-.02) for t in [i*math.pi/32 for i in range(33)]],.024,10)
        for i in range(19):
            t=math.pi*i/18;rfsphere(asset,linen,.108*math.cos(t),1.64+.126*math.sin(t),.006,.006,.006,.006,10,6)
        # Hood ribbon ends leave the braided back of the head visible.
        for sg in [-1,1]:
            rftube(asset,cloth,[(sg*.08,1.69,-.061),(sg*.081,1.53,-.086),(sg*.066,1.40,-.078)],.014,7)
    else:rfcap(asset,0,1.625,0,.82);rfbeard(asset,0,1.625,0,.8)
    rfbone='Chest';rfchain(asset,0,1.435,.115,.155,.17)
    rfsphere(asset,gold,0,1.26,.15,.022,.030,.008,16,10)
    for sg,suffix in [(1,'L'),(-1,'R')]:
        rfbone=f'UpperArm.{suffix}'
        rfloft(asset,cloth,sg*.24,0,[(1.08,.052,.055,sg*.300),(1.14,.057,.061,sg*.292),(1.20,.071,.076,sg*.278),(1.27,.092,.094,sg*.259),(1.34,.102,.101,sg*.243),(1.39,.090,.089,sg*.231),(1.425,.060,.063,sg*.218),(1.441,.029,.034,sg*.205)],32,pleat=.025)
        for j in range(5):
            t=(j/4)*math.pi
            rftube(asset,linen,[(sg*.24+.088*math.cos(t),1.24,.093*math.sin(t)),(sg*.24+.099*math.cos(t),1.34,.103*math.sin(t))],.008,6)
        rfbone=f'Forearm.{suffix}';rfloft(asset,cloth,sg*.30,0,[(.89,.038,.040,sg*.32),(.96,.044,.048,sg*.316),(1.04,.051,.055,sg*.307),(1.10,.055,.059,sg*.296),(1.17,.056,.060,sg*.289)],32)
        rfloft(asset,linen,sg*.32,.015,[(.88,.045,.046),(.925,.048,.048)],24,pleat=.12)
        rfbone=f'Hand.{suffix}'
        rfhand(asset,sg,suffix,rig,factor)
        rfbone=f'Thigh.{suffix}'
        rfloft(asset,cloth,sg*(.075 if female else .10),0,[(.52,.058,.066),(.58,.069,.077),(.71,.065 if female else .088,.09),(.84,.065 if female else .097,.105),(.95,.060 if female else .097,.106),(1.065,.060 if female else .080,.095)],32,pleat=.025)
        rfbone=f'Shin.{suffix}';rfloft(asset,linen,sg*.10,0,[(.12,.038,.035),(.33,.052,.054),(.56,.066,.067)],20)
        rfbone=f'Foot.{suffix}';rfsphere(asset,leather,sg*.10,.067,.065,.064,.065,.14,24,14)
        rftube(asset,gold,[(sg*.10-.045,.118,.08),(sg*.10+.045,.118,.08)],.008,6)
    if female:
        rfbone='Hips'
        rfloft(asset,cloth,0,0,[(.075,.42,.34),(.13,.425,.345),(.40,.35,.29),(.70,.27,.21),(1.04,.145,.108)],48,pleat=.028)
        # Contrasting forepart, gold seam and floral embroidery.
        for sg in [-1,1]:
            rftube(asset,gold,[(sg*.27,.12,.28),(sg*.20,.49,.24),(sg*.11,.82,.16),(sg*.035,1.02,.106)],.009,7)
        for j in range(7):
            yy=.19+j*.105; zz=.347-(yy-.1)*.247
            rfsphere(asset,gold,0,yy,zz,.012,.02,.005,10,6)
    else:
        rfbone='Hips';rfloft(asset,cloth,0,0,[(.95,.16,.115),(1.055,.15,.11)],28,pleat=.045)
        for i in range(7):rfsphere(asset,gold,0,1.10+i*.048,.118,.0055,.007,.004,10,6,'Chest')
    rfbone='Hips';rfloft(asset,gold,0,0,[(1.035,.15,.115),(1.055,.151,.116)],32)
    # Scale female mesh and rig together before binding; feet remain at zero.
    if factor!=1:
        for (a,_),b in rfbatch.items():
            if a==asset:b['v']=[(x*factor,y*factor,z*factor) for x,y,z in b['v']]
    objects=rfflush(asset,rig)
    rig.animation_data_create()
    for clip,frames in [('Idle',90),('Walking',30),('StrafeLeft',30),('StrafeRight',30)]:
        action=bpy.data.actions.new(clip);rig.animation_data.action=action
        for frame in range(0,frames+1,3):
            phase=math.tau*frame/frames
            for p in rig.pose.bones:
                p.rotation_mode='XYZ';p.rotation_euler=(0,0,0);p.location=(0,0,0)
            if clip=='Idle':
                rig.pose.bones['Chest'].rotation_euler.x=.012*math.sin(phase)
                rig.pose.bones['Head'].rotation_euler.z=.013*math.sin(phase)
                rig.pose.bones['Hips'].location.y=.004*math.sin(phase)
                for sg,suffix in [(1,'L'),(-1,'R')]:rig.pose.bones[f'UpperArm.{suffix}'].rotation_euler.x=sg*.022*math.sin(phase)
            elif clip=='Walking':
                rig.pose.bones['Hips'].location.y=.018*(1-math.cos(phase*2))
                rig.pose.bones['Chest'].rotation_euler.z=.032*math.sin(phase)
                for sg,suffix in [(1,'L'),(-1,'R')]:
                    t=phase+(math.pi if sg<0 else 0)
                    rig.pose.bones[f'Thigh.{suffix}'].rotation_euler.x=.38*math.sin(t)
                    rig.pose.bones[f'Shin.{suffix}'].rotation_euler.x=-.52*max(0,math.sin(t))
                    rig.pose.bones[f'Foot.{suffix}'].rotation_euler.x=.15*math.sin(t)
                    rig.pose.bones[f'UpperArm.{suffix}'].rotation_euler.x=-.32*math.sin(t)
                    rig.pose.bones[f'Forearm.{suffix}'].rotation_euler.x=-.26-.07*math.sin(t)
            else:
                direction=1 if clip=='StrafeLeft' else -1
                rig.pose.bones['Hips'].location.x=direction*.022*math.sin(phase)
                rig.pose.bones['Hips'].location.y=.014*(1-math.cos(phase*2))
                rig.pose.bones['Chest'].rotation_euler.z=direction*.025*math.sin(phase)
                for sg,suffix in [(1,'L'),(-1,'R')]:
                    t=phase+(0 if sg==direction else math.pi)
                    # Local bone Z tilts a vertical leg sideways; X lifts the foot.
                    rig.pose.bones[f'Thigh.{suffix}'].rotation_euler.z=direction*.30*math.sin(t)
                    rig.pose.bones[f'Thigh.{suffix}'].rotation_euler.x=.10*max(0,math.sin(t))
                    rig.pose.bones[f'Shin.{suffix}'].rotation_euler.x=-.29*max(0,math.sin(t))
                    rig.pose.bones[f'Foot.{suffix}'].rotation_euler.z=-direction*.15*math.sin(t)
                    # Sidesteps keep relaxed arms; no forward-walk arm swing.
                    rig.pose.bones[f'Forearm.{suffix}'].rotation_euler.x=-.19
            for p in rig.pose.bones:
                p.keyframe_insert(data_path='rotation_euler',frame=frame,group=p.name);p.keyframe_insert(data_path='location',frame=frame,group=p.name)
        rig.animation_data.action=None
        track=rig.animation_data.nla_tracks.new();track.name=clip;strip=track.strips.new(clip,0,action);strip.name=clip
    rfscene.frame_start=0;rfscene.frame_end=90;rfscene.frame_set(0)
    rfexport(asset,[rig]+objects,RFOUT,True)
    rig.location=(3.8 if female else -3.8,0,0)

rfbust('bustFrancoisI','francois');rfbust('bustLouisXIV','louis')
rfavatar('courtMale');rfavatar('courtFemale',True)
world=bpy.data.worlds.new('Portrait studio');world.use_nodes=True;rfscene.world=world
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.25,.28,.32,1);bg.inputs[1].default_value=.7
for name,pos,power,size in [('Key',(0,-4,5),1500,5),('Fill',(-4,-1,3),850,4),('Rim',(3,2,4),1800,3)]:
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.shape='DISK';light.size=size
    obj=bpy.data.objects.new(name,light);rfscene.collection.objects.link(obj);obj.location=pos;obj.rotation_euler=(Vector((0,0,1))-obj.location).to_track_quat('-Z','Y').to_euler()
camdata=bpy.data.cameras.new('Portraits camera');cam=bpy.data.objects.new('Portraits camera',camdata);rfscene.collection.objects.link(cam);cam.location=(0,-10,3);cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat('-Z','Y').to_euler();camdata.lens=40;rfscene.camera=cam
rfscene.render.resolution_x=1600;rfscene.render.resolution_y=1000;rfscene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(RFEVID/'renaissance-court.blend'),compress=True)
(RFEVID/'asset-stats.json').write_text(json.dumps(rfstats,indent=2))
print(json.dumps(rfstats))
