# Extend short water clips throughout the four-second export interval.
for group in ['water','centralJet','lateralJet']:
    for obj in groups[group]:
        sk=obj.data.shape_keys
        keys=list(sk.key_blocks)[1:]
        duration=4 if group=='water' else 1
        sk.animation_data_clear()
        count=len(keys)
        for i,key in enumerate(keys):
            for step in range(int(count*4/duration)+1):
                key.value=1 if step%count==i else 0
                key.keyframe_insert(data_path='value',frame=1+step*duration*24/count)
        action=sk.animation_data.action; action.name=obj.name+'_Loop'
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for point in curve.keyframe_points: point.interpolation='LINEAR'
# Fresnel/specular cues with standard glTF materials and bounded transparency.
for mat,alpha,color in [(streammat,.66,(.56,.70,.69)),(watermat,.90,(.10,.25,.23))]:
    p=mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Alpha'].default_value=alpha
    mat.surface_render_method='DITHERED'
scene.frame_set(1)
print('Continuous four-second clips; translucent water materials.')
