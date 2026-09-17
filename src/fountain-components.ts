import { createComponent, Types } from '@iwsdk/core';
export const WaterJet = createComponent('WaterJet', {
  kind: { type: Types.Float32, default: 0 },
  phase: { type: Types.Float32, default: 0 },
  elapsed: { type: Types.Float32, default: 0 },
});
export const FountainWater = createComponent('FountainWater', {});
