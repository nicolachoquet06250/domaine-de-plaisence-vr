# Bancs et fontaine — sources Blender

Créés le 7 septembre 2026 dans Blender 5.2.1, par le serveur MCP `blender-mcp` déclaré dans `.mcp.json`.

- `estate-assets.blend` : sources éditables, avec scènes `REVIEW - Bench` et `REVIEW - Fountain` ; animation aux images 0–96, 24 images/s.
- `../../public/gltf/estate/` : cinq GLB autonomes, textures PBR embarquées de 512 px, sans décodeur externe.
- `glb-verification.json` : triangles, appels de rendu et contrôle des animations exportées.
- `runtime-water.png` : capture de l'application IWSDK en VR émulée.
- `bench-in-scene.png` : vue rapprochée du banc dans l'éditeur IWSDK.

Les identifiants de manifeste existants (`bench`, `basin`, `water`, `centralJet`, `lateralJet`) chargent désormais les GLB. Toutes les instances existantes sont remplacées, sans changer leurs placements. Les anciennes formes solides servent uniquement de proxies de collision simplifiés ; l'ancien code de shaders d'eau a été retiré. Les animations morphologiques Blender sont lues par `FountainSystem`, avec une horloge partagée entre visiteurs et des ressources graphiques communes aux instances. Les systèmes ne créent aucun objet par image.

Le banc utilise 2 952 triangles et 3 matériaux. La structure de la fontaine utilise 7 136 triangles. Fontaine complète avec eau, jet central et six jets latéraux : 16 880 triangles et 18 appels de rendu hors éclairage. Les cinq fichiers pèsent 2 552 236 octets au total. Ce sont des budgets d'assets ; les performances à 72–90 Hz restent à mesurer sur casque physique.

Validation : `npx tsc --noEmit`, `node scripts/verify-estate-assets.mjs`, rendus de la fontaine isolée et du domaine sans diagnostics, inspection rapprochée du banc et capture VR en exécution. Le vérificateur contrôle les données GLB, l'absence de ressources externes, les budgets de triangles, les cibles de morphing, la continuité de chaque boucle de quatre secondes et la présence de mouvement pendant chaque seconde. Le débogage ECS a confirmé l'avancement des sept jets.

Pour régénérer, lancer dans l'ordre via `node scripts/blender-mcp.mjs execute_blender_code <script>` :

1. `scripts/blender-estate-models.py`
2. `scripts/blender-estate-water.py`
3. `scripts/blender-estate-refine.py`
4. `scripts/blender-estate-finalize.py`
5. `scripts/blender-estate-export.py`
6. `scripts/blender-estate-organize.py`

Ces scripts partagent un espace d'exécution dans Blender. Ils créent une scène dédiée et conservent les scènes déjà ouvertes. Après export, exécuter `node scripts/verify-estate-assets.mjs`. Le chemin de projet est déclaré au début du script de modèles.

La collecte des prompts, scripts, captures et données de scène du MCP Blender a été désactivée après un blocage du contrôle automatique. Le serveur indique conserver des compteurs anonymes d'usage.
