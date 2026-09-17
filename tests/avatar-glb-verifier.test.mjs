import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdirSync,mkdtempSync,writeFileSync,readFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,dirname,basename,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';

function makeGLB(mutation) {
  const views=[],accessors=[],chunks=[];let offset=0;
  function add(values,width,type=5126) {
    const array=type===5123?new Uint16Array(values):new Float32Array(values),raw=Buffer.from(array.buffer);
    const buffer=Buffer.alloc(Math.ceil(raw.length/4)*4);raw.copy(buffer);
    const view=views.length;views.push({buffer:0,byteOffset:offset,byteLength:raw.length});offset+=buffer.length;chunks.push(buffer);
    const index=accessors.length;accessors.push({bufferView:view,componentType:type,count:values.length/width,type:{1:'SCALAR',3:'VEC3',4:'VEC4',16:'MAT4'}[width]});return index;
  }
  const positions=[],joints=[],weights=[],inverse=[];
  for(let i=0;i<8;i++) {
    positions.push(-.03,i*.2,0,.03,i*.2+.02,0,0,i*.2+(i===7?.38:.08),.03);
    for(let k=0;k<3;k++){joints.push(i,0,0,0);weights.push(mutation==='weights'?.5:1,0,0,0);}
    inverse.push(1,0,0,0,0,1,0,0,0,0,1,0,0,-i*.2,0,1);
  }
  const attributes={POSITION:add(positions,3),JOINTS_0:add(joints,4,5123),WEIGHTS_0:add(weights,4)};
  const targetNames=['sil','PP','FF','TH','DD','kk','CH','SS','nn','RR','aa','E','I','O','U'].map(name=>`viseme_${name}`);
  const targets=targetNames.map((_,i)=>({POSITION:add(positions.map((value,k)=>k===1?(i>0?.001*i:mutation==='silence'?.05:0):0),3)}));
  const inverseBindMatrices=add(inverse,16),time=add([0,.5,1],1);
  const idle=add([0,.2,0,0,.205,0,0,mutation==='loop'?.215:.2,0],3);
  const first=add([0,0,0,1,Math.sin(.2),0,0,Math.cos(.2),0,0,0,1],4);
  const second=add([0,0,0,1,Math.sin(-.15),0,0,Math.cos(-.15),0,0,0,1],4);
  const nodes=[{children:[1,9]}];
  for(let i=0;i<8;i++)nodes.push({translation:[0,i? .2:0,0],...(i<7?{children:[i+2]}:{})});
  nodes.push({mesh:0,skin:0});
  const mesh=mutation==='morphs'?{primitives:[{attributes}]}:{extras:{targetNames},primitives:[{attributes,targets}]};
  const json={asset:{version:'2.0'},scene:0,scenes:[{nodes:[0]}],nodes,meshes:[mesh],
    skins:[{joints:[1,2,3,4,5,6,7,8],inverseBindMatrices}],
    animations:[
      {name:mutation==='clip'?'Wrong':'Idle',samplers:[{input:time,output:idle}],channels:[{sampler:0,target:{node:2,path:'translation'}}]},
      {name:'Walking',samplers:[{input:time,output:first},{input:time,output:second}],channels:[{sampler:0,target:{node:2,path:'rotation'}},{sampler:1,target:{node:3,path:'rotation'}}]},
    ],buffers:[{byteLength:offset}],bufferViews:views,accessors};
  for(const name of ['StrafeLeft','StrafeRight'])json.animations.push({...json.animations[1],name});
  const text=Buffer.from(JSON.stringify(json)),jsonChunk=Buffer.alloc(Math.ceil(text.length/4)*4,32);text.copy(jsonChunk);
  const bin=Buffer.concat(chunks),header=Buffer.alloc(12),jHeader=Buffer.alloc(8),bHeader=Buffer.alloc(8);
  header.writeUInt32LE(0x46546c67);header.writeUInt32LE(2,4);header.writeUInt32LE(28+jsonChunk.length+bin.length,8);
  jHeader.writeUInt32LE(jsonChunk.length);jHeader.writeUInt32LE(0x4e4f534a,4);bHeader.writeUInt32LE(bin.length);bHeader.writeUInt32LE(0x004e4942,4);
  return Buffer.concat([header,jHeader,jsonChunk,bHeader,bin]);
}

test('GLB verifier accepts actual skeletal deformation and rejects corrupt weights, missing clips and broken loops',()=>{
  const cwd=mkdtempSync(join(tmpdir(),'plaisance-avatar-verify-'));
  try {
    const folder=join(cwd,'public/gltf/avatars');mkdirSync(folder,{recursive:true});
    const script=fileURLToPath(new URL('../scripts/verify-rigged-avatars.mjs',import.meta.url));
    for(const mutation of [undefined,'weights','clip','loop','morphs','silence']) {
      for(const id of ['courtMale','courtFemale'])writeFileSync(join(folder,`${id}.glb`),makeGLB(mutation));
      const result=spawnSync(process.execPath,[script],{cwd,encoding:'utf8',timeout:30000});
      if(!mutation) {
        assert.equal(result.status,0,result.stderr);
        const report=JSON.parse(readFileSync(join(cwd,'artifacts/avatars/verification.json')));
        assert.equal(report.assets.courtMale.weightedJoints,8);
        assert.ok(report.assets.courtFemale.clips.Walking.maxSkinnedVertexMotion>.015);
        assert.ok(report.assets.courtMale.clips.Idle.maxBoneMotion>.0005);
      } else assert.notEqual(result.status,0,`${mutation} must be rejected`);
    }
  } finally {
    assert.equal(dirname(resolve(cwd)),resolve(tmpdir()),'cleanup stays inside the temporary directory');
    assert.match(basename(cwd),/^plaisance-avatar-verify-/);
    rmSync(cwd,{recursive:true,force:true});
  }
});
