groups['water'][0].name='Basin_Water_Surface'
scene.frame_start=0; scene.frame_end=96
for group in ['water','centralJet','lateralJet']:
    for obj in groups[group]:
        action=obj.data.shape_keys.animation_data.action
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:
                            key.co.x-=1; key.handle_left.x-=1; key.handle_right.x-=1
scene.frame_set(0)
print('Distinct water mesh binding and exact four-second animation interval.')
