"""Reference-led ear contours and continuous sculpted beard. Run via Blender MCP.
Authoring coordinates are X right, Y up, Z front; no primitive operators.
"""
from pathlib import Path
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
code=(ROOT/'scripts/blender-refined-avatars.py').read_text(encoding='utf-8-sig')
exec(compile(code.split('main=main.replace(')[0],'refined-foundations','exec'))
OUT=ROOT/'artifacts/avatars/francois';OUT.mkdir(parents=True,exist_ok=True)
scene.name='Cour - implantation anatomique et barbe Francois Ier'

# Retain the high bun and court cap, without retaining the old scalp or flyaway cards.
organic=(ROOT/'scripts/blender-organic-avatars.py').read_text(encoding='utf-8-sig')
native_code=organic.split('def native_hair(',1)[1].split('\ndef build_groom():',1)[0]
native_code=native_code.replace('m for m in ob.modifiers','m for m in ev.modifiers')
exec(compile('def native_hair('+native_code,'evaluated-native-hair','exec'))
accessories=organic.split('    if female:\n        # Tall coiled bun',1)[1].split('\ndef build_beard():',1)[0]
accessories='    if female:\n        # Tall coiled bun'+accessories
accessories=accessories.replace('range(120)','range(80)').replace('TAU*i/120','TAU*i/80')
start=accessories.index('        loose=[]');end=accessories.index("        strip('Ruban",start)
accessories=accessories[:start]+accessories[end:]
exec(compile('def groom_accessories():\n'+accessories,'court-accessories','exec'))

def beard_weight(p):
    x,h,d=p;u=abs(x)
    # Curved cheek line descends from the sideburn towards the corner of the mouth.
    line=1.580+.058*smooth((u-.028)/.047)
    cheek=smooth((line-h)/.005)*smooth((h-1.520)/.010)*smooth((d-.008)/.021)
    # Preserve the curved vermilion border and a small clear area below the lip.
    mouth=((x/.0305)**2+((h-1.588)/.021)**2)**.5
    cheek*=smooth((mouth-1)/.16)
    moustache=smooth((h-1.597)/.003)*smooth((1.608-h)/.003)*smooth((.033-u)/.006)*smooth((d-.080)/.010)
    moustache*=.9+.1*smooth(u/.004)
    return max(cheek,moustache)

def build_beard():
    # The beard grows FROM the facial topology. There is no offset mask edge.
    original=[Vector((v.co.x,v.co.z,-v.co.y))/scale for v in face.data.vertices]
    weights=[beard_weight(p) for p in original]
    colors=face.data.color_attributes['Complexion']
    for i,(p,w) in enumerate(zip(original,weights)):
        x,h,d=p
        n=Vector((x*.7,-.22 if h<1.56 else -.07,max(.018,d))).normalized()
        thickness=(.0035+.008*gauss(h,1.543,.025))*w
        delta=n*thickness;delta.y-=.006*w*gauss(h,1.533,.017)
        # Identical displacement of Basis and every viseme keeps all attachments exact.
        for key in face.data.shape_keys.key_blocks:key.data[i].co+=coord(delta)
        col=tuple(colors.data[i].color);shade=1+.12*math.sin(x*550+h*700)
        target=(.019*shade,.0065*shade,.003*shade)
        colors.data[i].color=(*(col[k]*(1-w)+target[k]*w for k in range(3)),1)
    face['beardConstruction']='continuous facial topology; feathered cheek boundary; sculpted chin volume'
    vv=[];ff=[];lookup={}
    for poly in face.data.polygons:
        if min(weights[i] for i in poly.vertices)<.72:continue
        row=[]
        for i in poly.vertices:
            if i not in lookup:
                lookup[i]=len(vv);v=face.data.shape_keys.key_blocks[0].data[i].co
                vv.append(Vector((v.x,v.z,-v.y))/scale)
            row.append(lookup[i])
        ff.append(tuple(row))
    emitter=mesh_obj('Surface emission barbe adherente Head',vv,ff,[hair])
    def beard_groom(root,i):
        # Fine curling fibres give the compact rounded beard in the Clouet portrait relief.
        n=Vector((root.x*.7,-.18,max(.025,root.z))).normalized()
        side=n.cross(Vector((0,1,0))).normalized()
        length=.0025+.0025*gauss(root.y,1.540,.025)
        return [root+n*length*t+side*.00045*math.sin(t*math.pi*2+i)-Vector((0,.0015*t,0)) for t in [0,.5,1]]
    curves=native_hair(emitter,1000,.005,beard_groom,'Barbe continue Francois Ier')
    discard(emitter)
    fibres=fibers_mesh('Duvet boucle barbe continue',curves,hair,.00013,False,1)
    base=[Vector((v.co.x,v.co.z,-v.co.y))/scale for v in fibres.data.vertices]
    fibres.shape_key_add(name='Basis')
    for name,pose in POSES.items():
        key=fibres.shape_key_add(name='viseme_'+name);key.value=0
        for i,p in enumerate(base):key.data[i].co=coord(p+facial_delta(p,pose))

def hairline(a):
    # Small C-shaped arch: sideburn / front helix / top helix / behind lobe / nape.
    # Ear occupies depth -0.028..+0.009 and height 1.596..1.657 in the source anatomy.
    u=abs((a+math.pi)%TAU-math.pi)
    rows=[(0,1.700),(.45,1.699),(.82,1.683),(1.04,1.642),(1.13,1.629),
          (1.25,1.653),(1.43,1.662),(1.61,1.650),(1.79,1.605),
          (1.99,1.578 if not female else 1.588),(2.4,1.574 if not female else 1.583),(math.pi,1.577 if not female else 1.585)]
    h=interpolate(rows,u)[0]
    if not female:h-=.006*math.sin(a*2)*smooth((1.04-u)/.4)
    return h

def build_groom():
    global headtree
    points=[Vector((v.co.x,v.co.z,-v.co.y))/scale for v in face.data.vertices]
    headtree=BVHTree.FromPolygons(points,[tuple(p.vertices) for p in face.data.polygons])
    def surface(a,t,extra=0):
        bottom=hairline(a);h=bottom+(1.779-bottom)*t
        direction=Vector((math.sin(a),0,math.cos(a)))
        center=Vector((0,h,-.027))
        hit=headtree.ray_cast(center,direction)
        q=hit[0] if hit[0] is not None else center+direction*.012
        u=abs((a+math.pi)%TAU-math.pi)
        # Keep the hair behind the cartilage, even where the horizontal ray hits the ear.
        if 1.13<u<1.86 and h<1.665:q.x=clamp(q.x,-.079,.079)
        # Coherent sculpted mass with fine flowing furrows; zero offset at hairline.
        ramp=smooth(t/.07);volume=(.005 if female else .009)*ramp
        volume+=(.001 if female else .0015)*ramp*math.sin(a*64+9*t+2*math.sin(a*3))
        if not female and u>1.7:volume+=.005*ramp*(1-t)
        q+=direction*(volume+extra)
        q.y+=.002*ramp*smooth((t-.75)/.25)
        return q
    n=192;rows=24;vv=[];ff=[];uv=[]
    for j in range(rows+1):
        t=j/rows
        for i in range(n):
            a=TAU*i/n;vv.append(surface(a,t));uv.append((i/n,t))
    for j in range(rows):
        for i in range(n):a=j*n+i;b=j*n+(i+1)%n;ff.append((a,b,b+n,a+n))
    ff.append(tuple(rows*n+i for i in range(n)))
    scalp=mesh_obj('Implantation continue tour oreille Head',vv,ff,[hair]);scalp['keepDetail']=True
    scalp['earContour']='temple-sideburn-helix-nape continuous C contour, reference profiles'
    # Dense microstrands run ALONG this surface; they never bridge the scalp in space.
    def groom(root,i):
        a=math.atan2(root.x,root.z+.027)
        t=clamp((root.y-hairline(a))/(1.779-hairline(a)),.01,.94)
        result=[]
        for j in range(9):
            s=j/8
            if female:
                # All swept roots travel towards the high bun without crossing the ear arch.
                aa=a+(math.pi-a)*.32*s if a>=0 else a+(-math.pi-a)*.32*s
                tt=t+(1-t)*s*.9
            else:
                aa=a+.04*math.sin(s*4+i)*s
                tt=t*(1-.92*s)
            q=surface(aa,tt,.0005)
            result.append(q)
        return result
    guides=native_hair(scalp,460,.12,groom,'Tour oreille dense')
    # Reuse the export binding, with substantially finer strands and no front fan/cards.
    dense_ribbons(guides)
    groom_accessories()
    if female:
        loose=[]
        for sg in [-1,1]:
            for i in range(6):
                a=sg*(1.94+.014*i);root=surface(a,.18,.001)
                loose.append([root+Vector((sg*.003*math.sin(t*7),-.044*t,-.004*t)) for t in [j/8 for j in range(9)]])
        fibers_mesh('Petites meches nuque dynamiques',loose,hair,.00022,True,2)

# Fine strands supplement the opaque sculpted mass rather than trying to cover bald panels.
ribbon_source=code.split('def dense_ribbons(guides):',1)[1].split('\nold_clothes=',1)[0]
ribbon_source=ribbon_source.replace('width=.00060','width=.00018').replace("(.030*shade,.011*shade,.0055*shade,1)","(.019*shade,.0065*shade,.003*shade,1)")
exec(compile('def dense_ribbons(guides):'+ribbon_source,'fine-fibre-surface','exec'))

aligned_clothes=build_voluminous_clothes
def build_voluminous_clothes():
    aligned_clothes()
    for ob in objects+native_emitters:
        if not ob.name.startswith(asset) or not ob.get('firstPersonHidden') or 'Col de lin' in ob.name:continue
        blocks=ob.data.shape_keys.key_blocks if ob.data.shape_keys else None
        base=blocks[0].data if blocks else ob.data.vertices
        weights=[smooth((v.co.z/scale-1.435)/.105) for v in base]
        for data in ([k.data for k in blocks] if blocks else [ob.data.vertices]):
            for v,w in zip(data,weights):v.co.z-=.050*scale*w
        if ob.get('hairDynamics'):
            d=ob['hairDynamics'].to_dict()
            for p in d['points']:p[1]-=.050*scale*smooth((p[1]/scale-1.435)/.105)
            d['headCenter'][1]-=.050*scale
            # The compact hair shell stays close to the head; only its fine guides flex.
            d['shapeStiffness']=.35;d['headRadii']=[.082*scale,.124*scale,.104*scale]
            ob['hairDynamics']=d
    # Move the neck/head articulation with the new anatomy, retaining actions and skin weights.
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
    bpy.ops.object.mode_set(mode='EDIT')
    head=rig.data.edit_bones['Head'];head.head.z-=.05*scale;head.tail.z-=.05*scale
    for bone in head.children_recursive:bone.head.z-=.05*scale;bone.tail.z-=.05*scale
    rig.data.edit_bones['Neck'].tail=head.head
    bpy.ops.object.mode_set(mode='OBJECT')
    scene['headLoweringMillimeters']=50

main=main.replace('renaissance-organic-work.blend','renaissance-francois-work.blend')
exec(compile('models={};reports={}'+main,'francois-build','exec'))
