// Planar camera/oblique clipping adapted from Three.js Reflector (MIT, three.js authors).
// Copyright © 2010-2025 three.js authors. License: design/THREE-MIRROR-LICENSE.txt.
// Imports use the SDK's Three instance. Unlike the stock r181 reflector, targets
// are independent for each XR eye and renderer state is restored in finally.
import { Camera, Matrix4, Mesh, PerspectiveCamera, Plane, ShaderMaterial, Vector3, Vector4, WebGLRenderTarget, HalfFloatType, type ArrayCamera, type Scene, type WebGLRenderer } from '@iwsdk/core';

export const REFLECTION_ONLY_LAYER = 29;

export class ReflectionCamera {
  readonly camera = new PerspectiveCamera();
  readonly textureMatrix = new Matrix4();
  readonly position = new Vector3();
  readonly normal = new Vector3();
  private readonly rotation = new Matrix4();
  private readonly eye = new Vector3();
  private readonly view = new Vector3();
  private readonly target = new Vector3();
  private readonly plane = new Plane();
  private readonly clip = new Vector4();
  private readonly q = new Vector4();
  private readonly corner = new Vector3();

  update(surface: Mesh, source: Camera): boolean {
    this.position.setFromMatrixPosition(surface.matrixWorld);
    this.eye.setFromMatrixPosition(source.matrixWorld);
    this.rotation.extractRotation(surface.matrixWorld);
    this.normal.set(0, 0, 1).transformDirection(this.rotation);
    this.view.subVectors(this.position, this.eye);
    if (this.view.dot(this.normal) >= -.015) return false;
    this.camera.position.copy(this.view.reflect(this.normal).negate().add(this.position));
    // A window through the mirror: align the virtual camera to the glass and
    // fit its off-axis frustum to the four edges, instead of copying the HMD FOV.
    // This spends the entire texture on the mirror and culls everything outside it.
    this.target.copy(this.camera.position).add(this.normal);
    this.camera.up.set(0, 1, 0).transformDirection(this.rotation);
    this.camera.lookAt(this.target);
    this.camera.far = (source as PerspectiveCamera).far ?? 220;
    this.camera.near = (source as PerspectiveCamera).near ?? .05;
    this.camera.layers.mask = source.layers.mask;
    this.camera.layers.enable(REFLECTION_ONLY_LAYER);
    this.camera.updateMatrixWorld();
    if (!surface.geometry.boundingBox) surface.geometry.computeBoundingBox();
    const bounds = surface.geometry.boundingBox!;
    let left=Infinity, right=-Infinity, bottom=Infinity, top=-Infinity;
    const near=this.camera.near;
    for(let i=0;i<4;i++) {
      this.corner.set(i&1?bounds.max.x:bounds.min.x,i&2?bounds.max.y:bounds.min.y,0)
        .applyMatrix4(surface.matrixWorld).applyMatrix4(this.camera.matrixWorldInverse);
      const scale=near/-this.corner.z;
      left=Math.min(left,this.corner.x*scale);right=Math.max(right,this.corner.x*scale);
      bottom=Math.min(bottom,this.corner.y*scale);top=Math.max(top,this.corner.y*scale);
    }
    if(right-left<1e-7||top-bottom<1e-7)return false;
    this.camera.projectionMatrix.makePerspective(left,right,top,bottom,near,this.camera.far);
    this.textureMatrix.set(.5,0,0,.5, 0,.5,0,.5, 0,0,.5,.5, 0,0,0,1)
      .multiply(this.camera.projectionMatrix).multiply(this.camera.matrixWorldInverse).multiply(surface.matrixWorld);
    this.plane.setFromNormalAndCoplanarPoint(this.normal, this.position).applyMatrix4(this.camera.matrixWorldInverse);
    this.clip.set(this.plane.normal.x, this.plane.normal.y, this.plane.normal.z, this.plane.constant);
    const p = this.camera.projectionMatrix.elements;
    this.q.set((Math.sign(this.clip.x)+p[8])/p[0], (Math.sign(this.clip.y)+p[9])/p[5], -1, (1+p[10])/p[14]);
    const denominator = this.clip.dot(this.q);
    if (Math.abs(denominator) < 1e-6) return false;
    this.clip.multiplyScalar(2/denominator);
    p[2]=this.clip.x; p[6]=this.clip.y; p[10]=this.clip.z+1-.003; p[14]=this.clip.w;
    this.camera.projectionMatrixInverse.copy(this.camera.projectionMatrix).invert();
    return true;
  }
}

export class PlanarReflection {
  readonly view = new ReflectionCamera();
  readonly material = new ShaderMaterial({
    name: 'Miroir de la cour — reflet planaire',
    uniforms: {
      reflection: { value: null }, textureMatrix: { value: new Matrix4() }, ready: { value: 0 },
      reflectionRight: { value: null }, textureMatrixRight: { value: new Matrix4() }, readyRight: { value: 0 },
    },
    vertexShader: `
      uniform mat4 textureMatrix, textureMatrixRight;
      varying vec4 reflectedUV;
      void main() {
        reflectedUV = textureMatrix * vec4(position, 1.);
        #ifdef VIEW_ID
          if (VIEW_ID == 1u) reflectedUV = textureMatrixRight * vec4(position, 1.);
        #endif
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.);
      }
    `,
    fragmentShader: `
      uniform sampler2D reflection, reflectionRight;
      uniform float ready, readyRight;
      varying vec4 reflectedUV;
      void main() {
        vec3 c;
        float available;
        #ifdef VIEW_ID
          if (VIEW_ID == 1u) {
            c = texture2DProj(reflectionRight, reflectedUV).rgb;
            available = readyRight;
          } else
        #endif
        {
          c = texture2DProj(reflection, reflectedUV).rgb;
          available = ready;
        }
        gl_FragColor = vec4(mix(vec3(.18,.20,.21), c*.94, available), 1.);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }
    `,
  });
  readonly targets = [new WebGLRenderTarget(1,1,{type:HalfFloatType,depthBuffer:true,samples:2}),new WebGLRenderTarget(1,1,{type:HalfFloatType,depthBuffer:true,samples:2})];
  readonly matrices = [new Matrix4(), new Matrix4()];
  readonly frames = [-1, -1];
  enabled = false;
  captures = 0;
  previousVisible = true;
  private readonly viewport = new Vector4();
  private readonly scissor = new Vector4();
  private readonly originalMaterial;
  private readonly originalCallback;
  private readonly size = new Vector3();

  constructor(readonly mesh: Mesh) {
    this.originalMaterial=mesh.material; this.originalCallback=mesh.onBeforeRender;
    mesh.material=this.material;
    mesh.updateWorldMatrix(true,false);
    if(!mesh.geometry.boundingBox)mesh.geometry.computeBoundingBox();
    mesh.geometry.boundingBox!.getSize(this.size);
    const e=mesh.matrixWorld.elements;
    const width=this.size.x*Math.hypot(e[0],e[1],e[2]),height=this.size.y*Math.hypot(e[4],e[5],e[6]);
    const ratio=width/Math.max(.001,height);
    // Stable portrait/landscape allocation: never resize render targets as the head moves.
    const w=ratio>=1?1024:Math.max(256,Math.round(1024*ratio));
    const h=ratio>=1?Math.max(256,Math.round(1024/ratio)):1024;
    for(const target of this.targets)target.setSize(w,h);
    for(const target of this.targets)target.texture.generateMipmaps=false;
  }

  /** Called before the main scene pass, after WebXR has updated both eye cameras. */
  capture(renderer: WebGLRenderer, scene: Scene, camera: Camera, frame: number, before: () => void, after: () => void): void {
    if ((camera as ArrayCamera).isArrayCamera) {
      const eyes = (camera as ArrayCamera).cameras;
      for (let eye = 0; eye < Math.min(2, eyes.length); eye++) this.captureEye(renderer, scene, eyes[eye], eye, frame, before, after);
    } else this.captureEye(renderer, scene, camera, 0, frame, before, after);
  }

  private captureEye(renderer: WebGLRenderer, scene: Scene, camera: Camera, eye: number, frame: number, before: () => void, after: () => void): void {
    if (this.enabled && this.frames[eye]!==frame && this.view.update(this.mesh,camera)) {
      const oldTarget=renderer.getRenderTarget(), oldFace=renderer.getActiveCubeFace(), oldMip=renderer.getActiveMipmapLevel();
      const xr=renderer.xr.enabled, shadows=renderer.shadowMap.autoUpdate, scissorTest=renderer.getScissorTest();
      renderer.getViewport(this.viewport); renderer.getScissor(this.scissor);
      before();
      try {
        renderer.xr.enabled=false; renderer.shadowMap.autoUpdate=false;
        renderer.setRenderTarget(this.targets[eye]); renderer.setScissorTest(false);
        // Transparent fire/glass can leave depth writes disabled from the last pass.
        // gl.clear respects that mask: stale depth otherwise erases moving reflections.
        renderer.state.buffers.depth.setMask(true);
        renderer.clear(); renderer.render(scene,this.view.camera);
        this.matrices[eye].copy(this.view.textureMatrix); this.frames[eye]=frame; this.captures++;
      } finally {
        renderer.xr.enabled=xr; renderer.shadowMap.autoUpdate=shadows;
        renderer.setRenderTarget(oldTarget,oldFace,oldMip);
        renderer.setViewport(this.viewport); renderer.setScissor(this.scissor); renderer.setScissorTest(scissorTest);
        after();
      }
    }
  }

  /** Binding a mirror never interrupts the opaque/transparent or multiview draw pass. */
  bindEye(eye: number): void {
    this.material.uniforms.reflection.value=this.targets[eye].texture;
    this.material.uniforms.textureMatrix.value=this.matrices[eye];
    this.material.uniforms.ready.value=this.frames[eye]>=0?1:0;
    this.material.uniforms.reflectionRight.value=this.targets[1].texture;
    this.material.uniforms.textureMatrixRight.value=this.matrices[1];
    this.material.uniforms.readyRight.value=this.frames[1]>=0?1:0;
    this.material.uniformsNeedUpdate=true;
  }

  dispose(): void {
    this.mesh.onBeforeRender=this.originalCallback;this.mesh.material=this.originalMaterial;
    this.material.dispose();for(const target of this.targets)target.dispose();
  }
}
