import { createComponent, Types } from '@iwsdk/core';

export const PalaceMirror = createComponent('PalaceMirror', {
  maxDistance: { type: Types.Float32, default: 18 },
  captures: { type: Types.Int32, default: 0 },
  active: { type: Types.Boolean, default: false },
});
