import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
import * as core from '@iwsdk/core';
const api={};
vm.runInNewContext(ts.transpileModule(readFileSync(new URL('../src/court-avatar-ik.ts',import.meta.url),'utf8'),{
  compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022},
}).outputText,{exports:api,require:()=>core});

function rig() {
  const root=new core.Group(), model=new core.Group();root.add(model);
  for(const [label,x] of [['L',-.2],['R',.2]]) { // Deliberately reversed labels: anatomical positions must win.
    const upper=new core.Bone(),forearm=new core.Bone(),hand=new core.Bone();
    upper.name=`UpperArm.${label}`;forearm.name=`Forearm.${label}`;hand.name=`Hand.${label}`;
    upper.position.set(x,1.4,0);forearm.position.set(0,-.3,0);hand.position.set(0,-.27,0);
    model.add(upper);upper.add(forearm);forearm.add(hand);
  }
  return {root,model,...api.createCourtArmIK(model)};
}
function target(root,point) {return {position:root.localToWorld(new core.Vector3(...point)),quaternion:new core.Quaternion(),tracked:true};}

test('anatomical side is determined by geometry, with independent tracked arms',()=>{
  const r=rig();assert.equal(r.left.upper.name,'UpperArm.R');assert.equal(r.right.upper.name,'UpperArm.L');
  const before=r.right.upper.quaternion.clone();r.left.solve(target(r.root,[.42,1.14,.23]));
  assert.ok(r.left.error<1e-6);assert.ok(r.right.upper.quaternion.equals(before));
  const position=r.left.wristPosition.clone();r.left.solve({tracked:false});assert.ok(position.equals(r.left.wristPosition));
});
test('reachable world targets preserve limb lengths under translated, yawed and scaled roots',()=>{
  const r=rig();r.root.position.set(5,.8,-12);r.root.rotation.y=1.2;r.root.scale.setScalar(.95);
  const handTarget=target(r.root,[.43,1.13,.23]);r.left.solve(handTarget);
  assert.ok(r.left.error<1e-6,`reach error ${r.left.error}`);
  const a=new core.Vector3(),b=new core.Vector3(),c=new core.Vector3();
  r.left.upper.getWorldPosition(a);r.left.forearm.getWorldPosition(b);r.left.hand.getWorldPosition(c);
  assert.ok(Math.abs(a.distanceTo(b)-.3*.95)<1e-6);assert.ok(Math.abs(b.distanceTo(c)-.27*.95)<1e-6);
});
test('unreachable targets clamp extension, folding, shoulder swing and wrist rotation',()=>{
  for(const point of [[.2,1.4,3],[.2,1.4,0],[.2,3,0]]) {
    const r=rig(),handTarget=target(r.root,point);
    handTarget.quaternion.setFromEuler(new core.Euler(2,2,2));r.left.solve(handTarget);
    assert.ok(r.left.elbowFlex>=5-1e-6&&r.left.elbowFlex<=145+1e-6);
    assert.ok(r.left.shoulderSwing<=155+1e-6);assert.ok(r.left.wristSwing<=70+1e-6);assert.ok(Math.abs(r.left.wristTwist)<=80+1e-6);
    assert.ok(Math.abs(r.left.forearmTwist)<=90+1e-6);
    assert.ok(Number.isFinite(r.left.error));
    const shoulder=new core.Vector3();r.left.upper.getWorldPosition(shoulder);
    assert.ok(shoulder.distanceTo(r.left.wristPosition)<.571,'arm never stretches');
  }
});

function exportedRig(gender) {
    const buffer=readFileSync(new URL(`../public/gltf/avatars/court${gender}.glb`,import.meta.url));
    const json=JSON.parse(buffer.subarray(20,20+buffer.readUInt32LE(12)).toString('utf8'));
    const joints=new Set(json.skins.flatMap(skin=>skin.joints));
    const nodes=json.nodes.map((node,index)=>{
      const object=joints.has(index)?new core.Bone():new core.Group();object.name=core.PropertyBinding.sanitizeNodeName(node.name??'');
      if(node.matrix)new core.Matrix4().fromArray(node.matrix).decompose(object.position,object.quaternion,object.scale);
      else {if(node.translation)object.position.fromArray(node.translation);if(node.rotation)object.quaternion.fromArray(node.rotation);if(node.scale)object.scale.fromArray(node.scale);}
      object.userData=node.extras??{};return object;
    });
    json.nodes.forEach((node,index)=>{for(const child of node.children??[])nodes[index].add(nodes[child]);});
    const root=new core.Group(),model=new core.Group();root.add(model);
    for(const index of json.scenes[json.scene??0].nodes)model.add(nodes[index]);
    return {root,model,json,nodes,buffer,...api.createCourtArmIK(model)};
}

function accessorValues(rig,index) {
  const a=rig.json.accessors[index],view=rig.json.bufferViews[a.bufferView];
  const arity={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT4:16}[a.type];
  const [bytes,read,maximum]={5121:[1,'readUInt8',255],5123:[2,'readUInt16LE',65535],5125:[4,'readUInt32LE',4294967295],5126:[4,'readFloatLE',1]}[a.componentType];
  const start=28+rig.buffer.readUInt32LE(12)+(view.byteOffset??0)+(a.byteOffset??0),stride=view.byteStride??bytes*arity;
  return Array.from({length:a.count},(_,i)=>Array.from({length:arity},(_,j)=>rig.buffer[read](start+i*stride+j*bytes)/(a.normalized?maximum:1)));
}

function actualHandVertices(rig,hand) {
  const result=[];
  for(const node of rig.json.nodes) {
    if(node.mesh===undefined||node.skin===undefined||!/Peau/i.test(node.name))continue;
    const skin=rig.json.skins[node.skin],handJoint=skin.joints.indexOf(rig.nodes.indexOf(hand));
    if(handJoint<0)continue;
    const inverses=accessorValues(rig,skin.inverseBindMatrices).map(values=>new core.Matrix4().fromArray(values));
    for(const primitive of rig.json.meshes[node.mesh].primitives) {
      const positions=accessorValues(rig,primitive.attributes.POSITION),joints=accessorValues(rig,primitive.attributes.JOINTS_0),weights=accessorValues(rig,primitive.attributes.WEIGHTS_0);
      for(let i=0;i<positions.length;i++) {
        if(joints[i].reduce((total,joint,k)=>total+(joint===handJoint?weights[i][k]:0),0)<.99)continue;
        const influences=joints[i].map((joint,k)=>({bone:rig.nodes[skin.joints[joint]],inverse:inverses[joint],weight:weights[i][k]})).filter(influence=>influence.weight>0);
        const vertex=new core.Vector3(...positions[i]);
        const skinPosition=()=>influences.reduce((sum,influence)=>sum.addScaledVector(vertex.clone().applyMatrix4(influence.inverse).applyMatrix4(influence.bone.matrixWorld),influence.weight),new core.Vector3());
        result.push({rest:skinPosition(),skinPosition});
      }
    }
  }
  return result;
}

test('both exported Blender rigs accept world grip targets without stretching',()=>{
  for(const gender of ['Male','Female']) {
    const {root,left,right}=exportedRig(gender);const arms={left,right};assert.ok(arms.left&&arms.right,`${gender} has both arm chains`);
    root.position.set(-4,1,3);root.rotation.y=-.7;root.scale.setScalar(1.1);root.updateMatrixWorld(true);
    for(const [side,arm] of [['left',arms.left],['right',arms.right]]) {
      const shoulder=new core.Vector3(),elbow=new core.Vector3(),wrist=new core.Vector3();
      arm.upper.getWorldPosition(shoulder);arm.forearm.getWorldPosition(elbow);arm.hand.getWorldPosition(wrist);
      const a=shoulder.distanceTo(elbow),b=elbow.distanceTo(wrist);
      const offset=new core.Vector3(side==='left'?.14:-.14,-.24,.2).applyQuaternion(root.quaternion);
      const grip=root.quaternion.clone().multiply(new core.Quaternion().setFromEuler(new core.Euler(Math.PI/2,Math.PI,0,'YXZ')));
      arm.solve({position:shoulder.clone().add(offset),quaternion:grip,tracked:true});
      assert.ok(arm.error<1e-5,`${gender} ${side} reachable error ${arm.error}`);
      arm.forearm.getWorldPosition(elbow);arm.hand.getWorldPosition(wrist);
      assert.ok(Math.abs(shoulder.distanceTo(elbow)-a)<1e-5);assert.ok(Math.abs(elbow.distanceTo(wrist)-b)<1e-5);
    }
  }
});

test('exported bind frames match WebXR grip thumb and finger axes for both hands and body yaws',()=>{
  for(const gender of ['Male','Female']) for(const yaw of [-Math.PI,-.8,0,.8,Math.PI]) for(const controllerRoll of [-.35,0,.35]) for(const controllerPitch of [-.2,0,.2]) {
    const {root,left,right}=exportedRig(gender);
    const localAnatomy=[left,right].map(arm=>{
      const bind=arm.hand.getWorldQuaternion(new core.Quaternion()).invert();
      return {finger:new core.Vector3(0,-1,0).applyQuaternion(bind),thumb:new core.Vector3(0,0,1).applyQuaternion(bind)};
    });
    root.position.set(3,.5,-4);root.rotation.y=yaw;root.scale.setScalar(.95);root.updateMatrixWorld(true);
    const grip=root.quaternion.clone().multiply(new core.Quaternion().setFromAxisAngle(new core.Vector3(0,1,0),Math.PI))
      .multiply(new core.Quaternion().setFromEuler(new core.Euler(Math.PI / 2 + controllerPitch,0,controllerRoll)));
    const expectedFinger=new core.Vector3(0,-1,0).applyQuaternion(grip),expectedThumb=new core.Vector3(0,0,-1).applyQuaternion(grip);
    for(const [index,arm] of [left,right].entries()) {
      const shoulder=arm.upper.getWorldPosition(new core.Vector3());
      const position=shoulder.add(new core.Vector3(index===0?.10:-.10,-.25,.27).multiplyScalar(.95).applyQuaternion(root.quaternion));
      for(let frame=0;frame<8;frame++)arm.solve({position,quaternion:grip,tracked:true});
      const handQ=arm.hand.getWorldQuaternion(new core.Quaternion());
      const finger=localAnatomy[index].finger.clone().applyQuaternion(handQ),thumb=localAnatomy[index].thumb.clone().applyQuaternion(handQ);
      const label=`${gender} ${index===0?'left':'right'} yaw=${yaw} roll=${controllerRoll} pitch=${controllerPitch}`;
      assert.ok(finger.angleTo(expectedFinger)<.001,`${label}: fingers error ${finger.angleTo(expectedFinger)*180/Math.PI}°`);
      assert.ok(thumb.angleTo(expectedThumb)<.001,`${label}: thumb error ${thumb.angleTo(expectedThumb)*180/Math.PI}°`);
      assert.ok(arm.error<1e-5,`${label}: wrist position ${arm.error}`);
      assert.ok(Math.abs(arm.forearmTwist)<=90+1e-6&&Math.abs(arm.wristTwist)<=80+1e-6&&arm.wristSwing<=70+1e-6);
    }
  }
});

test('exported arms preserve measured lengths and anatomical bend limits for extreme controller poses',()=>{
  for(const gender of ['Male','Female']) for(const side of [1,-1]) for(const offset of [[0,3,0],[0,0,3],[0,0,0],[-side*2,0,0]]) {
    const rig=exportedRig(gender),arm=side===1?rig.left:rig.right;
    const shoulder=arm.upper.getWorldPosition(new core.Vector3()),elbow=arm.forearm.getWorldPosition(new core.Vector3()),wrist=arm.hand.getWorldPosition(new core.Vector3());
    const upperLength=shoulder.distanceTo(elbow),lowerLength=elbow.distanceTo(wrist),restAxis=elbow.clone().sub(shoulder).normalize();
    arm.solve({position:shoulder.clone().add(new core.Vector3(...offset)),quaternion:new core.Quaternion().setFromEuler(new core.Euler(2,-2,2)),tracked:true});
    arm.forearm.getWorldPosition(elbow);arm.hand.getWorldPosition(wrist);
    const upperAxis=elbow.clone().sub(shoulder).normalize(),lowerAxis=wrist.clone().sub(elbow).normalize();
    const measuredFlex=upperAxis.angleTo(lowerAxis)*180/Math.PI,measuredShoulder=upperAxis.angleTo(restAxis)*180/Math.PI;
    assert.ok(Math.abs(shoulder.distanceTo(elbow)-upperLength)<1e-6&&Math.abs(elbow.distanceTo(wrist)-lowerLength)<1e-6,'actual exported limb lengths stay fixed');
    // GLB Float32 transforms introduce a few ten-thousandths of a degree of roundoff.
    assert.ok(measuredFlex>=5-1e-3&&measuredFlex<=145+1e-3,`actual elbow flex ${measuredFlex}`);
    assert.ok(measuredShoulder<=155+1e-3,`actual shoulder swing ${measuredShoulder}`);
    assert.ok(arm.wristSwing<=70+1e-6&&Math.abs(arm.wristTwist)<=80+1e-6&&Math.abs(arm.forearmTwist)<=90+1e-6);
  }
});

test('real skinned fingertip vertices match the WebXR grip frame after XR posing',()=>{
  for(const gender of ['Male','Female']) for(const yaw of [-Math.PI,0,Math.PI]) {
    const rig=exportedRig(gender),{root,left,right}=rig;
    for(const [side,arm] of [[1,left],[-1,right]]) {
      const anatomy=arm.hand.userData.handAnatomy;assert.ok(anatomy,`${gender}: anatomical landmarks exported`);
      const vertices=actualHandVertices(rig,arm.hand);assert.ok(vertices.length>100,`${gender}: actual skin vertices weighted to hand`);
      const landmarks={};
      for(const name of ['thumbTip','middleTip','indexKnuckle','dorsalKnuckle']) {
        const landmark=new core.Vector3(...anatomy[name]);
        const nearest=vertices.reduce((best,vertex)=>vertex.rest.distanceToSquared(landmark)<best.rest.distanceToSquared(landmark)?vertex:best);
        const distance=nearest.rest.distanceTo(landmark);
        assert.ok(distance<.008*arm.hand.userData.xrGrip.uniformHandScale,`${gender} ${side} ${name}: landmark-to-surface distance ${distance} m`);
        landmarks[name]=nearest;
      }
      assert.ok(landmarks.thumbTip.rest.z-landmarks.indexKnuckle.rest.z>.030,`${gender}: thumb sits on radial +Z side of index`);
      const wrist=arm.hand.getWorldPosition(new core.Vector3());
      assert.ok(landmarks.middleTip.rest.y<wrist.y-.14,`${gender}: fingers point down in the rest mesh`);
      // Pose this exact GLB skin, including inverse bind matrices, under a yawed/scaled body.
      root.position.set(3,.5,-4);root.rotation.y=yaw;root.scale.setScalar(.95);root.updateMatrixWorld(true);
      const grip=root.quaternion.clone().multiply(new core.Quaternion().setFromEuler(new core.Euler(0,Math.PI,0)))
        .multiply(new core.Quaternion().setFromEuler(new core.Euler(Math.PI / 2 + .15,0,side*.25)));
      const shoulder=arm.upper.getWorldPosition(new core.Vector3());
      const position=shoulder.add(new core.Vector3(side*.10,-.25,.27).multiplyScalar(.95).applyQuaternion(root.quaternion));
      arm.solve({position,quaternion:grip,tracked:true});
      const finger=landmarks.middleTip.skinPosition().sub(arm.wristPosition).normalize();
      const expectedForward=new core.Vector3(0,-1,0).applyQuaternion(grip),expectedUp=new core.Vector3(0,0,-1).applyQuaternion(grip);
      assert.ok(finger.dot(expectedForward)>.97,`${gender} ${side}: real fingertips face controller forward`);
      const radial=landmarks.thumbTip.skinPosition().sub(landmarks.indexKnuckle.skinPosition());
      assert.ok(radial.dot(expectedUp)>.027,`${gender} ${side}: real thumb is above index, not inverted`);
      const dorsal=landmarks.dorsalKnuckle.skinPosition().sub(landmarks.indexKnuckle.skinPosition());
      assert.ok(side*dorsal.dot(new core.Vector3(1,0,0).applyQuaternion(grip))<-.003,`${gender} ${side}: mirrored dorsal surface faces outward`);
      assert.ok(arm.error<1e-5&&arm.wristSwing<=70+1e-6&&Math.abs(arm.wristTwist)<=80+1e-6&&Math.abs(arm.forearmTwist)<=90+1e-6);
      // Restore for the other hand's independent rest-surface measurement.
      root.position.set(0,0,0);root.rotation.set(0,0,0);root.scale.setScalar(1);root.updateMatrixWorld(true);
    }
  }
});

test('enlarged hands retain proportions and centre the grip inside the palm, not at the wrist',()=>{
  for(const gender of ['Male','Female']) {
    const rig=exportedRig(gender);
    for(const arm of [rig.left,rig.right]) {
      const {handAnatomy:a,xrGrip:g}=arm.hand.userData;
      assert.equal(g.uniformHandScale,1.18);
      const wrist=new core.Vector3(...a.wrist),middle=new core.Vector3(...a.middleTip);
      const originalLength=Math.hypot(.0055,.164,.021)*(gender==='Female'?.95:1);
      assert.ok(Math.abs(middle.distanceTo(wrist)/originalLength-1.18)<1e-5,'uniform anatomical length scale');
      assert.ok(new core.Vector3(...g.wristToGripModel).length()>.06,'palm grip is separated from wrist');
      const grip=new core.Quaternion().setFromEuler(new core.Euler(Math.PI/2,Math.PI,0,'YXZ'));
      const position=arm.upper.getWorldPosition(new core.Vector3()).add(new core.Vector3(arm.side*.1,-.25,.27));
      arm.solve({position,quaternion:grip,tracked:true});
      assert.ok(arm.gripPosition.distanceTo(position)<1e-5,'actual transformed palm anchor follows grip');
      assert.ok(arm.wristPosition.distanceTo(position)>.06,'wrist remains behind palm anchor');
    }
  }
});

test('Blender Walking swings opposite arms with bent elbows; sidestep clips have no arm swing',()=>{
  for(const gender of ['Male','Female']) {
    const rig=exportedRig(gender);
    const track=(clip,bone)=>{
      const animation=rig.json.animations.find(a=>a.name===clip);
      const channel=animation.channels.find(c=>c.target.path==='rotation'&&rig.json.nodes[c.target.node].name===bone);
      return accessorValues(rig,animation.samplers[channel.sampler].output).map(q=>new core.Quaternion(...q));
    };
    for(const suffix of ['L','R']) {
      const upper=track('Walking',`UpperArm.${suffix}`),fore=track('Walking',`Forearm.${suffix}`);
      assert.ok(Math.max(...upper.map(q=>q.angleTo(upper[0])))>.30,'visible shoulder swing');
      assert.ok(Math.max(...fore.map(q=>q.angleTo(fore[0])))>.06,'elbow flex varies during walking');
      for(const clip of ['StrafeLeft','StrafeRight']) for(const bone of [`UpperArm.${suffix}`,`Forearm.${suffix}`]) {
        const q=track(clip,bone);assert.ok(q.every(v=>v.angleTo(q[0])<.001),`${clip}: no arm swing`);
      }
    }
    const left=track('Walking','UpperArm.L'),right=track('Walking','UpperArm.R');
    assert.ok(Math.max(...left.map((q,i)=>q.angleTo(right[i])))>.60,'arms swing in opposition');
  }
});

