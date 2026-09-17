import { createComponent, Types } from '@iwsdk/core';

/** Local player travel state. Never serialized into room packets. */
export const CoachJourney = createComponent('CoachJourney', {
  phase: { type: Types.String, default: 'arrival' },
  progress: { type: Types.Float32, default: 0 },
  traveling: { type: Types.Boolean, default: false },
  effectsEnabled: { type: Types.Boolean, default: false },
  identityReady: { type: Types.Boolean, default: false },
  domainLoaded: { type: Types.Boolean, default: false },
  connectedHalfway: { type: Types.Boolean, default: false },
  speed: { type: Types.Float32, default: 0 },
  distance: { type: Types.Float32, default: 0 },
  error: { type: Types.String, default: '' },
});
export const CoachVehicle = createComponent('CoachVehicle', {});
export const ArrivalPortalHint = createComponent('ArrivalPortalHint', {
  side: { type: Types.Int8, default: 0 },
});
export const CoachPortal = createComponent('CoachPortal', {
  destination: { type: Types.String, default: 'castle' },
});

export type JourneyPhase = 'arrival' | 'outbound' | 'waiting' | 'activating' | 'visiting' | 'returning';
