// Optional GPU diagnostic: call from the managed runtime before entering XR.
// Exercises both Quest VIEW_ID shader branches on GPUs without OCULUS_multiview.
import { Color, DataTexture, Mesh, OrthographicCamera, PlaneGeometry, Scene, Vector4, WebGLRenderTarget, type WebGLRenderer } from '@iwsdk/core';
import { PlanarReflection } from '../src/planar-reflection.js';
import { hearthFire } from '../src/scene-assets/hearth-fire.scene-asset.js';

export function verifyVRShaders(renderer: WebGLRenderer): void {
  const scene = new Scene(), camera = new OrthographicCamera(-1, 1, 1, -1, .05, 10);
  camera.position.z = 2;
  const mesh = new Mesh(new PlaneGeometry(2, 2)), mirror = new PlanarReflection(mesh);
  const red = new DataTexture(new Uint8Array([255, 0, 0, 255]), 1, 1);
  const green = new DataTexture(new Uint8Array([0, 255, 0, 255]), 1, 1);
  red.needsUpdate = green.needsUpdate = true;
  const target = new WebGLRenderTarget(32, 32), pixels = new Uint8Array(32 * 32 * 4);
  const previous = renderer.getRenderTarget(), xr = renderer.xr.enabled;
  const viewport = renderer.getViewport(new Vector4()), scissor = renderer.getScissor(new Vector4());
  const scissorTest = renderer.getScissorTest(), clear = renderer.getClearColor(new Color()), alpha = renderer.getClearAlpha();
  const results: object[] = [];
  scene.add(mesh);
  try {
    renderer.xr.enabled = false; renderer.setRenderTarget(target); renderer.setScissorTest(false); renderer.setClearColor(0, 1);
    mirror.material.uniforms.reflection.value = red;
    mirror.material.uniforms.reflectionRight.value = green;
    mirror.material.uniforms.ready.value = mirror.material.uniforms.readyRight.value = 1;
    for (const eye of [0, 1]) {
      mirror.material.defines = { VIEW_ID: `${eye}u` }; mirror.material.needsUpdate = true;
      renderer.render(scene, camera); renderer.readRenderTargetPixels(target, 0, 0, 32, 32, pixels);
      const offset = (16 * 32 + 16) * 4;
      const color = Array.from(pixels.slice(offset, offset + 3));
      if (color[eye] < 150 || color[1-eye] > 10 || color[2] > 10) throw new Error(`Wrong mirror eye ${eye}: ${color}`);
      results.push({ mirrorEye: eye, color });
    }
    scene.remove(mesh);
    const flame = hearthFire.clone(); scene.add(flame);
    const material = hearthFire.material.clone(); flame.material = material;
    try {
      for (const eye of [0, 1]) {
        material.defines = { VIEW_ID: `${eye}u` }; material.needsUpdate = true;
        for (const distance of [2, .2, 2]) {
          camera.position.z = distance;
          renderer.render(scene, camera); renderer.readRenderTargetPixels(target, 0, 0, 32, 32, pixels);
          let lit = 0;
          for (let i = 0; i < pixels.length; i += 4) if (pixels[i] > 20) lit++;
          if (lit < 15) throw new Error(`Fire disappeared for eye ${eye} at ${distance} m: ${lit} pixels`);
          results.push({ flameEye: eye, distance, lit });
        }
      }
    } finally { material.dispose(); }
    console.info('VR shader GPU verification', JSON.stringify(results));
  } finally {
    renderer.xr.enabled = xr; renderer.setRenderTarget(previous);
    renderer.setViewport(viewport); renderer.setScissor(scissor); renderer.setScissorTest(scissorTest); renderer.setClearColor(clear, alpha);
    mirror.dispose(); mesh.geometry.dispose(); red.dispose(); green.dispose(); target.dispose();
  }
}
