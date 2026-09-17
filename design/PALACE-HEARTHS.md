# Cheminées du château

Les quatre foyers (est/ouest, rez-de-chaussée/étage) utilisent le même insert Blender : trois bûches avec écorce, cernes et fissures, braises, fond en briques et protection ouverte en fer forgé à volutes. Le parement recouvre le panneau noir existant, avec un espace entre surfaces pour éviter le scintillement.

- Source éditable : `artifacts/castle/foyers-bois-fer-forge.blend`.
- Générateur MCP : `scripts/blender-hearth.py`, export limité à la scène active.
- GLB partagé : `public/gltf/castle/hearth.glb`, 12 256 triangles, 6 matériaux, environ 652 Kio.
- Flammes : 32 triangles par foyer, shader de turbulence, plans croisés pour les vues obliques et stéréo. La simulation volumétrique Blender n'est pas exportée dans le navigateur.
- Chaque foyer dispose d'une petite lumière orange vacillante, de portée 3 m, sans ombres supplémentaires. Les flammes et la lumière s'arrêtent visuellement à plus de 28 m.
- Le système clone uniquement le matériau animé de chaque feu et le libère au changement de scène ; géométries et matériaux du GLB restent partagés.

Composition : nœuds `hearth-{east,west}-{salon,gallery}` dans la scène plate `public/scenes/plaisance.iwsdk.scene.json` et le module de château. Origine sur la tablette, face +Z vers la pièce ; grilles devant les bûches. `scripts/integrate-hearths.mjs` met à jour uniquement ces nœuds et les deux vues de détail, sans réaplatir la scène.

Vérification : `node scripts/verify-hearths.mjs` contrôle les dimensions, le budget, les quatre placements, les directions et l'absence d'anciens modèles dans le GLB. Les rendus IWSDK `hearth-detail` et `hearth-upper` permettent de vérifier le montage. Les captures runtime et l'avancement ECS confirment l'animation ; l'intensité du foyer est a été observée à 2,81 puis 3,65 cd. Les mesures sur ordinateur ne constituent pas une mesure de fréquence d'images dans un casque physique.

Référence de workflow : iwsdk-scene-composer ; capacité IWSDK initiale `sha256:87cb5f614b2fa34a6184b828df615a6e92a6056b668de6ee6d8333f62b47b9df`.

## Raccordement aux murs

Les quatre fenêtres centrales derrière les foyers ont été supprimées, y compris vitrages, croisillons, encadrements et appuis. Les baies sont rebouchées en calcaire assorti ; les huit fenêtres voisines des murs latéraux restent ouvertes. Deux massifs maçonnés de 2,60 m de large relient les cheminées au mur et au plafond. Leur face intérieure touche l'arrière des cadres dorés à x = ±19,965 m ; les surfaces réfléchissantes sont à x = ±19,925 m, devant la maçonnerie.

La dernière source Blender du château est `artifacts/castle/chateau-plaisance-cheminees-murs.blend`. La modification ciblée est reproductible avec `scripts/blender-chimney-walls.py` ; les générateurs d'architecture et d'intérieur sont également corrigés. `scripts/verify-chimney-walls.mjs` contrôle les vitrages supprimés et conservés, les murs, les collisions et l'alignement des miroirs. Les vues `chimney-wall-exterior` et `chimney-wall-interior` montrent les raccords des deux côtés du mur.
