for m in leaf_mats:
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');tex=next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE')
 clip=m.node_tree.nodes.new('ShaderNodeMath');clip.operation='GREATER_THAN';clip.inputs[1].default_value=.45
 m.node_tree.links.new(tex.outputs['Alpha'],clip.inputs[0]);m.node_tree.links.new(clip.outputs[0],p.inputs['Alpha'])
for (variant,lod),objects in models.items():
 export(f'oak{variant+1}'+('Far' if lod else ''),objects)
 for obj in objects:obj.hide_set(True);obj.hide_render=True
export('forest',forest)
estate.location-=Vector((100,95,0))
print('Estate mesh repaired:',estate.data.validate(verbose=True));estate.data.update()
export('estateExterior',[estate]);estate.location+=Vector((100,95,0))
bpy.data.libraries.write(str(EVID/'accueil-paysage.blend'),{scene},fake_user=True,compress=True)
(EVID/'asset-stats.json').write_text(json.dumps({'assets':stats,'trees':len(placements),'estateOffset':spec['offset'],'sourcePlacements':len(spec['placements'])},indent=2))
print('Final exports and Blender source saved')
