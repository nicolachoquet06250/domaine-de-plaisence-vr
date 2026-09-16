import bpy,json
print(json.dumps({'version':bpy.app.version_string,'scene':bpy.context.scene.name,'hairOperator':hasattr(bpy.ops.object,'particle_system_add'),'particleSettings':hasattr(bpy.data,'particles'),'sourceReady':hasattr(bpy,'_natural_source'),'naturalReady':hasattr(bpy,'_natural_models')}))
