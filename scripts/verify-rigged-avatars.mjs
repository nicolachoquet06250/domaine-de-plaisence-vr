/** Offline verification of the exported GLBs, plus the SDK's actual skeleton clone API.
 * Run: node scripts/verify-rigged-avatars.mjs [optional-output-json]
 * Geometry/skin/animation data is decoded directly; this needs no WebGL renderer or server.
 */
import assert from 'node:assert/strict';
import {readFileSync, writeFileSync, mkdirSync} from 'node:fs';
import {dirname, resolve} from 'node:path';
import {
  AnimationClip, AnimationMixer, AssetManager, Bone, Box3, BufferGeometry, CacheManager,
  Float32BufferAttribute, Group, InterpolateDiscrete, LoopOnce, Matrix4, MeshBasicMaterial,
  QuaternionKeyframeTrack, Skeleton, SkinnedMesh, Uint16BufferAttribute, Vector3,
  VectorKeyframeTrack,
} from '@iwsdk/core';

const component = {
  5120: {bytes:1,read:'readInt8',max:127,signed:true}, 5121:{bytes:1,read:'readUInt8',max:255},
  5122: {bytes:2,read:'readInt16LE',max:32767,signed:true}, 5123:{bytes:2,read:'readUInt16LE',max:65535},
  5125: {bytes:4,read:'readUInt32LE',max:4294967295}, 5126:{bytes:4,read:'readFloatLE'},
};
const widths={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT4:16};
const report={assets:{},checks:[],decoder:'glTF buffers reconstructed with core types; AssetManager.getGLTF clone API exercised directly'};

function parseGLB(path) {
  const file=readFileSync(path);assert.equal(file.readUInt32LE(0),0x46546c67,'GLB magic');
  assert.equal(file.readUInt32LE(4),2);assert.equal(file.readUInt32LE(8),file.length);
  let json,bin;
  for(let offset=12;offset<file.length;) {
    const length=file.readUInt32LE(offset),kind=file.readUInt32LE(offset+4);
    assert.ok(offset+8+length<=file.length,'valid chunk length');
    const chunk=file.subarray(offset+8,offset+8+length);
    if(kind===0x4e4f534a)json=JSON.parse(chunk.toString('utf8'));
    if(kind===0x004e4942)bin=chunk;
    offset+=8+length;
  }
  assert.ok(json&&bin,'JSON and BIN chunks');
  assert.ok(json.buffers.every(b=>!b.uri),'embedded buffers');
  assert.ok((json.images??[]).every(image=>image.bufferView!==undefined),'embedded textures');
  const decoded=new Map();
  function accessor(id) {
    if(decoded.has(id))return decoded.get(id);
    const a=json.accessors[id];assert.ok(a,`accessor ${id}`);
    const v=json.bufferViews[a.bufferView],c=component[a.componentType],width=widths[a.type];
    assert.ok(c&&width&&(v||a.sparse),'supported accessor encoding');
    const stride=v?.byteStride??width*c.bytes,offset=(v?.byteOffset??0)+(a.byteOffset??0),values=Array(a.count*width).fill(0);
    if(v)assert.ok((a.byteOffset??0)+(a.count-1)*stride+width*c.bytes<=v.byteLength,'accessor fits its view');
    if(v)for(let i=0;i<a.count;i++)for(let j=0;j<width;j++) values[i*width+j]=bin[c.read](offset+i*stride+j*c.bytes);
    if(a.sparse) {
      const s=a.sparse,ic=component[s.indices.componentType],iv=json.bufferViews[s.indices.bufferView],sv=json.bufferViews[s.values.bufferView];
      const io=(iv.byteOffset??0)+(s.indices.byteOffset??0),so=(sv.byteOffset??0)+(s.values.byteOffset??0);
      assert.ok((s.indices.byteOffset??0)+s.count*ic.bytes<=iv.byteLength);
      assert.ok((s.values.byteOffset??0)+s.count*width*c.bytes<=sv.byteLength);
      let previous=-1;
      for(let i=0;i<s.count;i++) {
        const index=bin[ic.read](io+i*ic.bytes);assert.ok(index>previous&&index<a.count);previous=index;
        for(let j=0;j<width;j++)values[index*width+j]=bin[c.read](so+(i*width+j)*c.bytes);
      }
    }
    for(let i=0;i<values.length;i++) {
      let value=values[i];
      if(a.normalized&&c.max)value=Math.max(c.signed?-1:0,value/c.max);
      assert.ok(Number.isFinite(value),'finite accessor value');values[i]=value;
    }
    const result={values,count:a.count,width};decoded.set(id,result);return result;
  }
  return {json,file,accessor};
}

function reconstruct(data) {
  const {json,accessor}=data;
  const jointIds=new Set(json.skins.flatMap(s=>s.joints));
  const objects=json.nodes.map((node,i)=>{
    const object=jointIds.has(i)?new Bone():new Group();object.name=`AvatarNode_${i}`;
    if(node.matrix)new Matrix4().fromArray(node.matrix).decompose(object.position,object.quaternion,object.scale);
    else {
      if(node.translation)object.position.fromArray(node.translation);
      if(node.rotation)object.quaternion.fromArray(node.rotation);
      if(node.scale)object.scale.fromArray(node.scale);
    }
    return object;
  });
  json.nodes.forEach((node,i)=>{for(const child of node.children??[])objects[i].add(objects[child]);});
  const scene=new Group();for(const index of json.scenes[json.scene??0].nodes)scene.add(objects[index]);
  scene.updateMatrixWorld(true);
  const skeletons=json.skins.map(skin=>{
    const inverses=skin.inverseBindMatrices===undefined?undefined:accessor(skin.inverseBindMatrices);
    if(inverses)assert.equal(inverses.count,skin.joints.length);
    return new Skeleton(skin.joints.map(index=>objects[index]),skin.joints.map((_,i)=>inverses?new Matrix4().fromArray(inverses.values,i*16):new Matrix4()));
  });
  const material=new MeshBasicMaterial(),meshes=[];
  json.nodes.forEach((node,i)=>{
    if(node.mesh===undefined||node.skin===undefined)return;
    for(const primitive of json.meshes[node.mesh].primitives) {
      const geometry=new BufferGeometry();
      geometry.setAttribute('position',new Float32BufferAttribute(accessor(primitive.attributes.POSITION).values,3));
      geometry.setAttribute('skinIndex',new Uint16BufferAttribute(accessor(primitive.attributes.JOINTS_0).values,4));
      geometry.setAttribute('skinWeight',new Float32BufferAttribute(accessor(primitive.attributes.WEIGHTS_0).values,4));
      if(primitive.indices!==undefined)geometry.setIndex(accessor(primitive.indices).values);
      if(primitive.targets) {
        geometry.morphTargetsRelative=true;
        geometry.morphAttributes.position=primitive.targets.map(target=>new Float32BufferAttribute(accessor(target.POSITION).values,3));
      }
      const mesh=new SkinnedMesh(geometry,material);objects[i].add(mesh);
      mesh.bind(skeletons[node.skin],new Matrix4());meshes.push(mesh);
    }
  });
  const animations=json.animations.map(animation=>new AnimationClip(animation.name,-1,animation.channels.map(channel=>{
    const sampler=animation.samplers[channel.sampler],times=accessor(sampler.input).values,values=accessor(sampler.output).values;
    assert.ok(['LINEAR','STEP'].includes(sampler.interpolation??'LINEAR'),'export sampled LINEAR/STEP tracks for this verifier');
    const path=channel.target.path;
    assert.ok(['translation','rotation','scale'].includes(path),'skeletal TRS channels');
    const name=`${objects[channel.target.node].name}.${path==='translation'?'position':path==='rotation'?'quaternion':'scale'}`;
    const track=path==='rotation'?new QuaternionKeyframeTrack(name,times,values):new VectorKeyframeTrack(name,times,values);
    if(sampler.interpolation==='STEP')track.setInterpolation(InterpolateDiscrete);
    return track;
  })));
  scene.updateMatrixWorld(true);for(const skeleton of skeletons)skeleton.update();
  return {scene,scenes:[scene],animations,meshes};
}

function sampleRig(gltf) {
  gltf.scene.updateMatrixWorld(true);
  const bones=[],vertices=[],v=new Vector3();
  gltf.scene.traverse(object=>{
    if(object.isBone){object.getWorldPosition(v);bones.push(...v.toArray());}
    if(object.isSkinnedMesh){
      object.skeleton.update();
      const positions=object.geometry.getAttribute('position');
      // Deterministic distributed samples across every skinned primitive.
      const stride=Math.max(1,Math.floor(positions.count/192));
      for(let i=0;i<positions.count;i+=stride){
        v.fromBufferAttribute(positions,i);object.applyBoneTransform(i,v);v.applyMatrix4(object.matrixWorld);vertices.push(...v.toArray());
      }
    }
  });
  return {bones,vertices};
}
function displacement(a,b) {
  assert.equal(a.length,b.length);let max=0;
  for(let i=0;i<a.length;i+=3)max=Math.max(max,Math.hypot(a[i]-b[i],a[i+1]-b[i+1],a[i+2]-b[i+2]));
  return max;
}

for(const id of ['courtMale','courtFemale']) {
  const data=parseGLB(`public/gltf/avatars/${id}.glb`),{json,accessor,file}=data;
  assert.ok(json.skins?.length,`${id} has a skin`);
  assert.ok(['Idle','Walking','StrafeLeft','StrafeRight'].every(name=>json.animations?.some(a=>a.name===name)),`${id}: all four locomotion clips`);
  let vertices=0,triangles=0,skinnedPrimitives=0,maxWeightError=0;
  const influencedJoints=new Set();
  for(const node of json.nodes) {
    if(node.mesh===undefined)continue;
    if(node.extras?.hairDynamics) {
      const groom=node.extras.hairDynamics;
      assert.equal(groom.version,1);assert.equal(groom.gravity,9.81);
      assert.ok(groom.pointsPerStrand>=3&&groom.points.length%groom.pointsPerStrand===0);
      assert.ok(groom.points.every(p=>p.length===3&&p.every(Number.isFinite)));
      for(const primitive of json.meshes[node.mesh].primitives) {
        const bindings=accessor(primitive.attributes._HAIR_PARTICLE);
        assert.equal(bindings.count,accessor(primitive.attributes.POSITION).count);
        assert.ok(bindings.values.every(i=>Number.isInteger(i)&&i>=0&&i<groom.points.length));
      }
    }
    for(const p of json.meshes[node.mesh].primitives) {
      assert.ok(p.mode===undefined||p.mode===4,'triangles');
      const positions=accessor(p.attributes.POSITION);vertices+=positions.count;
      triangles+=(p.indices===undefined?positions.count:accessor(p.indices).count)/3;
      if(node.skin===undefined)continue;
      const skin=json.skins[node.skin],joints=accessor(p.attributes.JOINTS_0),weights=accessor(p.attributes.WEIGHTS_0);
      assert.equal(joints.width,4);assert.equal(weights.width,4);assert.equal(joints.count,positions.count);assert.equal(weights.count,positions.count);
      assert.equal(p.attributes.JOINTS_1,undefined,'at most four influences per vertex');
      skinnedPrimitives++;
      for(let i=0;i<positions.count;i++) {
        let sum=0;
        for(let j=0;j<4;j++) {
          const index=joints.values[i*4+j],weight=weights.values[i*4+j];
          assert.ok(Number.isInteger(index)&&index>=0&&index<skin.joints.length,'joint index in skin');
          assert.ok(weight>=0&&weight<=1.00001,'valid bone weight');sum+=weight;
          if(weight>.001)influencedJoints.add(skin.joints[index]);
        }
        maxWeightError=Math.max(maxWeightError,Math.abs(sum-1));
      }
    }
  }
  assert.ok(skinnedPrimitives>0&&influencedJoints.size>=8,'body vertices weighted to a genuine articulated skeleton');
  assert.ok(maxWeightError<.002,'normalized skin weights');
  const visemes={};
  for(const mesh of json.meshes) {
    const names=mesh.extras?.targetNames;if(!names)continue;
    assert.equal(names.length,15,'fifteen exported mouth shapes');
    for(const [i,name] of names.entries()) {
      assert.ok(name.startsWith('viseme_'),'named mouth shape');
      let motion=0;
      for(const primitive of mesh.primitives) {
        assert.equal(primitive.targets.length,15);
        const base=accessor(primitive.attributes.POSITION),delta=accessor(primitive.targets[i].POSITION);
        assert.equal(delta.count,base.count,'morph matches base vertex count');
        motion=Math.max(motion,...delta.values.map(Math.abs));
      }
      assert.ok(motion<.1,'mouth stays within a human-scale facial region');
      if(name==='viseme_sil')assert.ok(motion<.0001,'silence preserves the neutral facial geometry');
      if(name!=='viseme_sil')assert.ok(motion>.0001,`${name} has a visible deformation`);
      visemes[name]=Math.max(visemes[name]??0,motion);
    }
  }
  assert.equal(Object.keys(visemes).length,15,'both avatars have all visemes');
  assert.ok(triangles<100000&&file.length<12_000_000,'anatomical avatar and strand geometry budget');
  const clips={};
  for(const name of ['Idle','Walking','StrafeLeft','StrafeRight']) {
    const animation=json.animations.find(a=>a.name===name);let movingJointTracks=0,maxLoopError=0;
    for(const channel of animation.channels) {
      const sampler=animation.samplers[channel.sampler],input=accessor(sampler.input),output=accessor(sampler.output);
      assert.equal(output.count,input.count,'one sampled TRS value per animation time');
      assert.ok(input.count>=2&&input.values.at(-1)>input.values[0],'nonempty animation timeline');
      assert.equal(input.values[0],0,'clip starts at time zero');
      for(let i=1;i<input.count;i++)assert.ok(input.values[i]>input.values[i-1],'strictly increasing sample times');
      const width=output.width,first=output.values.slice(0,width),last=output.values.slice(-width);
      let error;
      if(channel.target.path==='rotation') {
        for(let i=0;i<output.values.length;i+=4)assert.ok(Math.abs(Math.hypot(...output.values.slice(i,i+4))-1)<.002,'normalized animation quaternion');
        const dot=Math.abs(first.reduce((sum,v,i)=>sum+v*last[i],0));error=2*Math.acos(Math.min(1,dot));
      } else error=Math.hypot(...first.map((v,i)=>v-last[i]));
      maxLoopError=Math.max(maxLoopError,error);assert.ok(error<.003,`${id}/${name} closes its ${channel.target.path} loop`);
      if(influencedJoints.has(channel.target.node)&&output.values.some((v,i)=>Math.abs(v-first[i%width])>.0001))movingJointTracks++;
    }
    assert.ok(movingJointTracks>=(name==='Walking'?2:1),`${name} animates weighted joints`);
    clips[name]={movingJointTracks,maxLoopError};
  }

  const source=reconstruct(data),cacheKey=`verify-${id}`;
  CacheManager.setKeyToUrl(cacheKey,cacheKey);CacheManager.setAsset(cacheKey,source);
  const one=AssetManager.getGLTF(cacheKey),two=AssetManager.getGLTF(cacheKey);
  assert.ok(one&&two&&one.scene!==two.scene&&one.scene!==source.scene);
  const aMeshes=[],bMeshes=[];
  one.scene.traverse(o=>{if(o.isSkinnedMesh)aMeshes.push(o);});two.scene.traverse(o=>{if(o.isSkinnedMesh)bMeshes.push(o);});
  aMeshes.forEach((a,i)=>{
    const b=bMeshes[i];assert.notEqual(a.skeleton,b.skeleton);assert.equal(a.geometry,b.geometry);assert.equal(a.material,b.material);
    if(a.morphTargetInfluences) {
      assert.notEqual(a.morphTargetInfluences,b.morphTargetInfluences,'mouth weights belong to each visitor');
      a.morphTargetInfluences[0]=.5;assert.equal(b.morphTargetInfluences[0],0);a.morphTargetInfluences[0]=0;
    }
    a.skeleton.bones.forEach((bone,j)=>assert.notEqual(bone,b.skeleton.bones[j],'clones have independent bones'));
  });
  const bounds=new Box3().setFromObject(one.scene),height=bounds.max.y-bounds.min.y;
  assert.ok(height>1.3&&height<2.3,`human-scale height: ${height}`);
  assert.ok(Math.abs(bounds.min.y)<.10,`feet at origin: ${bounds.min.y}`);
  const neighbourBefore=sampleRig(two),sourceBefore=sampleRig(source);
  for(const name of ['Idle','Walking','StrafeLeft','StrafeRight']) {
    const clip=one.animations.find(a=>a.name===name),mixer=new AnimationMixer(one.scene);
    const action=mixer.clipAction(clip).setLoop(LoopOnce,1);action.clampWhenFinished=true;action.play();
    mixer.setTime(0);const start=sampleRig(one);let boneMotion=0,vertexMotion=0;
    for(let i=1;i<=8;i++) {
      mixer.setTime(clip.duration*i/8);const sample=sampleRig(one);
      boneMotion=Math.max(boneMotion,displacement(start.bones,sample.bones));
      vertexMotion=Math.max(vertexMotion,displacement(start.vertices,sample.vertices));
    }
    assert.ok(boneMotion>(name==='Walking'?.015:.0005),`${name} moves bones: ${boneMotion}m`);
    assert.ok(vertexMotion>(name==='Walking'?.015:.0005),`${name} deforms skinned vertices: ${vertexMotion}m`);
    assert.ok(displacement(neighbourBefore.vertices,sampleRig(two).vertices)<1e-8,'neighbour clone stays unchanged');
    assert.ok(displacement(sourceBefore.vertices,sampleRig(source).vertices)<1e-8,'cached prototype stays unchanged');
    clips[name]={...clips[name],duration:clip.duration,maxBoneMotion:boneMotion,maxSkinnedVertexMotion:vertexMotion};
    mixer.stopAllAction();mixer.uncacheRoot(one.scene);
  }
  CacheManager.deleteAsset(cacheKey);
  report.assets[id]={bytes:file.length,vertices,triangles,skins:json.skins.length,weightedJoints:influencedJoints.size,
    skinnedPrimitives,maxWeightError,visemes,bounds:{min:bounds.min.toArray(),max:bounds.max.toArray()},clips};
}
report.checks=['embedded GLBs','normalized joint weights','articulated weighted skeletons','Idle, Walking, StrafeLeft and StrafeRight loop closure',
  'human scale and feet origin','15 finite named mouth morphs per avatar','actual animated bone and vertex displacement','SDK skeleton and mouth clone independence','prototype and material sharing'];
const output=resolve(process.argv[2]??'artifacts/avatars/verification.json');mkdirSync(dirname(output),{recursive:true});
writeFileSync(output,JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
