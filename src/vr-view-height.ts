import type { WebXRManager } from '@iwsdk/core';

/** Extra eye height in metres, shared by the headset and every tracked input. */
export const VR_VIEW_HEIGHT = 0.20;

/** Install once per world, not once per scene: changing rooms must not stack offsets. */
export function installVRViewHeight(xr: WebXRManager): () => void {
  let base: XRReferenceSpace | null = null;
  let raised: XRReferenceSpace | null = null;
  const start = () => {
    if (!xr.isPresenting || raised) return;
    base = xr.getReferenceSpace();
    if (!base) return;
    // A lower reference origin raises all poses. IWSDK input and Three's two
    // eye cameras read this same space, keeping controller/hand tracking aligned.
    const transform = new XRRigidTransform({ x: 0, y: -VR_VIEW_HEIGHT, z: 0 });
    // The bundled IWER emulator consumes matrix indices instead of the standard
    // XRRigidTransform. Keep the native object and expose those indices as well.
    if (Object.isExtensible(transform)) Object.assign(transform, transform.matrix);
    raised = base.getOffsetReferenceSpace(transform);
    xr.setReferenceSpace(raised);
  };
  const end = () => { base = raised = null; };
  xr.addEventListener('sessionstart', start);
  xr.addEventListener('sessionend', end);
  start();
  return () => {
    xr.removeEventListener('sessionstart', start);
    xr.removeEventListener('sessionend', end);
    if (base && xr.getReferenceSpace() === raised) xr.setReferenceSpace(base);
    end();
  };
}
