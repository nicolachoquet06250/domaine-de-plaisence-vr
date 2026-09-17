# Accueil Renaissance — contrat de modèle

Source de génération : `scripts/blender-arrival-realistic.py`, à exécuter dans Blender via le MCP existant. Le script crée une scène Blender séparée, sans supprimer les autres scènes et sans modifier le namespace des générateurs du château.

Livrables après exécution :

- `public/gltf/arrival/arrival.glb`
- `artifacts/arrival-realistic/arrival-realistic.blend`
- `artifacts/arrival-realistic/asset-stats.json`

Le modèle remplace le prototype `arrival` avec la même origine et les mêmes conventions : mètres, Y vertical, terrasse de rayon 8 m, sol à Y=0, piliers à X=±2,6 m et Z=−4 m. Les placements existants du panneau, du joueur et des deux cyprès restent valides. Le passage central demeure entièrement libre.

Le dallage et la rose des vents sont tessellés à la même altitude, sans triangles de revêtement superposés. Le support continu reste 24 mm sous le dallage. Les vraies formes de moulures, cannelures, volutes, balustres, denticules, lanternes et jardinières remplacent les volumes simples. Les matériaux sont mutualisés et les géométries regroupées par famille sémantique et matériau ; les textures PBR sont embarquées dans le GLB.

Intégration du manifeste, à effectuer après génération : conserver l'ancien prototype sous le nom local `arrivalCollisionProxy` pour `createStaticCollision(arrivalCollisionProxy)`, et enregistrer `arrival` avec l'URL relative à BASE_URL `gltf/arrival/arrival.glb`, de type `AssetType.GLTF`. Aucune modification des transforms de la scène d'accueil n'est nécessaire.

Les pelouses doivent rester hors du rayon 8,05 m de la terrasse. Les cyprès existants restent à X=±5 m, Z=−3 m ; leurs jardinières ont un rayon extérieur de 0,785 m et un dessus de terre à Y=0,135 m. Le GLB n'inclut pas la végétation, conservée dans les assets de jardin réutilisés par cette scène.

Intégration effectuée via le MCP Blender : GLB de 2 544 316 octets, 52 900 triangles, 24 groupes. Le manifeste charge maintenant ce GLB. Le rendu natif de l'accueil et le runtime XR ont été inspectés ; le choix Homme/Femme remplace bien l'aperçu. TypeScript et compilation de production validés. Les sources Blender éditables sont présentes dans ce dossier. Les performances sur casque physique restent à mesurer.
