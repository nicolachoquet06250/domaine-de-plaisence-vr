"""Anatomical MakeHuman CC0 faces and groomed hair particles, via Blender MCP.
No Blender mesh primitive operators. Native particle systems are retained in .blend;
their authored guide curves and skinned strand surfaces are exported for WebXR PBD.
"""
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
old_source=(ROOT/'scripts/blender-natural-avatars.py').read_text(encoding='utf-8-sig')
exec(compile(old_source.split('reports={}; models={}')[0],'natural-authoring-functions','exec'))
import random
OUT=ROOT/'artifacts/avatars/organic';OUT.mkdir(parents=True,exist_ok=True)
scene.name='Cour - anatomie et cheveux particulaires';scene.gravity=(0,0,-9.81)
native_emitters=[]
verts=[];facegroups={};uvs=[];group=''
for line in (OUT/'reference/makehuman-base.obj').read_text().splitlines():
    parts=line.split()
    if not parts:continue
    if parts[0]=='v':verts.append(tuple(map(float,parts[1:4])))
    elif parts[0]=='g':group=parts[1]
    elif parts[0]=='f':facegroups.setdefault(group,[]).append(tuple(int(v.split('/')[0])-1 for v in parts[1:]))

def anatomy(p):
    x,y,z=p
    jaw=gauss(y,6.24,.38)*smooth((z-.2)/.7)
    xx=x*.104*(1+(.035 if female else .11)*gauss(y,6.35,.45))
    h=.892+y*.104
    d=z*.104-.063+(.009 if female else .018)*jaw
    return Vector((xx,h,d))

def complexion(obj,vs):
    c=obj.data.color_attributes.new(name='Complexion',type='FLOAT_COLOR',domain='POINT')
    for i,(x,h,d) in enumerate(vs):
        cheeks=gauss(abs(x),.047,.027)*gauss(h,1.616,.023)*smooth(d/.07)
        noise=.004*math.sin(x*930+h*320)*math.sin(h*710-d*610)
        base=(.48,.255,.175) if female else (.40,.20,.128)
        y=(h-.892)/.104; u=abs(x)/.028
        lip=smooth((y-(6.49+.055*u*u))/.026)*smooth(((6.741-.09*u*u)-y)/.024)*smooth((1-u)/.14)*smooth((d-.088)/.010)
        tint=(.38,.13,.105) if female else (.31,.105,.077)
        rgb=(base[0]+.026*cheeks+noise,base[1]-.018*cheeks+noise,base[2]-.012*cheeks+noise)
        c.data[i].color=(*(rgb[k]*(1-lip*.76)+tint[k]*lip*.76 for k in range(3)),1)

def facial_delta(p,pose):
    x,h,d=p;width,opening,protrude,tuck,tup,tout=pose
    # Native lip edge topology and oral cavity move together; Gaussian support extends
    # to cheeks and chin. No replacement elliptical ring is grafted onto the mouth.
    frontweight=smooth((d-.015)/.055)
    mouth=gauss(x,0,.035)*gauss(h,1.589,.018)*frontweight
    jaw=smooth((1.589-h)/.012)*smooth((h-1.493)/.032)*frontweight
    upper=smooth((h-1.590)/.008)*gauss(h,1.594,.017)*gauss(x,0,.032)*frontweight
    dx=x*(width-1)*mouth
    dy=-(opening-.0007)*.74*jaw+(opening-.0007)*.20*upper
    dz=protrude*mouth-opening*.07*jaw
    if h<1.592:dy+=tuck*mouth;dz-=tuck*mouth
    return Vector((dx,dy,dz))

def build_anatomical_face():
    global mh_source_indices,mh_face_positions
    faces=[f for f in facegroups['body'] if all(verts[i][1]>5.30 and (abs(verts[i][0])<.52 or verts[i][1]>6.04) for i in f)]
    ids=sorted(set(i for f in faces for i in f));lookup={v:i for i,v in enumerate(ids)}
    vv=[anatomy(verts[i]) for i in ids];ff=[tuple(lookup[i] for i in f) for f in faces]
    mi=[]
    for f in faces:
        p=sum((Vector(verts[i]) for i in f),Vector())/len(f);x,y,z=p
        # The native labial volumes are painted within their vermilion border.
        labial=abs(x)<.285 and 6.615<y<6.86 and z>1.485
        inner=abs(x)<.31 and 6.36<y<6.86 and z<1.38 and z>.55
        mi.append(0)
    ww=[]
    for x,h,d in vv:
        t=smooth((h-1.469)/.045);ww.append({'Head':t,'Neck':1-t})
    obj=mesh_obj('Visage anatomique Head',vv,ff,[skin,lipmat,oral],mi,weights=ww);complexion(obj,vv)
    # Subdivide the existing anatomical topology, retaining oral loops and ear cartilage.
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    sub=obj.modifiers.new('Subdivisions anatomiques','SUBSURF');sub.levels=1
    bpy.ops.object.modifier_move_up(modifier=sub.name);bpy.ops.object.modifier_apply(modifier=sub.name)
    vv=[Vector((v.co.x,v.co.z,-v.co.y))/scale for v in obj.data.vertices]
    obj.shape_key_add(name='Basis')
    for name,pose in POSES.items():
        key=obj.shape_key_add(name='viseme_'+name)
        for i,p in enumerate(vv):key.data[i].co=coord(p+facial_delta(p,pose))
        key.value=0
    obj['visemeSet']='Oculus-15';obj['anatomicalSource']='MakeHuman base.obj, CC0, 2026-09-12'
    obj['mouthGeometry']='native anatomical vermilion, orbicular loops and oral cavity'
    mh_face_positions=vv
    # Real eye shells from the same reference, with matching eyelid openings.
    for sg,side in [(1,'l'),(-1,'r')]:
        fs=facegroups['helper-'+side+'-eye'];idx=sorted(set(i for f in fs for i in f));mp={v:i for i,v in enumerate(idx)}
        ev=[anatomy(verts[i]) for i in idx]
        # The helper eyeballs are slightly recessed: bring the corneal surface forward.
        for p in ev:p.z+=.001
        eyeobj=mesh_obj('Globe oculaire Head',ev,[tuple(mp[i] for i in f) for f in fs],[white])
        bpy.ops.object.select_all(action='DESELECT');eyeobj.select_set(True);bpy.context.view_layer.objects.active=eyeobj
        sub=eyeobj.modifiers.new('Cornee lisse','SUBSURF');sub.levels=2
        bpy.ops.object.modifier_move_up(modifier=sub.name);bpy.ops.object.modifier_apply(modifier=sub.name)
        ex=sg*.30775*.104;ey=.892+7.28415*.104;dep=1.390*.104-.063+.001
        iv=[];iff=[];ims=[];ns=48
        for j,r in enumerate([0,.0021,.0026,.0047,.0051]):
            for k in range(ns):
                a=TAU*k/ns;iv.append((ex+r*math.cos(a),ey+r*math.sin(a),dep+.0006-.001*(r/.0051)**2))
        for j in range(4):
            for k in range(ns):q=j*ns+k;iff.append((q,j*ns+(k+1)%ns,(j+1)*ns+(k+1)%ns,q+ns));ims.append(0 if j in [0,3] else 1+k%2)
        mesh_obj('Iris anatomique Head',iv,iff,[pupil,iris,iris2],ims)
        pts=[]
        for k in range(30):
            t=k/29;x=sg*(.014+.045*t);h=1.674+.005*math.sin(t*math.pi)-.005*t
            candidates=[p.z for p in vv if abs(p.x-x)<.006 and abs(p.y-h)<.006 and p.z>0]
            pts.append((x,h,max(candidates,default=.09)+.0018))
        strip('Sourcils Head',pts,.0015 if female else .0026,hair)
    for name,mat,lower in [('helper-upper-teeth',teeth,False),('helper-lower-teeth',teeth,True),('helper-tongue',tongue,True)]:
        fs=facegroups[name];ids=sorted(set(i for f in fs for i in f));mp={v:i for i,v in enumerate(ids)};tv=[anatomy(verts[i]) for i in ids]
        ob=mesh_obj(name+' Head',tv,[tuple(mp[i] for i in f) for f in fs],[mat])
        ob.shape_key_add(name='Basis')
        for keyname,pose in POSES.items():
            key=ob.shape_key_add(name='viseme_'+keyname)
            for i,p in enumerate(tv):
                delta=Vector((0,-(pose[1]-.0007)*.65 if lower else 0,0))
                if name=='helper-tongue':delta.y+=pose[4]*smooth((p.z-.01)/.065);delta.z+=pose[5]*smooth((p.z-.01)/.065)
                # Tiny anatomically supported lip-contact/dental differences keep every
                # exported non-silence morph nonempty on the aggregate face.
                key.data[i].co=coord(p+delta)
            key.value=0
    return obj

def fibers_mesh(name,curves,mat,radius=.0008,dynamic=False,followers=1):
    rng=random.Random(148 if female else 92);vv=[];ff=[];particle_ids=[];points=[]
    for curve in curves:points.extend([[p[0]*scale,p[1]*scale,p[2]*scale] for p in curve])
    npoints=len(curves[0])
    for ci,curve in enumerate(curves):
        for follower in range(followers):
            phase=rng.random()*TAU;offset=Vector((rng.uniform(-.0018,.0018),0,rng.uniform(-.0018,.0018))) if follower else Vector()
            start=len(vv)
            for j,p in enumerate(curve):
                t=j/(npoints-1);tangent=Vector(curve[min(j+1,npoints-1)])-Vector(curve[max(j-1,0)])
                tangent.normalize();side=tangent.cross(Vector((0,0,1)))
                if side.length<.01:side=tangent.cross(Vector((0,1,0)))
                side.normalize();other=tangent.cross(side).normalized()
                r=radius*(.22+.78*(1-t)**.5)
                for k in range(3):
                    a=phase+k*TAU/3;pos=Vector(p)+offset*math.sin(math.pi*t)*.8+r*(side*math.cos(a)+other*math.sin(a))
                    vv.append(pos);particle_ids.append(ci*npoints+j)
            for j in range(npoints-1):
                for k in range(3):q=start+j*3+k;ff.append((q,start+j*3+(k+1)%3,start+(j+1)*3+(k+1)%3,q+3))
    ob=mesh_obj(name+' Head',vv,ff,[mat]);ob['strandSurface']=True
    if dynamic:
        att=ob.data.attributes.new('_HAIR_PARTICLE','FLOAT','POINT')
        for value,idx in zip(att.data,particle_ids):value.value=idx
        ob['hairDynamics']={'version':1,'points':points,'pointsPerStrand':npoints,'gravity':9.81,'damping':.965,'shapeStiffness':.055,
            'headCenter':[0,1.650*scale,-.027*scale],'headRadii':[.097*scale,.139*scale,.119*scale],
            'shoulderCenter':[0,1.40*scale,0],'shoulderRadii':[.24*scale,.07*scale,.135*scale]}
    return ob

def scalp_surface():
    # Extract the actual anatomical scalp, not a spherical primitive.
    sv=[];sf=[];mp={}
    for poly in face.data.polygons:
        coords=[Vector((face.data.vertices[i].co.x,face.data.vertices[i].co.z,-face.data.vertices[i].co.y))/scale for i in poly.vertices]
        p=sum(coords,Vector())/len(coords)
        if not (p.y>1.712 or (p.z<.020 and p.y>1.61) or (abs(p.x)>.071 and p.y>1.665)):continue
        ids=[]
        for i,p in zip(poly.vertices,coords):
            if i not in mp:
                p.x*=1.045;p.z=(p.z+.025)*1.045-.025;p.y+=.002
                mp[i]=len(sv);sv.append(p)
            ids.append(mp[i])
        sf.append(tuple(ids))
    scalp=mesh_obj('Cuir chevelu Head',sv,sf,[hair]);smooth_boundary(scalp,5)
    return scalp

def smooth_boundary(ob,iterations):
    bm=bmesh.new();bm.from_mesh(ob.data)
    border=[v for v in bm.verts if v.is_boundary]
    for _ in range(iterations):
        positions={v:sum((e.other_vert(v).co for e in v.link_edges if e.is_boundary),Vector())/max(1,sum(e.is_boundary for e in v.link_edges)) for v in border}
        for v,p in positions.items():v.co=v.co.lerp(p,.6)
    bm.to_mesh(ob.data);bm.free()

def native_hair(emitter,count,length,groom,label):
    # Keep an independent particle emitter in the editable Blender asset.
    ob=emitter.copy();ob.data=emitter.data.copy();ob.name=asset+' Particules '+label;scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.particle_system_add();ps=ob.particle_systems[-1];settings=ps.settings
    settings.type='HAIR';settings.count=count;settings.hair_length=length;settings.hair_step=1 if 'Barbe' in label else 3
    settings.child_type='INTERPOLATED';settings.child_percent=4;settings.rendered_child_count=18
    settings.root_radius=.00035;settings.tip_radius=.00004;settings.radius_scale=1
    settings.clump_factor=.15;settings.roughness_1=.003;settings.roughness_2=.001
    ps.seed=163 if female else 91
    scene.frame_set(1);bpy.context.view_layer.update()
    # Entering particle edit transfers evaluated particles to persistent RNA data.
    scene.tool_settings.particle_edit.default_key_count=3 if 'Barbe' in label else 9
    bpy.ops.particle.particle_edit_toggle();bpy.ops.particle.particle_edit_toggle()
    deps=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(deps);eps=ev.particle_systems[-1]
    mod=next(m for m in ob.modifiers if m.type=='PARTICLE_SYSTEM')
    curves=[]
    # Hair roots are sampled by Blender on the emitter surface. Groom each guide
    # through the API in emitter coordinates, then retain the same points for export.
    for pi,p in enumerate(eps.particles):
        root=Vector((p.hair_keys[0].co.x,p.hair_keys[0].co.z,-p.hair_keys[0].co.y))/scale
        curve=groom(root,pi);curves.append(curve)
        for key,co in zip(ps.particles[pi].hair_keys,curve):key.co_object_set(ev,mod,p,coord(co))
    ps.use_hair_dynamics=True
    if ps.cloth:
        ps.cloth.settings.quality=6;ps.cloth.settings.mass=.015
        ps.cloth.settings.bending_stiffness=8 if not female else 25
    # Exported strand mesh is the runtime representation. Native particles are kept
    # editable and visible in Blender without duplicating them in studio renders.
    ob.hide_render=True;ob.hide_set(True);native_emitters.append(ob)
    ob['particleHairGroom']=label;ob['gravityMetersPerSecondSquared']=9.81
    if len(curves)!=count:raise RuntimeError(f'Hair sampling failed: {len(curves)}/{count}')
    return curves

def build_groom():
    scalp=scalp_surface()
    def groom(root,i):
        result=[];a=math.atan2(root.x,root.z+.027);h=root.y
        for j in range(9):
            t=j/8
            if female:
                target=Vector((.008*math.sin(i),1.805,-.087))
                p=root.lerp(target,smooth(t));p.x+=.017*math.sin(math.pi*t)*(1 if root.x>=0 else -1);p.z-=.025*math.sin(math.pi*t)
                q=Vector((p.x/.098,(p.y-1.650)/.137,(p.z+.027)/.118))
                if q.length<1.025:
                    q.normalize();q*=1.025;p=Vector((q.x*.098,1.650+q.y*.137,-.027+q.z*.118))
            else:
                # Swept crown: guides follow an enlarged cranial contour, then fall
                # to the nape. Front roots sweep towards the temples, clear of eyes.
                aa=a+(1 if a>=0 else -1)*1.20*t if math.cos(a)>.3 else a+.035*math.sin(t*4+i)
                hh=h-(.15+.035*math.sin(i*1.7))*t
                if h>1.71:hh=h-.025*math.sin(t*math.pi/2)-.15*t*t
                rx=.099;dep=.120
                crown=math.sqrt(max(.03,1-((max(hh,1.63)-1.65)/.139)**2))
                p=Vector((rx*math.sin(aa)*crown,hh,dep*math.cos(aa)*crown-.027))
                p=root.lerp(p,smooth(t*3))
                if math.cos(a)>.3:p.y=max(p.y,1.714-.045*t)
                p.x+=.0016*math.sin(t*11+i)*t;p.z+=.0013*math.cos(t*13+i)*t
            result.append(p)
        return result
    curves=native_hair(scalp,112 if not female else 128,.17,groom,'Coiffure')
    fibers_mesh('Cheveux particulaires',curves,hair,.00048,dynamic=not female,followers=4)
    if female:
        # Tall coiled bun, built as a continuous authored surface with wrapped fibres.
        bun=garment('Chignon haut Head',[(1.741,.025,.026,0),(1.769,.048,.049,0),(1.807,.070,.060,0),(1.853,.066,.057,0),(1.885,.042,.038,0),(1.900,.004,.004,0)],hair,'Head',64,28,.0017)
        for v in bun.data.vertices:v.co.y+=.070*scale
        brng=random.Random(31);coils=[]
        for i in range(120):
            phase=TAU*i/120;curve=[]
            for j in range(17):
                t=j/16;a=phase+t*TAU*.7;h=1.759+.137*t
                rx,rz,cx=interpolate([(1.741,.025,.026,0),(1.769,.048,.049,0),(1.807,.070,.060,0),(1.853,.066,.057,0),(1.885,.042,.038,0),(1.900,.004,.004,0)],h)
                curve.append(Vector(((rx+.002)*math.sin(a),h,(rz+.002)*math.cos(a)-.070)))
            coils.append(curve)
        fibers_mesh('Fibres chignon',coils,hairlight,.00048)
        loose=[]
        for sg in [-1,1]:
            for i in range(10):
                loose.append([Vector((sg*(.088+.007*math.sin(t*8+i*.3)),1.682-.15*t,.017-i*.003+.006*math.sin(t*7+i*.5))) for t in [j/8 for j in range(9)]])
        fibers_mesh('Meches libres particulaires',loose,hair,.00068,True,3)
        strip('Ruban du chignon Head',[(.073*math.sin(a),1.807,.063*math.cos(a)-.07) for a in [TAU*i/80 for i in range(81)]],.0023,gold)
    else:
        # Keep the court cap, now above the anatomical cranial volume.
        garment('Toque Head',[(1.749,.085,.080,0),(1.766,.113,.096,-.012),(1.788,.132,.102,-.021),(1.807,.105,.084,-.027),(1.819,.002,.002,-.025)],red,'Head',56,14,.0014)
        build_beard()

def build_beard():
    vv=[];ff=[];mp={};original=[]
    for poly in face.data.polygons:
        pp=[Vector((face.data.vertices[i].co.x,face.data.vertices[i].co.z,-face.data.vertices[i].co.y))/scale for i in poly.vertices]
        p=sum(pp,Vector())/len(pp)
        cheekline=1.598+.022*smooth(abs(p.x)/.075)
        if p.y>cheekline or p.y<1.535 or p.z<.028:continue
        if abs(p.x)<.030 and 1.570<p.y<1.605:continue
        row=[]
        for idx,p in zip(poly.vertices,pp):
            if idx not in mp:
                mp[idx]=len(vv);original.append(p.copy())
                p.x*=1.10;p.z+=.010*smooth((p.z+.02)/.05);p.y-=.018*smooth((1.56-p.y)/.045)
                vv.append(p)
            row.append(mp[idx])
        ff.append(tuple(row))
    beard=mesh_obj('Barbe pleine taillee Head',vv,ff,[hair]);smooth_boundary(beard,4)
    vv=[Vector((v.co.x,v.co.z,-v.co.y))/scale for v in beard.data.vertices]
    beard.shape_key_add(name='Basis')
    for name,pose in POSES.items():
        key=beard.shape_key_add(name='viseme_'+name)
        for i,p in enumerate(vv):key.data[i].co=coord(p+facial_delta(original[i],pose))
        key.value=0
    def groom(root,i):return [root+Vector((.001*math.sin(i)*t,-.006*t,.003*t)) for t in [0,.5,1]]
    curves=native_hair(beard,600,.010,groom,'Barbe taillee')
    fibers=fibers_mesh('Poils de barbe',curves,hairlight,.00026,False,1)
    fv=[Vector((v.co.x,v.co.z,-v.co.y))/scale for v in fibers.data.vertices]
    fibers.shape_key_add(name='Basis')
    for name,pose in POSES.items():
        key=fibers.shape_key_add(name='viseme_'+name)
        for i,p in enumerate(fv):key.data[i].co=coord(p+facial_delta(p,pose))
        key.value=0
    # Defined moustache follows the philtrum and stays clear of the moving vermilion.
    curves=[]
    for sg in [-1,1]:
        for i in range(36):
            root=Vector((sg*(.002+i*.00062),1.601+.001*math.sin(i/36*math.pi),.106-.014*i/36))
            curves.append([root+Vector((sg*.006*t,-.006*t,-.002*t)) for t in [j/4 for j in range(5)]])
    fibers_mesh('Moustache taillee',curves,hair,.00048)

original_clothes=build_clothes
def build_voluminous_clothes():
    start=len(objects);original_clothes()
    for ob in objects[start:]:
        if 'Pourpoint' in ob.name or 'Manche ' in ob.name:
            for v in ob.data.vertices:
                h=v.co.z/scale;v.co.y*=1.22
                if female and 'Pourpoint' in ob.name:
                    # Anatomical chest curvature under the fitted doublet.
                    x=v.co.x/scale;d=-v.co.y/scale
                    if d>0:v.co.y-=scale*.016*(gauss(x,-.071,.06)+gauss(x,.071,.06))*gauss(h,1.315,.073)
        if not female and ' Bas ' in ob.name:
            for v in ob.data.vertices:
                h=v.co.z/scale;sg=1 if v.co.x>0 else -1;cx=sg*.10*scale
                calf=gauss(h,.355,.085)
                v.co.x=cx+(v.co.x-cx)*(1+.34*calf)
                # Bulge of the gastrocnemius lies at the BACK of the shin.
                v.co.y=v.co.y*(1+.40*calf)+.013*scale*calf

models={};reports={}
for asset,female,scale in [('courtMale',False,1),('courtFemale',True,.95)]:
    oldrig=next(o for o in source.objects if o.type=='ARMATURE' and o.name.startswith(asset))
    rig=oldrig.copy();rig.data=oldrig.data.copy();rig.name=asset+' Organic Rig';scene.collection.objects.link(rig);rig.location=(0,0,0)
    objects=[]
    for old in source.objects:
        if old.parent!=oldrig or 'Head' in old.name or not (' Peau.' in old.name or ' Ongles' in old.name):continue
        ob=old.copy();ob.data=old.data.copy();ob.parent=rig;ob.name=asset+' '+('Mains' if ' Peau.' in old.name else 'Ongles');scene.collection.objects.link(ob)
        for mod in ob.modifiers:
            if mod.type=='ARMATURE':mod.object=rig
        objects.append(ob)
    face=build_anatomical_face();build_groom();build_voluminous_clothes()
    for ob in objects:
        if ob.data.shape_keys:
            for key in ob.data.shape_keys.key_blocks[1:]:key.value=0
    models[asset]={'rig':rig,'objects':objects,'face':face}
    reports[asset]={'vertices':sum(len(o.data.vertices) for o in objects),'meshes':len(objects),'nativeHairSystems':sum(o.name.startswith(asset) for o in native_emitters)}
    rig.location.x=-.49 if not female else .49
bpy._natural_models=models;bpy._natural_scene=scene;bpy._organic_emitters=native_emitters
scene.frame_start=1;scene.frame_end=90;scene.frame_set(1)
bpy.data.libraries.write(str(OUT/'renaissance-organic-work.blend'),{scene},fake_user=True,compress=True)
(OUT/'construction.json').write_text(json.dumps(reports,indent=2))
print(json.dumps(reports))
