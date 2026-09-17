# Architecture
Existing app delta: replace starter scene/manifest/registrations; preserve virtual:iwsdk-project. Retain locomotion/spatialUI; disable unused physics/grabbing. Static native scene with semantic assets and seven jet nodes.
File ownership: root src/index.ts,assets.ts,components.ts,iwsdk.config.json,public/scenes, fountain/architecture assets; multiplayer worker src/multiplayer*, server/*, tests/rooms*, Vite plugin module; garden worker src/scene-assets/garden.scene-asset.ts only.
Components: WaterJet kind Float32 0, phase Float32 0; RemoteVisitor server ID and target pose data (worker schema).
Systems: FountainSystem priority20 query WaterJet, MultiplayerSystem priority21 query RemoteVisitor, BrowserLookSystem priority1. Network sends on timer, interpolation per frame without allocations.
M0 passed: original screenshot nonblank, tsc clean, XR enter+exit succeeds, bridge ready.
M1 assets: palace/gardens native render hero/top/quarter/spawn, no validation diagnostics.
M2 fountain: exactly7 jets, runtime animation and clock sync verified.
M3 multiplayer: isolated rooms, two peers receive poses, disconnect cleanup, reconnect; integration tests.
M4 complete: typecheck, native editor clean, runtime/XR screenshots, npm build, local deployable room server.
[ASSUMED] Architecture approved within request; local build only, no git commit or deployment.
