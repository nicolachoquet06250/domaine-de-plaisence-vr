# Mains, marche et escalier — 10 septembre 2026

Cette révision remplace la calibration décrite dans COURT-HANDS.md. Les mains des deux avatars sont agrandies uniformément de 18 % autour du poignet dans le générateur Blender, peau et ongles compris. Le nombre de triangles reste identique : 51 896 pour l'avatar masculin, 44 910 pour le féminin.

La précédente calibration confondait le repère de prise avec une direction de pointage : elle plaçait le pouce suivant +Y du grip. La [spécification WebXR, gripSpace](https://www.w3.org/TR/webxr/#dom-xrinputsource-gripspace) définit −Z vers le pouce le long du manche tenu, avec une origine dans la prise. Blender exporte maintenant `xrGrip.modelToGripQuaternion` et `wristToGripModel` sur chaque os Hand. Le runtime les utilise pour orienter la main et décaler le poignet derrière la paume, en tenant compte de l'échelle du personnage. Le pôle des coudes est rapproché du corps. Les limites articulaires et longueurs des bras sont conservées. Les diagnostics `leftReachError` et `rightReachError` mesurent désormais l'erreur du repère de prise, et non la distance poignet/manette.

Blender Walking : balancement alterné des épaules ±0,32 rad, coudes pliés de 0,19 à 0,33 rad. Le contrôle des coordonnées des pose bones confirme une flexion vers l'avant et l'opposition gauche/droite. StrafeLeft et StrafeRight gardent les bras détendus, sans balancement cyclique. En VR, les mains suivies restent pilotées par les manettes ; l'IK conserve cette priorité sur les pistes de bras de l'animation.

Château : suppression ciblée de l'îlot de maillage de la dalle arrière supérieure (centre local [0,4.91,-4.89], dimensions [9.3,0.26,1.78]) et de sa collision. Le palier intermédiaire à 2,84 m reliant les volées reste présent. La source de génération omet aussi cette dalle. Source Blender révisée : `artifacts/castle/chateau-plaisance-escalier.blend` ; avatars : `artifacts/avatars/renaissance-court.blend`.

Validation :

- TypeScript sans erreur, 25 tests passent, dont neuf tests sur les rigs, véritables sommets GLB, repère de prise, agrandissement proportionnel et distinction Walking/Strafe.
- Vérification des quatre clips, poids, sommets animés et indépendance des clones GLB.
- Vérificateur château : collisions des passages, marches et parcours réel du capsule locomotor jusqu'au salon supérieur ; 430 triangles de sol sans superposition.
- Revue native : `artifacts/court/enlarged-hand.png`, `artifacts/castle/landing-without-platform.png`.
- Runtime XR émulé masculin : deux prises suivies ; déplacement et rotation de la manette droite modifient le bras droit, gauche stable. Capture `artifacts/court/grip-corrected-xr.png`, mesures `grip-20260910-runtime.json`. Écart du repère de prise : environ 2 mm en pose symétrique, 13 mm à droite dans la pose tournée testée, du fait des limites articulaires. Aucun essai au casque physique n'est revendiqué.
- Code de démarrage restauré à l'identique et identité/salon temporaires retirés ; démarrage normal sur l'accueil.
