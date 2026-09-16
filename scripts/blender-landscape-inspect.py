import bpy, os
print('PID', os.getpid(), 'SCENES', list(bpy.data.scenes.keys()))
print('AUTHORING', sorted(bpy.__dict__.get('_estate_authoring', {}).keys()))
