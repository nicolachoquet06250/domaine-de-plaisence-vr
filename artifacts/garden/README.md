# Jardin Blender

Les six familles du jardin sont modélisées dans Blender via le MCP local : pelouse, allées de gravier, parterres de buis et roses, cyprès, urnes fleuries et murets. Les bancs et la fontaine animée de la première étape restent dans `../blender/estate-assets.blend`.

Ouvrir `garden-assets.blend` : les scènes `REVIEW - Garden …` permettent d'inspecter les objets séparément. Les modèles exportés sont dans `../../public/gltf/garden/`. Textures intégrées, matériaux PBR, géométrie fusionnée par modèle, feuillage opaque sans mélange alpha. Les trois variantes d'allée gardent les dimensions de composition existantes et adaptent les UV au gravier en mètres.

Régénération depuis la racine, avec Blender et son MCP actifs : exécuter `scripts/blender-garden-base.py`, `scripts/blender-garden-hardscape.py`, `scripts/blender-garden-plants.py`, `scripts/blender-garden-export.py`, puis `scripts/blender-garden-organize.py` via `node scripts/blender-mcp.mjs execute_blender_code <script> scripts/blender-garden-prompt.json`. La correction UV historique est déjà intégrée au générateur.

Vérifications : `npx tsc --noEmit`, `node scripts/verify-garden-assets.mjs`, `node scripts/verify-garden-collisions.mjs`, `npm run build` réussis. La compilation signale les gros bundles et des annotations Zod, sans erreur. Les GLB sont autonomes ; les placements, composants, collisions de composition et point d'entrée ont été comparés au document précédent.

Les collisions utilisent des enveloppes dédiées (2 172 triangles par parterre), sans pétales ni feuillage détaillé. Une correction de `StaticCollisionSystem` réapplique le point de départ après l'enregistrement des environnements, une fois par chargement : le décodage des GLB pouvait laisser commencer la chute avant leur disponibilité. Vérification en XR émulée Quest 3 : joueur stable à y≈0,053 m sur l'allée, session immersive active et animation des sept jets en progression. `runtime-xr.png` montre l'application, les autres captures proviennent de l'éditeur natif. L'entrée normale `arrival` a été restaurée après le test de chargement direct du jardin.

Captures : `before.png`, `after.png`, `detail.png`, `spawn.png`, `runtime-xr.png`. Mesures et empreintes dans `review.json` et `final-render.json`. Les statistiques correspondent aux vues de l'éditeur et ne mesurent pas la fréquence d'affichage d'un casque physique.
