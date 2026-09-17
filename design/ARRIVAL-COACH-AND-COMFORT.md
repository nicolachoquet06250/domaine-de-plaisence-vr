# Arrival comfort, wicket and royal carriage

The arrival scene exposes only comfort settings through desktop M, right-controller
B and the mobile Confort button. Room and voice controls remain available in the
castle menu. Mobile Accueil keeps nickname and avatar selection accessible; Domaine
is hidden in arrival. Scene changes close panels and preserve the comfort preference.

Blender MCP generated `public/gltf/arrival-coach/arrival.glb`, `wicket.glb` and
`royalCoach.glb`. The terrace has a 2.393 m opening in its east parapet, at the gravel
arrival. Its other geometry and scene placements are unchanged. The 1.114 m wicket
uses the castle gate's wrought iron, gold fleurs-de-lys, scrolls and crowned blue
escutcheon. The original `arrivalCollision`, `arrivalBoundary` and recovery system
remain closed, including across this visual opening.

The carriage has a timber grain texture, sculpted panels, gold mouldings, four
spoked wheels, hubs, axles, suspension, steps, velvet seating and roof crown. Two
sculpted horses have distinct coats, manes, tails, hooves, eyes, bridles, collars,
traces and reins. This is static decoration. The carriage centre lies exactly five
metres along the existing path from the wicket tangent. The horses and flexible
front assembly follow the bend, and all hoof vertices remain inside the gravel.

Sources: `scripts/blender-arrival-coach.py` and
`scripts/integrate-arrival-coach.mjs`. Run the former through the existing local
Blender MCP wrapper, then the latter with Node. The full landscape Blender pipeline
also invokes the model generator. Source scenes are saved separately under
`artifacts/arrival-coach/`; the original Blender files are preserved. Telemetry
remains disabled in the MCP wrapper. Bump the manifest URL version after regenerating
an asset that has already loaded into the editor/runtime cache.

Verification: TypeScript and production build pass. Forty targeted tests pass:
comfort and mobile handlers, arrival identity flow, landscape preservation, actual
Locomotor perimeter blocking, castle enclosure regressions, exact unchanged terrace
geometry outside the opening, wicket height, carriage distance, hoof placement and
embedded GLB resources. B was also pressed and released in IWER's Quest 3 session;
the live ComfortSettings entity opened and closed and the screenshot shows only
comfort controls. This is emulator verification, not a physical Quest performance
measurement.

Evidence in `artifacts/arrival-coach/`: `model-stats.json`, `comfort-vr.png`,
`horses-final.png`, `wicket.png`, `arrival-final.png`, `arrival-top.png`,
`exit-final.png`, `arrival-spawn.png` and corresponding render JSON metadata.
The carriage and horses use fewer than 65,000 triangles; the wicket uses 5,632.
The scene is import-free and the editor reports valid, clean and conflict-free.
