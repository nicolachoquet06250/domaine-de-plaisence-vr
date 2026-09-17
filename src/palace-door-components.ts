import { createComponent, Types } from '@iwsdk/core';
export const PalaceDoor = createComponent('PalaceDoor', {
  automatic: { type: Types.Boolean, default: true },
  requestedOpen: { type: Types.Boolean, default: false },
  openness: { type: Types.Float32, default: 0 },
  approachDistance: { type: Types.Float32, default: 3.2 },
});
export const PalaceDoorBlocker = createComponent('PalaceDoorBlocker', {
  owner: { type: Types.Entity, default: null },
});
