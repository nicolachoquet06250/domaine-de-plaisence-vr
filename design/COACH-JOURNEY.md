# Royal carriage journey — approved feature delta

## Spec and acceptance (phase 1)
Approved in conversation: arrival identity unlocks a portal at the wicket; entering
seats and locks locomotion; local carriage follows the gravel smoothly with Blender
rigged animated horses. At 50% outbound distance connect as an invisible observer
and receive visible peers. At castle arrival publish the player at the gate and
enable mirrors/fires. Returning to the grand gate boards locally, hides the player
and disables effects immediately. A broad smooth turn precedes the return journey;
at 50% return distance disconnect fully. Drop inside the arrival circle by the wicket.
Carriages never enter the wire protocol. Saved identity/invitations never skip boarding.

[ASSUMED] Head/look tracking remains free while seated. Travel takes approximately
one minute at a gentle speed, pauses if the app is blurred, and slows at endpoints.
Arrival waits for a successful network activation instead of spawning a ghost player.
An unavailable/full room offers retry or return without releasing the player outside
the accessible estate. The castle is translated to the approved landscape location
(100,0,-95); all players use the same world coordinates. Existing room links remain.

## Design (phase 2)
Reuse the approved landscape and coach visuals. The wicket gains a subtle gold/blue
portal once identity is valid. The passenger viewpoint is inside the rear seat and
faces along travel, retaining free look. A small world panel shows destination and
progress during travel. The castle interior and gardens occupy their existing relative
positions. See coach-journey.html for the transition diagram and route.

## Grounding (phase 3)
Installed IWSDK 0.5.3 source is authoritative; reference CLI fails with ONNX DLL load
error. LocomotionSystem.setPlayerPosition exists; pausing the ECS locomotion/slide/
turn/teleport systems allows a local moving seat without physics fighting it. Restore
the engine position once on disembark, preserving XR head rotation and physical offset.
World assets.instantiate and AssetManager provide loaded GLTF animation clips;
AnimationMixer and CatmullRomCurve3 come from @iwsdk/core. Scene JSON remains an
import-free asset-only composition. RayInteractable handles portal click accessibility;
walking into an authored trigger volume also boards before reaching the retained wall.

CUSTOM: journey state machine, arc-length route, observer protocol, shader phase gate.
CONFIGURE: merged composition, authored portal, passenger UI, locomotion suspension.
BUILT-IN: ECS queries, player transforms, controller input, asset manager and mixers.

## Architecture (phase 4)
Root owns src/coach-journey*.ts, merged scene, shared component/asset registration,
shader gates, comfort/mobile phase scope and runtime verification.
Network agent owns server/rooms.mjs, src/multiplayer.ts, associated protocol/identity
tests. Blender agent owns scripts/blender-coach-rig.py, exported animated GLB and
rig verification. Shared contract below avoids cycles between gameplay and networking.

Multiplayer public contract: isIdentityReady(), prepareJourney():boolean,
connectObserver():void, activatePresence():Promise<boolean>, hidePresence():void,
disconnectJourney():void, finishJourney():void, isConnected():boolean,
isParticipant():boolean, getConnectionStatus():string,
setJourneyHandlers({depart:()=>void,return:()=>void}):()=>void,
subscribeIdentity(listener:()=>void):()=>void.
prepare freezes identity and reserves invitation/new room ID without connecting.
disconnectJourney ends socket/voice but keeps identity locked until finishJourney.
The legacy enterLobby/leaveLobby methods delegate to the journey callbacks.

Milestones: M0 current typecheck and managed runtime nonblank (passed); M1 observer
protocol tests; M2 Blender skin/animation export; M3 unified scene and journey;
M4 native runtime and XR phase transitions; M5 regressions/build/review.

## Progress
Phases 0–4 complete. User's confirmed design supplies approval; no new sign-off needed.
Phases 5–7 complete. Local-only delivery. Existing source scenes kept for rollback.

## Verification and delivery (2026-09-11)
- TypeScript: `npx tsc --noEmit` passed. Production: `npm run build` passed.
- 60 focused tests passed, including real WebSocket observer/presence visibility,
  room capacity, identity, rig weights, animation loops, route continuity, seat
  offsets, delayed acknowledgement, return cancellation, and existing controls.
  Log: `artifacts/coach-journey/tests.log`.
- Managed browser completed a real UI/portal/socket round trip in 175 seconds,
  including a 20-second diagnostic visit. Observer connection recorded at 50.3%,
  visible participant/effects at arrival, hidden participant/effects on return,
  full disconnect at 50.2% return, arrival eyes at (5.4,1.66,0).
  `artifacts/coach-journey/desktop-milestones.json` retains observations.
- IWER Meta Quest 3 immersive session: boarded through the wicket, remained
  seated during travel, arrived at the castle as participant with effects enabled,
  and triggered return by approaching the gate. Runtime screenshot:
  `artifacts/coach-journey/vr-arrival.png`. Physical Quest performance/comfort
  remains unmeasured; desktop GPU samples are not headset frame-rate evidence.
- Native scene validation and final gate render passed without diagnostics:
  `artifacts/coach-journey/visit-gate-final.json` and corresponding PNG.
  Source/composed hash: `sha256:1e7196b2915390caaf64abebaf25dc5976942dfd6eb5eb63fb800d4872870620`.
  Runtime hash: `sha256:0b4100d13b9ecb4b05bc82b3077005d58f023b3646744642ed3ce5435d4156a0`.
- Passenger view and isolated UIKit panel reviewed in `passenger.png` and
  `coach-panel.png`. Temporary test driver removed from src/index.ts.
- Blender MCP generated two 16-bone skinned horses with HorseIdle/HorseWalk,
  independent wheel pivots, and a 96-triangle gravel forecourt. Carriage is
  64,540 triangles / approximately 3.33 MB. Trimmed 2,638 intersecting grass faces
  in a derived lawn asset; original lawn/model sources remain intact.
- Review fixes: continuous route tangents through parking, gradual centring on
  the gate, active-scene-only Blender export, hidden avatar preview during travel,
  both VR buttons rebound after scene merge, XR seat recapture after input sampling.

The initial arrival remains lightweight. The complete visit composition loads
after boarding and remains available for subsequent trips; every carriage is a
persistent local entity. Server and client must be deployed together for the new
observer/presence protocol. No deployment was performed in this task.
