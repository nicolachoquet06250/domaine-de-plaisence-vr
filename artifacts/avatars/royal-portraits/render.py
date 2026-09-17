import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
ROOT=Path(r'C:/Users/nicol/Documents/workspaces/vr-workspace/test-meta-web-sdk-update')
OUT=ROOT/'artifacts/avatars/royal-portraits'
SOURCE=ROOT/'artifacts/avatars/moustache/renaissance-moustache.blend'
preview='--preview' in sys.argv
records=[]

def direct(rig, name, head, direction):
    bone=rig.data.bones[name]
    q=(bone.tail_local-bone.head_local).rotation_difference(Vector(direction).normalized())
    rig.pose.bones[name].matrix=Matrix.Translation(Vector(head)) @ q.to_matrix().to_4x4() @ bone.matrix_local.to_3x3().to_4x4()
    bpy.context.view_layer.update()

def arm(rig, side, target, hand_direction):
    upper=rig.pose.bones['UpperArm.'+side]
    fore=rig.pose.bones['Forearm.'+side]
    a=upper.head.copy(); c=Vector(target)
    l1=upper.bone.length; l2=fore.bone.length
    delta=c-a; dist=delta.length; axis=delta.normalized()
    assert abs(l1-l2)<dist<l1+l2, ('Unreachable hand target',side,dist)
    along=(l1*l1-l2*l2+dist*dist)/(2*dist)
    pole=Vector((1 if side=='L' else -1,.05,-.05))
    perpendicular=(pole-axis*pole.dot(axis)).normalized()
    b=a+axis*along+perpendicular*math.sqrt(max(0,l1*l1-along*along))
    direct(rig,'UpperArm.'+side,a,b-a)
    direct(rig,'Forearm.'+side,b,c-b)
    direct(rig,'Hand.'+side,c,hand_direction)
    # Turn the palms toward the costume, as in a formal court portrait.
    pb=rig.pose.bones['Hand.'+side]
    direction=Vector(hand_direction).normalized()
    rest=pb.bone
    q=(rest.tail_local-rest.head_local).rotation_difference(direction)
    palm=q @ Vector((-1 if side=='L' else 1,0,0))
    desired=Vector((0,1,0))
    desired=(desired-direction*desired.dot(direction)).normalized()
    current=(palm-direction*palm.dot(direction)).normalized()
    twist=current.rotation_difference(desired)
    pb.matrix=Matrix.Translation(c) @ twist.to_matrix().to_4x4() @ q.to_matrix().to_4x4() @ rest.matrix_local.to_3x3().to_4x4()
    bpy.context.view_layer.update()

for asset,label in [('courtMale','homme'),('courtFemale','femme')]:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene=bpy.context.scene
    rig=next(o for o in scene.objects if o.type=='ARMATURE' and o.name.startswith(asset))
    meshes=[o for o in scene.objects if o.type=='MESH' and o.parent==rig and not o.particle_systems]
    for obj in list(bpy.data.objects):
        if obj not in [rig]+meshes:bpy.data.objects.remove(obj,do_unlink=True)
    rig.animation_data_clear();rig.location=(0,0,0);rig.rotation_euler=(0,0,0)
    rig.data.pose_position='POSE'
    for p in rig.pose.bones:
        p.matrix_basis=Matrix.Identity(4)
        for constraint in list(p.constraints):p.constraints.remove(constraint)
    for obj in meshes:
        obj.hide_render=False;obj.hide_set(False)
        if obj.data.shape_keys:
            obj.data.shape_keys.animation_data_clear()
            for key in obj.data.shape_keys.key_blocks:key.value=0
        # The authored sleeve piping extends below the elbow but is rigidly
        # attached to the upper arm. Bind its lower portion to the forearm in
        # this portrait copy so the gold follows the bent sleeve.
        for side in ['L','R']:
            upper=obj.vertex_groups.get('UpperArm.'+side)
            if not upper:continue
            fore=obj.vertex_groups.get('Forearm.'+side) or obj.vertex_groups.new(name='Forearm.'+side)
            seam_vertices=set()
            for poly in obj.data.polygons:
                mat=obj.data.materials[poly.material_index]
                if mat and ('Or brode' in mat.name or 'Or brodé' in mat.name or 'broderie or' in mat.name):seam_vertices.update(poly.vertices)
            elbow=rig.data.bones['Forearm.'+side].head_local.z
            for i in seam_vertices:
                vertex=obj.data.vertices[i]
                weight=next((g.weight for g in vertex.groups if g.group==upper.index),0)
                if weight<.9:continue
                p=rig.matrix_world.inverted() @ obj.matrix_world @ vertex.co
                amount=max(0,min(1,(elbow+.055-p.z)/.11))
                if amount>0:
                    upper.add([i],1-amount,'REPLACE');fore.add([i],amount,'REPLACE')
    bpy.context.view_layer.update()
    if asset=='courtMale':
        arm(rig,'L',(.235,-.185,1.035),(-.42,0,-1))
        arm(rig,'R',(-.10,-.24,1.15),(1,-.02,-.23))
        # A slightly turned-out foot and lifted chin complete the formal stance.
        foot=rig.pose.bones['Foot.L'];m=foot.matrix.copy()
        foot.matrix=Matrix.Translation(m.translation) @ Matrix.Rotation(math.radians(13),4,'Z') @ m.to_3x3().to_4x4()
        rig.rotation_euler.z=math.radians(-12)
    else:
        arm(rig,'L',(.12,-.245,1.00),(-.92,0,-.42))
        arm(rig,'R',(-.115,-.215,1.025),(.95,0,-.30))
        rig.rotation_euler.z=math.radians(10)
    head=rig.pose.bones['Head'];m=head.matrix.copy()
    head.matrix=Matrix.Translation(m.translation) @ Matrix.Rotation(-rig.rotation_euler.z*.7,4,'Z') @ Matrix.Rotation(math.radians(-2),4,'X') @ m.to_3x3().to_4x4()
    bpy.context.view_layer.update()
    # Repair any obsolete packed-image path from the authoring file.
    missing=[]
    for mat in {m for o in meshes for m in o.data.materials if m}:
        if not mat.use_nodes:continue
        for node in mat.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image:
                img=node.image
                if not img.packed_file and not Path(bpy.path.abspath(img.filepath)).is_file():
                    candidates=list((ROOT/'artifacts/avatars/fbx'/asset/'Textures').glob(Path(img.filepath).name))
                    if candidates:img.filepath=str(candidates[0]);img.reload()
                    else:missing.append(img.name)
    assert not missing,missing
    scene.render.engine='CYCLES'
    scene.cycles.samples=16 if preview else 64
    scene.cycles.use_denoising=True
    scene.cycles.device='CPU'
    scene.render.threads_mode='FIXED';scene.render.threads=12
    scene.world=bpy.data.worlds.new('Fond blanc monochrome')
    scene.world.use_nodes=True
    nodes=scene.world.node_tree.nodes;links=scene.world.node_tree.links;nodes.clear()
    output=nodes.new('ShaderNodeOutputWorld');mix=nodes.new('ShaderNodeMixShader')
    path=nodes.new('ShaderNodeLightPath')
    ambient=nodes.new('ShaderNodeBackground');ambient.inputs['Color'].default_value=(1,1,1,1);ambient.inputs['Strength'].default_value=.24
    white=nodes.new('ShaderNodeBackground');white.inputs['Color'].default_value=(1,1,1,1);white.inputs['Strength'].default_value=2
    links.new(path.outputs['Is Camera Ray'],mix.inputs[0]);links.new(ambient.outputs[0],mix.inputs[1]);links.new(white.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],output.inputs[0])
    scene.view_settings.view_transform='Standard'
    scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
    scene.render.film_transparent=False
    scene.render.dither_intensity=0
    for name,loc,power,size in [('Grande boite douce',(-3,-4,4.5),330,4),('Remplissage',(3,-2,2.6),150,3),('Contour',(1,2,3),230,2.5)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
        light=bpy.data.objects.new(name,data);scene.collection.objects.link(light);light.location=loc
        light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
    deps=bpy.context.evaluated_depsgraph_get()
    coords=[o.evaluated_get(deps).matrix_world @ Vector(c) for o in meshes for c in o.evaluated_get(deps).bound_box]
    low=min(c.z for c in coords);high=max(c.z for c in coords);center=(low+high)/2
    camera=bpy.data.objects.new('Portrait vertical en pied',bpy.data.cameras.new('Portrait vertical en pied'));scene.collection.objects.link(camera);scene.camera=camera
    camera.data.type='ORTHO';camera.data.ortho_scale=(high-low)*1.15
    camera.location=(0,-6,center+.07)
    camera.rotation_euler=(Vector((0,0,center))-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.resolution_x=720 if preview else 1600
    scene.render.resolution_y=1080 if preview else 2400
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='8'
    scene.render.filepath=str(OUT/(label+('-apercu' if preview else '-pose-royale')+'.png'))
    if not preview:
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(label+'-pose-royale.blend')))
    bpy.ops.render.render(write_still=True)
    records.append({'avatar':asset,'file':scene.render.filepath,'boundsZ':[low,high],'originalMeshes':len(meshes),'background':'#FFFFFF','resolution':[scene.render.resolution_x,scene.render.resolution_y]})
    print('PORTRAIT_RENDERED',label,flush=True)
(OUT/('preview-report.json' if preview else 'render-report.json')).write_text(json.dumps(records,indent=2))
