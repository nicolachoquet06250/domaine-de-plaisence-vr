# Cour et paysage — livraison du 9 septembre 2026

Révision suivante : visage de courtisane distinct, coiffures arrière complètes sur les quatre modèles, suivi IK des manettes et animations `StrafeLeft`/`StrafeRight`. La description ci-dessous documente la première livraison ; les données et vérifications actuelles sont dans [COURT-MOTION.md](../../design/COURT-MOTION.md). Le fichier château révisé est `../castle/chateau-plaisance-coiffures.blend` et le script de placement remplace désormais les anciennes assemblées de portraits.

Les GLB sont générés via le MCP Blender local et intégrés au manifeste partagé et aux scènes existantes. La configuration démarre toujours sur l'accueil.

- Murs intérieurs prolongés jusqu'aux jambages : ouverture z[2,20 ; 5,40], jeu de 5 mm autour des vantaux, embrasures habillées. Les collisions conservent le passage libre.
- Deux portraits indépendants remplacent les anciennes silhouettes des chambres. François Ier porte béret, plume, barbe et chaîne ; Louis XIV, perruque bouclée, cravate et drapé. Ce sont des interprétations stylisées modelées dans Blender, pas des scans ni des copies fidèles des sculptures historiques.
- Deux avatars en costume de cour du XVIe siècle, squelette de 18 os, 16 articulations pondérées, clips bouclés `Idle` (3 s) et `Walking` (1 s). Les manches et la taille combinent les poids des os voisins. Les clips sont en place ; le réseau déplace les pieds et le mixer fond entre repos et marche. Pas de suivi IK des mains.
- Le pseudo et le choix Homme/Femme sont nécessaires à l'entrée. Le choix est mémorisé et transmis aux autres visiteurs, avec un aperçu animé à l'accueil. La sélection a été actionnée à la gâchette dans le runtime XR : male → female → male, avec changement du modèle et de `RoomConnection.avatar`. Le pseudo existant a été conservé.
- La terrasse d'accueil, ses colonnes, balustres, dallage, lanternes et jardinières utilisent le nouveau GLB. La pelouse des deux scènes possède une surface modelée et des brins opaques, groupés spatialement ; les chemins restent dégagés. Les parterres et urnes possèdent 82 fleurs sources avec tiges, sépales et feuilles.

## Fichiers éditables

- `../avatars/renaissance-court.blend` : portraits et avatars, armatures et animations.
- `../castle/chateau-plaisance.blend` : château et portraits placés.
- `../arrival-realistic/arrival-realistic.blend` : accueil.
- `../vegetation/dimensional-lawns.blend` et `rooted-garden-flowers.blend` : végétation.

## Vérification

`npx tsc --noEmit` et `npm run build` réussis. Les avertissements de bundle volumineux et d'annotations Zod subsistent. Tests identité/réseau/mixers : 25 cas, dont le test du libellé de sélection réexécuté après remplacement du caractère absent de la police ; tous passent dans leur exécution finale. Le vérificateur des GLB contrôle les poids normalisés, l'animation réelle des sommets, les boucles et l'indépendance des clones SDK (`../avatars/verification.json`). Les vérifications château, sols et végétation passent également. Le test des sols inspecte 432 triangles sans recouvrement ; les raccords de porte ont 60 sondes de continuité et 36 de dégagement.

Captures natives : `portraits-avatars.png`, `francois-bedroom.png`, `lawn.png`, `flowers.png`, `arrival-panel.png`. Le gros plan mur/porte a également été inspecté dans le rendu natif. Les rendus et l'émulation ne mesurent pas les FPS d'un casque physique. Les personnages et les sculptures restent visuellement stylisés ; cette livraison ne constitue pas un rendu photoréaliste.

Budgets exportés : avatar masculin 29 334 triangles / 905 988 octets ; féminin 48 598 / 1 446 528 ; François Ier 24 430 / 462 048 ; Louis XIV 37 104 / 680 100. Dix groupes de matériau par avatar, deux par buste. Accueil 52 900 triangles ; pelouses domaine/accueil 146 038 / 62 710.

## Références consultées

- [François Ier par Jean Clouet, Louvre](https://collections.louvre.fr/ark%3A/53355/cl010062204).
- [Louis XIV du Bernin, Versailles](https://www.chateauversailles.fr/actualites/expositions/genie-majeste-louis-xiv-bernin).
- [Catherine de Médicis par Clouet, 1555](https://www.viv-it.org/immagini/f-clouet-ritratto-di-caterina-de-medici-1555).

Les images consultées servent de références visuelles et ne sont pas embarquées dans les matériaux des modèles.

Régénération : `scripts/blender-royal-figures.py`, `blender-arrival-realistic.py`, `blender-vegetation-relief.py`, `blender-flower-stems.py`, chacun via `node scripts/blender-mcp.mjs execute_blender_code scripts/<fichier> scripts/blender-court-prompt.json`. La chaîne complète du château est décrite dans son README. Exécuter `blender-castle-place-portraits.py` une seule fois après une régénération complète du château ; une exécution répétée sur le même château ajoute des doublons Blender. Les GLB de portraits restent des assets séparés dans l'application.
