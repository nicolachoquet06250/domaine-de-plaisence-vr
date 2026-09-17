import { createComponent, Types } from '@iwsdk/core';

export const HearthFire = createComponent('HearthFire', {
  phase: { type: Types.Float32, default: 0 },
  elapsed: { type: Types.Float32, default: 0 },
});
export const HearthGlow = createComponent('HearthGlow', {
  phase: { type: Types.Float32, default: 0 },
});
