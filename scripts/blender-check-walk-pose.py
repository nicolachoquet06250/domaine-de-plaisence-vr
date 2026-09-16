import bpy,json
bpy.context.window.scene=rfscene
out=[]
for rig in [o for o in rfscene.objects if o.type=='ARMATURE']:
    for track in rig.animation_data.nla_tracks:track.mute=track.name!='Walking'
    for frame in [0,7,22]:
        rfscene.frame_set(frame)
        points={}
        for suffix in ['L','R']:
            points[suffix]=[(p.x,p.z,-p.y) for p in [rig.pose.bones['UpperArm.'+suffix].head,rig.pose.bones['Forearm.'+suffix].head,rig.pose.bones['Hand.'+suffix].head]]
        out.append({'rig':rig.name,'frame':frame,'pointsModel':points})
    for track in rig.animation_data.nla_tracks:track.mute=False
rfscene.frame_set(0)
print(json.dumps(out))
