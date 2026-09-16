# Match the five runtime door assemblies in the editable Blender scene.
bpy.context.window.scene=cscene
for suffix,x,z,floor,yaw in [('Salon ouest',-4.65,3.8,.64,-90),('Salon est',4.65,3.8,.64,90),('Galerie ouest',-4.65,3.8,5.04,-90),('Galerie est',4.65,3.8,5.04,90)]:
    assembly=bpy.data.objects.new('Portes '+suffix,None); cscene.collection.objects.link(assembly)
    assembly.location=(x,-z,floor); assembly.rotation_euler.z=math.radians(yaw)
    for side,asset in [(-1,'doorLeft'),(1,'doorRight')]:
        original,leaf=cobjects[asset]; hinge=original.copy(); hinge.name='Charniere '+suffix+str(side); cscene.collection.objects.link(hinge)
        hinge.parent=assembly; hinge.location=(side*1.6,0,0); hinge.scale=(1,1,1)
        panel=leaf.copy(); panel.name='Vantail '+suffix+str(side); cscene.collection.objects.link(panel); panel.parent=hinge
for name,x,y,energy in [('Vestibule',0,7.9,450),('Salon ouest',-10.6,3.54,180),('Salon est',10.6,3.54,180),('Galerie ouest',-10.6,7.94,180),('Galerie est',10.6,7.94,180)]:
    data=bpy.data.lights.new('Lustre '+name,'POINT'); data.energy=energy; data.color=(1,.80,.57); data.shadow_soft_size=.45
    lamp=bpy.data.objects.new('Lustre '+name,data); cscene.collection.objects.link(lamp); lamp.location=(x,0,y)
cscene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(CEVID/'chateau-plaisance.blend'),compress=True)
print('Editable castle saved with all five animated door pairs and interior lights')
