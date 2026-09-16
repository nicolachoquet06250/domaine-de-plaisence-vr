"""Leaf sprig atlases and crossed curved crowns, authored locally in Blender."""
def sprig_material(index):
 n=512;pixels=np.zeros((n,n,4),dtype=np.float32);rng=random.Random(661)
 def polygon(points,color):
  points=np.array(points)*n
  lo=np.maximum(0,np.floor(points.min(axis=0)).astype(int));hi=np.minimum(n,np.ceil(points.max(axis=0)).astype(int)+1)
  if any(hi<=lo):return
  yy,xx=np.mgrid[lo[1]:hi[1],lo[0]:hi[0]];inside=np.zeros(xx.shape,dtype=bool)
  for a,b in zip(points,np.roll(points,1,axis=0)):
   inside^=((a[1]>yy)!=(b[1]>yy))&(xx<(b[0]-a[0])*(yy-a[1])/(b[1]-a[1]+1e-12)+a[0])
  noise=.87+.13*np.sin(xx*.6+yy*.24)
  region=pixels[lo[1]:hi[1],lo[0]:hi[0]]
  for c in range(3):region[:,:,c][inside]=color[c]*noise[inside]
  region[:,:,3][inside]=1
 # Lobed oak leaves, irregular spacing, small gaps between the sprigs.
 for j in range(210):
  angle=rng.random()*math.tau;rad=math.sqrt(rng.random())*.42
  cx=.5+math.cos(angle)*rad;cy=.5+math.sin(angle)*rad
  angle=rng.random()*math.tau;u=np.array([math.cos(angle),math.sin(angle)]);w=np.array([-u[1],u[0]])
  length=rng.uniform(.038,.079);width=length*.5;outline=[]
  for k in range(22):
   a=k*math.tau/22;lobes=1+.26*math.cos(a*8)
   outline.append(np.array([cx,cy])+u*math.cos(a)*length+w*math.sin(a)*width*lobes)
  tint=rng.uniform(.65,1.35);base=np.array([.30,.43,.105])*(.88+index*.1)*tint
  polygon(outline,base)
  polygon([np.array([cx,cy])-u*length*.8-w*.0014,np.array([cx,cy])+u*length*.8,np.array([cx,cy])-u*length*.8+w*.0014],base*1.22)
 img=bpy.data.images.new('Rameaux de chene alpha '+str(index),width=n,height=n,alpha=True);img.pixels.foreach_set(pixels.ravel());img.pack()
 m=material('Feuilles decoupees de chene '+str(index),(.3,.43,.105));p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img;m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);m.node_tree.links.new(tex.outputs['Alpha'],p.inputs['Alpha'])
 m.surface_render_method='DITHERED';m.alpha_threshold=.5;m.use_backface_culling=False
 return m

leaf_mats=[sprig_material(i) for i in range(3)]
for (variant,lod),objects in models.items():
 old=objects[1];data=old.data;H=[9,13,17][variant];rng=random.Random(250+variant);crowns=[]
 for branch in range(11):
  angle=branch*2.4+rng.uniform(-.2,.2);spread=H*rng.uniform(.20,.34);h=H*rng.uniform(.54,.82)
  crowns.append(((math.cos(angle)*spread,h,math.sin(angle)*spread),H*rng.uniform(.13,.21)))
 crowns.append(((0,H*.88,0),H*.17));v=[];f=[];uvs=[]
 rng=random.Random(410+variant)
 for center,rad in crowns:
  for j in range(9 if not lod else 6):
   angle=j*2.4+rng.uniform(-.4,.4);normal=Vector((math.cos(angle),rng.uniform(-.8,.8),math.sin(angle))).normalized()
   u=normal.cross(Vector((0,1,0))).normalized();w=normal.cross(u).normalized()
   c=Vector(center)+Vector((rng.uniform(-.4,.4),rng.uniform(-.3,.3),rng.uniform(-.4,.4)))*rad
   size=rad*rng.uniform(.85,1.3);off=len(v)
   # A bent card gives each leafy branch depth, with no blended transparency.
   for x,y in [(-1,-1),(1,-1),(1,1),(-1,1),(0,0)]:v.append(tuple(c+u*x*size+w*y*size*.78+normal*(.16*rad if x==0 else 0)))
   for k in range(4):f.append((off+4,off+k,off+(k+1)%4));uvs.extend([(0.5,.5),[(0,0),(1,0),(1,1),(0,1)][k],[(0,0),(1,0),(1,1),(0,1)][(k+1)%4]])
 asset=f'oak{variant+1}'+('Far' if lod else '')
 obj=mesh('newFoliage','Rameaux feuillus '+asset,v,f,leaf_mats[variant],False)
 obj.data.uv_layers.active.data.foreach_set('uv',[value for pair in uvs for value in pair]);objects[1]=obj
 bpy.data.objects.remove(old,do_unlink=True);export(asset,objects)
 for o in objects:o.hide_set(True);o.hide_render=True

# Replace only this generated forest, keeping the approved placement seed.
for obj in globals().get('forest',[]):bpy.data.objects.remove(obj,do_unlink=True)
print('Oak foliage updated')
