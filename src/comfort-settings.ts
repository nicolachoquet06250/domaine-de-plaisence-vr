import { createComponent, Types } from '@iwsdk/core';

/** Local visitor preference. It is deliberately never sent to the room server. */
export const ComfortSettings = createComponent('ComfortSettings', {
  open: { type: Types.Boolean, default: false },
  strength: { type: Types.Float32, default: .5 },
  appliedStrength: { type: Types.Float32, default: .5 },
});
