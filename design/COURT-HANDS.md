# Mains des avatars — 9 septembre 2026

Révision ultérieure : [agrandissement, calibration WebXR corrigée et marche](COURT-GRIP.md). Les axes de prise décrits ci-dessous sont ceux de la version du 9 septembre et sont remplacés par cette révision.

Les deux avatars utilisent désormais des mains continues créées et exportées via le MCP Blender par `scripts/blender-royal-figures.py`. La paume, le relief thénar et les cinq doigts sont fusionnés par remeshing voxel, lissés puis décimés à environ 3 500 triangles de peau par main. Les doigts ont des longueurs différentes, une légère flexion et des extrémités arrondies. Les ongles sont des surfaces fines projetées sur la peau finale pour éviter les intersections.

Référence visuelle anatomique consultée : [Event Medicine Group, Anatomy of the Hand](https://www.eventmedicinegroup.org/patientassessment). Aucun pixel de cette référence n'est intégré aux modèles. Le rendu reste une géométrie simplifiée pour VR, avec les matériaux de peau existants.

Le repère de repos est explicite : doigts vers −Y, pouces vers +Z, paumes vers le corps. `CourtArmIK` calibre chaque poignet à partir de son véritable repère de liaison Blender. Une prise XR neutre donne des doigts vers −Z et des pouces vers +Y. La pronation/supination de l'avant-bras est limitée à ±90°, puis les limites existantes du poignet s'appliquent. Les doigts gardent une pose détendue fixe : cette modification ne crée pas de suivi individuel des doigts.

Les GLB remplacent les ressources existantes du manifeste, avec une version d'URL pour invalider les anciens modèles en cache. Le fichier éditable est `artifacts/avatars/renaissance-court.blend`.

| Avatar entier | Triangles | Taille GLB |
| --- | ---: | ---: |
| Masculin | 51 896 | 1 580 508 octets |
| Féminin | 44 910 | 1 379 424 octets |

Validation :

- TypeScript sans erreur ; 16 tests arrivée/avatars/validation GLB et 7 tests IK passent.
- Les tests IK chargent les vrais sommets, poids et matrices de liaison des GLB. Ils vérifient le pouce au-dessus de l'index, les doigts vers l'avant et le dos des mains vers l'extérieur après déformation, sur les deux avatars avec plusieurs rotations du corps. 180 poses vérifient également la calibration des axes, et les poses extrêmes respectent les longueurs et limites articulaires.
- Le vérificateur GLB confirme les poids normalisés, les quatre animations en boucle, la taille humaine et l'indépendance des clones.
- Gros plans natifs du moteur : `artifacts/court/male-hand.png` et `female-hand.png` ; les deux vues de diagnostic restent dans la scène de revue.
- Session XR native émulée, avatar féminin : corps visible, deux mains suivies ; changement de positions et rotations des deux manettes observé dans les diagnostics ECS. Erreurs de position des poignets inférieures à 0,000001 m sur les deux poses. Capture `artifacts/court/hands-xr.png`, mesures `hands-xr-observations.json`.
- Les données temporaires de test et le code de démarrage de test ont été retirés. Aucun essai matériel au casque ni mesure de fréquence d'affichage au casque n'est revendiqué.
