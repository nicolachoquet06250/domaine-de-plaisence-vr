/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

import { defineComponents } from '@iwsdk/core';
import { Robot } from './robot-component.js';
import { WaterJet, FountainWater } from './fountain-components.js';
import { RemoteVisitor, RoomConnection } from './multiplayer-components.js';
import { ComfortSettings } from './comfort-settings.js';
import { StaticCollision } from './collision-components.js';
import { PalaceDoor, PalaceDoorBlocker } from './palace-door-components.js';
import { PalaceMirror } from './mirror-components.js';
import { HearthFire, HearthGlow } from './hearth-components.js';
import { ArrivalBoundary } from './arrival-boundary-components.js';
import { CoachJourney, CoachVehicle, CoachPortal, ArrivalPortalHint } from './coach-journey-components.js';

export default defineComponents([Robot, WaterJet, FountainWater, RemoteVisitor, RoomConnection, ComfortSettings, StaticCollision, PalaceDoor, PalaceDoorBlocker, PalaceMirror, HearthFire, HearthGlow, ArrivalBoundary, CoachJourney, CoachVehicle, CoachPortal, ArrivalPortalHint]);
