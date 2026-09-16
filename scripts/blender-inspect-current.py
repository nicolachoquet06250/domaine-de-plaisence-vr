import bpy,json
print(json.dumps({'scenes':[(s.name,len(s.objects)) for s in bpy.data.scenes],'file':bpy.data.filepath,'authoringKeys':list(globals().keys())[-25:]}))
