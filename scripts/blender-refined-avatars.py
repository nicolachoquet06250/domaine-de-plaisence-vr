"""Corrected anatomical alignment, dense ear-cleared grooms, fitted jewellery and shoes.
All modelling uses authored vertices/topology; execution through Blender MCP.
"""
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
src=(ROOT/'scripts/blender-organic-avatars.py').read_text(encoding='utf-8-sig')
prefix,main=src.split('models={};reports={}',1)
prefix=prefix.replace("all(verts[i][1]>5.30 and (abs(verts[i][0])<.52 or verts[i][1]>6.04) for i in f)","all(verts[i][1]>6.04 for i in f)")
prefix=prefix.replace('    mi=[]\n    for f in faces:', '    vv,ff=extend_neck(vv,ff)\n    mi=[]\n    for f in faces:')
exec(compile(prefix,'organic-functions','exec'))
from mathutils.bvhtree import BVHTree
OUT=ROOT/'artifacts/avatars/refined';OUT.mkdir(parents=True,exist_ok=True)
scene.name='Cour - profils coiffures bijoux et souliers corriges'

def extend_neck(vv,ff):
    edges={}
    for f in ff:
        for a,b in zip(f,f[1:]+f[:1]):
            k=tuple(sorted((a,b)));edges[k]=edges.get(k,0)+1
    border=[e for e,n in edges.items() if n==1 and max(vv[i].y for i in e)<1.55]
    adjacent={}
    for a,b in border:adjacent.setdefault(a,[]).append(b);adjacent.setdefault(b,[]).append(a)
    if not adjacent:raise RuntimeError('Neck boundary not found')
    first=min(adjacent);loop=[first];previous=None;current=first
    while True:
        options=[i for i in adjacent[current] if i!=previous];nxt=options[0]
        if nxt==first:break
        loop.append(nxt);previous,current=current,nxt
        if len(loop)>len(adjacent):raise RuntimeError('Non-cyclic neck boundary')
    top=[vv[i].copy() for i in loop];last=loop
    for row in range(1,8):
        t=row/7;ring=[]
        for p in top:
            a=math.atan2(p.x,p.z+.027);target=Vector((.049*math.sin(a),1.443,.044*math.cos(a)))
            q=p.lerp(target,smooth(t));q.y=p.y*(1-t)+1.443*t
            ring.append(len(vv));vv.append(q)
        for i in range(len(loop)):j=(i+1)%len(loop);ff.append((last[i],last[j],ring[j],ring[i]))
        last=ring
    ff.append(tuple(reversed(last)))
    return vv,ff

def discard(ob):
    if ob in objects:objects.remove(ob)
    if ob in native_emitters:native_emitters.remove(ob)
    bpy.data.objects.remove(ob,do_unlink=True)

old_groom=build_groom
def build_groom():
    old_groom()
    for ob in list(objects):
        if any(s in ob.name for s in ['Cuir chevelu','Cheveux particulaires']):discard(ob)
    for ob in list(native_emitters):
        if ob.name.startswith(asset) and 'Coiffure' in ob.name:discard(ob)
    sv=[];sf=[];lookup={}
    for poly in face.data.polygons:
        pp=[Vector((face.data.vertices[i].co.x,face.data.vertices[i].co.z,-face.data.vertices[i].co.y))/scale for i in poly.vertices]
        p=sum(pp,Vector())/len(pp)
        line=1.696+.024*(min(1,abs(p.x)/.083))**1.4
        crown=p.y>line
        rear=p.z<-.061 and p.y>1.601
        side=abs(p.x)>.065 and p.y>1.677 and p.z<.060
        # Ear cartilage and its surrounding skin are never used as scalp.
        ear=abs(p.x)>.061 and 1.590<p.y<1.677 and -.064<p.z<.047
        if not (crown or rear or side) or ear:continue
        row=[]
        for i,q in zip(poly.vertices,pp):
            if i not in lookup:
                a=math.atan2(q.x,q.z+.027);relief=.0045+.0012*math.sin(a*110+q.y*28)
                n=Vector((q.x,(q.y-1.65)*.7,q.z+.027)).normalized()
                lookup[i]=len(sv);sv.append(q+n*relief)
            row.append(lookup[i])
        sf.append(tuple(row))
    scalp=mesh_obj('Implantation dense oreilles libres Head',sv,sf,[hair]);smooth_boundary(scalp,3)
    scalp['keepDetail']=True
    headtree=BVHTree.FromPolygons([Vector((v.co.x,v.co.z,-v.co.y))/scale for v in face.data.vertices],[tuple(p.vertices) for p in face.data.polygons])
    def groom(root,i):
        a=math.atan2(root.x,root.z+.027);result=[]
        for j in range(9):
            t=j/8
            if female:
                q=root.lerp(Vector((.006*math.sin(i),1.795,-.073)),smooth(t))
                q.x+=.012*math.sin(math.pi*t)*(1 if root.x>=0 else -1)
            else:
                aa=a+(1 if a>=0 else -1)*.95*t if math.cos(a)>.1 else a+.06*t
                h=root.y-(.085+.016*math.sin(i))*t
                if root.y>1.704:h=max(h,1.690-.027*t)
                q=Vector((.100*math.sin(aa),h,.123*math.cos(aa)-.027))
                q=root.lerp(q,smooth(t*2.3))
            u=Vector((q.x/.098,(q.y-1.65)/.133,(q.z+.027)/.117))
            if u.length<1.045:u.normalize();u*=1.045;q=Vector((u.x*.098,1.65+u.y*.133,-.027+u.z*.117))
            center=Vector((0,1.667,-.015));direction=(q-center).normalized()
            hit=headtree.ray_cast(center,direction)
            if hit[0] is not None and (q-center).length<(hit[0]-center).length+.009:q=hit[0]+direction*.009
            if not female and q.z>.024 and abs(q.x)<.074:q.y=max(q.y,1.696+.008*(1-abs(q.x)/.074))
            # All locks reaching ear height pass behind the ear, never over it.
            if q.y<1.678 and abs(q.x)>.06 and q.z>-.060:q.z=-.060-.014*smooth((1.678-q.y)/.04)
            q.x+=.001*math.sin(t*11+i)*t;q.z+=.001*math.cos(t*13+i)*t
            result.append(q)
        return result
    guides=native_hair(scalp,300,.16,groom,'Coiffure dense')
    guides+=frontal_guides(headtree)
    dense_ribbons(guides)

def frontal_guides(tree):
    result=[];center=Vector((0,1.667,-.015))
    for i in range(200):
        x=-.075+.15*(i+.5)/200;h=1.700+.017*(abs(x)/.075)**1.4
        root=Vector((x,h,.100));sg=1 if x>=0 else -1;curve=[]
        for j in range(9):
            t=j/8
            end=Vector((x*.15,1.798,-.074)) if female else Vector((sg*.079,1.736,-.015))
            q=root.lerp(end,smooth(t));q.y+=.012*math.sin(math.pi*t)
            direction=(q-center).normalized();hit=tree.ray_cast(center,direction)
            if hit[0] is not None and (q-center).length<(hit[0]-center).length+.011:q=hit[0]+direction*.011
            q.x+=.0005*math.sin(t*8+i*.21);curve.append(q)
        result.append(curve)
    return result

def dense_ribbons(guides):
    vv=[];ff=[];ids=[];tints=[];rng=random.Random(192 if female else 191)
    mat=material('fibres capillaires denses '+asset,(.028,.010,.005),.76)
    shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    color=mat.node_tree.nodes.new('ShaderNodeVertexColor');color.layer_name='FiberTint';mat.node_tree.links.new(color.outputs['Color'],shader.inputs['Base Color'])
    for ci,curve in enumerate(guides):
        for follower in range(2):
            phase=rng.random()*TAU;start=len(vv);shade=rng.uniform(.73,1.45)
            for j,q in enumerate(curve):
                t=j/8;p=q.copy();normal=Vector((p.x,(p.y-1.65)*.65,p.z+.027)).normalized()
                tangent=(curve[min(8,j+1)]-curve[max(0,j-1)]).normalized();side=tangent.cross(normal).normalized()
                p+=side*(follower-.5)*.00095+normal*(follower*.00015)
                p+=side*.0004*math.sin(t*16+phase)
                width=.00060*(.12+.88*(1-t)**.45)
                for sg in [-1,1]:vv.append(p+sg*side*width);ids.append(ci*9+j);tints.append((.030*shade,.011*shade,.0055*shade,1))
            for j in range(8):a=start+j*2;ff.append((a,a+1,a+3,a+2))
    ob=mesh_obj('Coiffure dense en meches Head',vv,ff,[mat]);ob['strandSurface']=True;ob['keepDetail']=True
    c=ob.data.color_attributes.new(name='FiberTint',type='FLOAT_COLOR',domain='POINT')
    for a,col in zip(c.data,tints):a.color=col
    if not female:
        att=ob.data.attributes.new('_HAIR_PARTICLE','FLOAT','POINT')
        for a,i in zip(att.data,ids):a.value=i
        ob['hairDynamics']={'version':1,'points':[[q.x*scale,q.y*scale,q.z*scale] for curve in guides for q in curve],'pointsPerStrand':9,'gravity':9.81,'damping':.97,'shapeStiffness':.11,'headCenter':[0,1.650*scale,-.027*scale],'headRadii':[.094*scale,.130*scale,.110*scale],'shoulderCenter':[0,1.4*scale,0],'shoulderRadii':[.24*scale,.07*scale,.135*scale]}

old_clothes=build_voluminous_clothes
def build_voluminous_clothes():
    old_clothes()
    for ob in list(objects):
        if 'Soulier ' in ob.name:discard(ob)
    torso=next(o for o in objects if 'Pourpoint taille' in o.name)
    tree=BVHTree.FromPolygons([v.co.copy() for v in torso.data.vertices],[tuple(p.vertices) for p in torso.data.polygons])
    gaps=[]
    for ob in objects:
        if not any(s in ob.name for s in ['Chaine de cour','Medaille','Pendentif','Passementerie pourpoint']):continue
        for v in ob.data.vertices:
            hit=tree.ray_cast(Vector((v.co.x,-1*scale,v.co.z)),Vector((0,1,0)))
            if hit[0] is not None:
                relief=.0033*scale;v.co.y=hit[0].y-relief;gaps.append(relief/scale)
        ob['keepDetail']=True
    for sg,suffix in [(1,'L'),(-1,'R')]:build_shoe(sg,suffix)
    # Independent eye materials: the pupils remain black, only the irises change.
    for ob in objects:
        if 'Iris anatomique' not in ob.name:continue
        for i,mat in enumerate(list(ob.data.materials)):
            if 'iris' not in mat.name.lower():continue
            m=mat.copy();m.name=('Iris vert ' if female else 'Iris marron ')+str(i)
            c=((.035,.19,.055) if i==1 else (.095,.29,.075)) if female else ((.085,.027,.008) if i==1 else (.18,.068,.018))
            m.diffuse_color=(*c,1);next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Base Color'].default_value=(*c,1);ob.data.materials[i]=m
        ob['keepDetail']=True
    # Advance the anatomical head by 45 mm, blending smoothly through the neck.
    # Apply the same transformation to every morph and to simulation guide metadata.
    for ob in objects+native_emitters:
        if not ob.name.startswith(asset) or not ob.get('firstPersonHidden') or 'Col de lin' in ob.name:continue
        blocks=ob.data.shape_keys.key_blocks if ob.data.shape_keys else None
        if blocks:
            for key in blocks:
                for v in key.data:v.co.y-=.045*scale*smooth((v.co.z/scale-1.45)/.105)
        else:
            for v in ob.data.vertices:v.co.y-=.045*scale*smooth((v.co.z/scale-1.45)/.105)
        if ob.get('hairDynamics'):
            d=ob['hairDynamics'].to_dict()
            for p in d['points']:p[2]+=.045*scale*smooth((p[1]/scale-1.45)/.105)
            d['headCenter'][2]+=.045*scale;ob['hairDynamics']=d
    scene['headAdvanceMillimeters']=45;scene['neckTopology']='continuous anatomical boundary loft';scene['necklaceClearanceMm']=3.3

def build_shoe(sg,suffix):
    leather2=material(('cuir prune ' if female else 'cuir espresso ')+suffix,(.066,.009,.018) if female else (.025,.010,.006),.38)
    sole=material('semelle cuir '+asset+suffix,(.022,.012,.008),.72)
    welt=material('couture cuir '+asset+suffix,(.12,.063,.029),.64)
    controls=[(0,-.084),(.027,-.081),(.039,-.052),(.040,0),(.051,.075),(.056,.115),(.050,.157),(.030,.184),(0,.193),(-.032,.184),(-.051,.154),(-.057,.109),(-.046,.046),(-.035,-.013),(-.034,-.060)]
    def outline(t):
        f=t*len(controls);i=int(f)%len(controls);u=f-int(f)
        p0=Vector(controls[(i-1)%len(controls)]);p1=Vector(controls[i]);p2=Vector(controls[(i+1)%len(controls)]);p3=Vector(controls[(i+2)%len(controls)])
        p=.5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u*u+(-p0+3*p1-3*p2+p3)*u*u*u)
        if female:p.x*=.78-.17*smooth((p.y-.12)/.07);p.y+=.008*smooth((p.y-.12)/.07)
        return p
    n=80;vs=[];fs=[]
    def bottom(d):return .009+(.022*smooth((.05-d)/.10) if female else .006*smooth((.01-d)/.06))
    # Layered sole follows the curved last; toe box and heel are distinct shapes.
    for row in range(3):
        for i in range(n):
            p=outline(i/n);vs.append((sg*.10+p.x*(1.04 if row==1 else 1.02),bottom(p.y)+row*.005,p.y))
    for row in range(2):
        for i in range(n):a=row*n+i;b=row*n+(i+1)%n;fs.append((a,b,b+n,a+n))
    fs.extend([tuple(reversed(range(n))),tuple(2*n+i for i in range(n))])
    ob=mesh_obj('Semelle cousue '+suffix,vs,fs,[sole],bone='Foot.'+suffix);ob['keepDetail']=True
    vs=[];fs=[]
    for row in range(9):
        t=row/8
        for i in range(n):
            p=outline(i/n);a=math.atan2(p.x,p.y+.026)
            opening=Vector((.029*math.sin(a),-.027+.039*math.cos(a)))
            q=p.lerp(opening,smooth(t));base=bottom(p.y)+.011
            h=base*(1-t)+.111*t+(.013 if not female else .008)*math.sin(math.pi*t)*smooth((p.y+.035)/.10)
            vs.append((sg*.10+q.x,h,q.y))
    for row in range(8):
        for i in range(n):a=row*n+i;b=row*n+(i+1)%n;fs.append((a,b,b+n,a+n))
    ob=mesh_obj(('Escarpin ' if female else 'Soulier a boucle ')+suffix,vs,fs,[leather2],bone='Foot.'+suffix);ob['keepDetail']=True
    shoe_tree=BVHTree.FromPolygons([v.co.copy() for v in ob.data.vertices],[tuple(p.vertices) for p in ob.data.polygons])
    # Dark lining inside the opening, with a rolled leather collar.
    opening=[(sg*.10+.029*math.sin(TAU*i/n),.111,-.027+.039*math.cos(TAU*i/n)) for i in range(n+1)]
    strip('Bord ouverture soulier '+suffix,opening,.0018,leather2,'Foot.'+suffix)
    outlinepath=[(sg*.10+outline(i/n).x*1.025,bottom(outline(i/n).y)+.011,outline(i/n).y) for i in range(n+1)]
    strip('Trépointe '+suffix,outlinepath,.00085,welt,'Foot.'+suffix)
    # Separate compact heel with bevelled corners; taller and narrower for the woman.
    rx=.022 if female else .032;rd=.024 if female else .034;cx=sg*.10;cd=-.048
    poly=[(-.75,-1),(.75,-1),(1,-.75),(1,.75),(.75,1),(-.75,1),(-1,.75),(-1,-.75)]
    v=[(cx+x*rx*(.91 if j==0 else 1),h,cd+d*rd) for j,h in enumerate([.003,.030 if female else .016]) for x,d in poly]
    f=[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
    mesh_obj('Talon biseaute '+suffix,v,f,[sole],bone='Foot.'+suffix)
    # Raised strap and small rectangular metal buckle over the vamp.
    depth=.047 if not female else .025;hh=.095 if not female else .104
    strapwidth=.028 if female else .039
    pts=[(sg*.10+x,hh+.006*(1-(x/strapwidth)**2),depth) for x in [(-strapwidth+2*strapwidth*i/24) for i in range(25)]]
    strap=strip('Bride de soulier '+suffix,pts,.007 if not female else .003,leather2,'Foot.'+suffix)
    w=.014 if not female else .009;h=.010 if not female else .006
    buckle=[(sg*.10+x,hh+.009,depth+d) for x,d in [(-w,-h),(w,-h),(w,h),(-w,h),(-w,-h)]]
    clasp=strip('Boucle de soulier '+suffix,buckle,.0017 if not female else .0012,gold,'Foot.'+suffix)
    for item,lift in [(strap,.0015),(clasp,.0030)]:
        for v in item.data.vertices:
            hit=shoe_tree.ray_cast(Vector((v.co.x,v.co.y,.35*scale)),Vector((0,0,-1)))
            if hit[0] is not None:v.co.z=hit[0].z+lift*scale
        item['keepDetail']=True

main=main.replace("bpy.data.libraries.write(str(OUT/'renaissance-organic-work.blend')","bpy.data.libraries.write(str(OUT/'renaissance-refined-work.blend')")
exec(compile('models={};reports={}'+main,'refined-build','exec'))
