"""Add actual mouth openings, continuous lips, teeth/tongue and 15 visemes to both existing rigs."""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Vector
ROOT=Path('C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
OUT=ROOT/'artifacts/avatars/lipsync'; OUT.mkdir(parents=True,exist_ok=True)
with bpy.data.libraries.load(str(ROOT/'artifacts/avatars/renaissance-court.blend'),link=False) as (src,dst):
    dst.scenes=src.scenes
source=next(s for s in dst.scenes if any(o.name.startswith('courtMale') and o.type=='ARMATURE' for o in s.objects))
scene=bpy.data.scenes.new('Cour Renaissance - articulation labiale');bpy.context.window.scene=scene
scene.render.fps=30
# width, opening, protrusion, lower lip tuck, tongue elevation, tongue protrusion
POSES={'sil':(1,.001,0,0,0,0),'PP':(.93,.0003,.001,0,0,0),'FF':(1,.004,-.001,.004,0,0),
 'TH':(1,.007,0,0,.014,.018),'DD':(1,.010,0,0,.015,0),'kk':(1.04,.016,0,0,.003,-.004),
 'CH':(.79,.011,.005,0,.006,0),'SS':(1.08,.006,-.001,0,.008,0),'nn':(1,.009,0,0,.012,0),
 'RR':(.85,.012,.003,0,.008,-.001),'aa':(1.08,.023,-.001,0,-.004,0),
 'E':(1.16,.013,-.002,0,.004,0),'I':(1.18,.006,-.002,0,.007,0),
 'O':(.74,.021,.007,0,0,0),'U':(.55,.011,.011,0,.001,0)}
def mat(name,color,rough=.65):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    return m
oral=mat('Bouche - cavite profonde',(.037,.006,.009),.9)
teeth=mat('Dents - ivoire naturel',(.68,.62,.49),.43)
tongue=mat('Langue et gencive',(.42,.105,.105),.62)
stats={}
for asset,factor in [('courtMale',1),('courtFemale',.95)]:
    rigsrc=next(o for o in source.objects if o.name.startswith(asset) and o.type=='ARMATURE')
    rig=rigsrc.copy();rig.data=rigsrc.data.copy();rig.name=asset+' Rig';scene.collection.objects.link(rig);rig.location=(0,0,0)
    objects=[]
    for old in source.objects:
        if old.parent!=rigsrc:continue
        obj=old.copy();obj.data=old.data.copy();obj.name=old.name.split('.')[0];scene.collection.objects.link(obj);obj.parent=rig
        for mod in obj.modifiers:
            if mod.type=='ARMATURE':mod.object=rig
        objects.append(obj)
    face=next(o for o in objects if 'Peau Head' in o.name)
    lipobj=next(o for o in objects if 'Levres Head' in o.name)
    # Remove the old closed lip tubes, retaining the nostril detail from the same batch.
    bm=bmesh.new();bm.from_mesh(lipobj.data)
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.z/factor<1.585],context='VERTS');bm.to_mesh(lipobj.data);bm.free()
    bm=bmesh.new();bm.from_mesh(face.data);bm.faces.ensure_lookup_table()
    unseen=set(bm.verts);shells=[]
    while unseen:
        stack=[unseen.pop()];shell=set(stack)
        while stack:
            for e in stack.pop().link_edges:
                for v in e.verts:
                    if v in unseen:unseen.remove(v);shell.add(v);stack.append(v)
        shells.append(shell)
    head_shell=max(shells,key=len)
    remove=[f for f in bm.faces if all(v in head_shell for v in f.verts) and abs(f.calc_center_median().x/factor)<.039 and abs(f.calc_center_median().z/factor-1.573)<.026 and -f.calc_center_median().y/factor>.045]
    cut=set(remove);boundary=[e for e in bm.edges if sum(f in cut for f in e.link_faces)==1 and len(e.link_faces)==2]
    boundary_verts=set(v for e in boundary for v in e.verts)
    bmesh.ops.delete(bm,geom=remove,context='FACES_ONLY')
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces and v not in boundary_verts],context='VERTS')
    adjacent={v:[] for v in boundary_verts}
    for e in boundary:a,b=e.verts;adjacent[a].append(b);adjacent[b].append(a)
    if any(len(v)!=2 for v in adjacent.values()):raise RuntimeError('Non-manifold mouth boundary')
    ordered=[next(iter(boundary_verts))];prev=None
    while True:
        current=ordered[-1];nxt=next(v for v in adjacent[current] if v!=prev)
        if nxt==ordered[0]:break
        ordered.append(nxt);prev=current
    if len(ordered)!=len(boundary_verts):raise RuntimeError('Multiple mouth holes')
    if len(ordered)<10:raise RuntimeError('Mouth opening boundary not found')
    bm.verts.index_update();boundary_coords=[v.co.copy() for v in ordered]
    boundary_indices=[v.index for v in ordered]
    bm.to_mesh(face.data);bm.free()
    verts=[v.co.copy() for v in face.data.vertices];faces=[tuple(p.vertices) for p in face.data.polygons]
    weights=[[(face.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in face.data.vertices]
    mats=[p.material_index for p in face.data.polygons]; base_count=len(verts)
    skinmat=face.data.materials[0];lipmat=lipobj.data.materials[0]
    # Parametric rings are evaluated for every pose with identical topology.
    specs=[]; N=len(ordered)
    angles=[math.atan2((v.z/factor-1.573)/.026,v.x/factor/.039) for v in boundary_coords]
    def add(spec):specs.append(spec);verts.append(Vector((0,0,0)));return len(verts)-1
    def ring(kind,param,material,previous=None):
        ids=[add((kind,param,i)) for i in range(N)]
        if previous:
            for i in range(N):faces.append((previous[i],previous[(i+1)%N],ids[(i+1)%N],ids[i]));mats.append(material)
        return ids
    prev=boundary_indices
    for t in [.25,.5,.75,1]:prev=ring('skin',t,0,prev)
    for t in [0,.25,.5,.75,1]:prev=ring('lip',t,1,prev)
    for t in [.2,.5,1]:prev=ring('cavity',t,2,prev)
    faces.append(tuple(reversed(prev)));mats.append(2)
    # Eight upper and eight lower teeth with curved dental arch and rounded-looking bevel edges.
    for lower in [False,True]:
        for tooth in range(8):
            xx=(tooth-3.5)*.0053;ids=[]
            for z,y,x in [(0,0,-1),(0,0,1),(0,1,1),(0,1,-1),(1,0,-1),(1,0,1),(1,1,1),(1,1,-1)]:
                ids.append(add(('tooth',(xx,lower,x*.00245,y,z),0)))
            for quad in [(0,1,2,3),(4,7,6,5),(0,4,5,1),(3,2,6,7),(0,3,7,4),(1,5,6,2)]:faces.append(tuple(ids[i] for i in quad));mats.append(3)
    # Tongue oval: top and underside, attached to the lower jaw.
    tr=[]
    for j in range(7):
        row=[]
        for i in range(17):row.append(add(('tongue',(j/6,math.tau*i/16),0)))
        tr.append(row)
    for j in range(6):
        for i in range(16):faces.append((tr[j][i],tr[j+1][i],tr[j+1][i+1],tr[j][i+1]));mats.append(4)
    old=face.data;mesh=bpy.data.meshes.new(asset+' Viseme face');mesh.from_pydata(verts,[],faces);mesh.update()
    for m in [skinmat,lipmat,oral,teeth,tongue]:mesh.materials.append(m)
    for p,mi in zip(mesh.polygons,mats):p.material_index=mi;p.use_smooth=mi!=3
    face.data=mesh
    # Entire face is rigidly bound to Head; jaw/lip motion is additive morph deformation.
    face.vertex_groups.clear()
    groups={b.name:face.vertex_groups.new(name=b.name) for b in rig.data.bones}
    for i,ws in enumerate(weights):
        for name,w in ws:groups[name].add([i],w,'REPLACE')
    groups['Head'].add(list(range(base_count,len(verts))),1,'REPLACE')
    def point(spec,pose):
        width,opening,protrude,tuck,tongue_up,tongue_out=pose
        kind,p,i=spec
        if kind in ['skin','lip','cavity']:
            a=angles[i];co=math.cos(a);si=math.sin(a)
            x=.026*width*co;y=1.573+opening*(.35 if si>0 else .65)*si
            z=.083-.005*abs(co)+protrude
            if si<0:y+=tuck*(-si);z-=tuck*(-si)
            if kind=='skin':
                outer=Vector((x*1.16,y+si*.004,z-.002))*factor;outer=Vector((outer.x,-outer.z,outer.y))
                return boundary_coords[i].lerp(outer,p)
            if kind=='lip':
                x*=1.16-.16*p;y+=si*.004*(1-p);z+=.002*math.sin(p*math.pi)
            else:
                x*=1-.35*p;y-=.004*p;z-=.040*p
        elif kind=='tooth':
            xx,lower,dx,yy,zz=p;x=xx+dx
            # Upper incisors stay at the maxilla, lower teeth descend with the jaw.
            y=1.573+(.003-yy*.005 if not lower else -.002-opening*.57-yy*.004)
            z=.073-.006*(abs(xx)/.025)**2-zz*.003
        else:
            t,a=p;x=.015*math.sin(a)*math.sin(math.pi*t)
            z=.030+t*.040+t*t*t*t*t*t*tongue_out
            y=1.562-opening*.42+t*t*tongue_up+.003*math.cos(a)*math.sin(math.pi*t)
        return Vector((x,-z,y))*factor
    for i,spec in enumerate(specs):mesh.vertices[base_count+i].co=point(spec,POSES['sil'])
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    for name,pose in [('Basis',POSES['sil'])]+[('viseme_'+k,p) for k,p in POSES.items()]:
        key=face.shape_key_add(name=name,from_mix=False)
        for i,spec in enumerate(specs):key.data[base_count+i].co=point(spec,pose)
        key.value=0
    face['firstPersonHidden']=True;face['visemeSet']='Oculus-15';face['mouthGeometry']='open cavity, continuous lips, upper/lower teeth, tongue'
    # Normals must face outwards around the cavity rather than close the mouth opening.
    scene.frame_set(0)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in [rig]+objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=rig
    path=ROOT/'public/gltf/avatars'/f'{asset}.glb'
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,use_active_scene=True,export_yup=True,
      export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_nla_strips=True,export_anim_single_armature=True,
      export_materials='EXPORT',export_skins=True,export_morph=True,export_morph_normal=True,export_extras=True)
    stats[asset]={'bytes':path.stat().st_size,'faceVertices':len(mesh.vertices),'mouthBoundaryVertices':N,'visemes':list(POSES)}
    rig.location.x=-.20 if asset=='courtMale' else .20
scene.frame_start=0;scene.frame_end=90
bpy.data.libraries.write(str(OUT/'renaissance-court-lipsync.blend'),{scene},fake_user=True,compress=True)
(OUT/'model-report.json').write_text(json.dumps(stats,indent=2))
print(json.dumps(stats))
