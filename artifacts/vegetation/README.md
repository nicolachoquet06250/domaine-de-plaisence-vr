# Pelouse en relief et roses sur tiges

Deux scripts Blender MCP autonomes, à exécuter séquentiellement :

1. `scripts/blender-vegetation-relief.py` importe le matériau du sol original et génère `public/gltf/vegetation/estateLawnRelief.glb` ainsi que `arrivalLawnRelief.glb`.
2. `scripts/blender-flower-stems.py` remplace les GLB `parterre` et `urn` avec les mêmes formes florales, des corolles relevées de 15/14 cm, 82 tiges enracinées, des sépales et des feuilles basses. Il garde une copie originale unique dans ce dossier pour que les répétitions ne doublent pas les tiges.

Le domaine conserve son emprise de 70 × 90 m et son sol de collision y=0. La surface végétale présente un relief de 0 à 22 mm et 22 133 brins courbés à section pliée, hauts de 6,5 à 12,8 cm. Les brins évitent les chemins, parterres de gravier, château, murets et pieds de cyprès. Vingt groupes permettent l'élimination des zones hors champ, sans transparence ni ombres coûteuses sur les brins.

L'accueil reçoit une pelouse annulaire indépendante autour de la terrasse, entre les rayons 8,01 et 20 m, avec 9 065 brins et quatre groupes. La terrasse et ses collisions restent inchangées.

Intégration dans le manifeste partagé : conserver l'ID `ground` et changer uniquement son URL en `gltf/vegetation/estateLawnRelief.glb`; ajouter `arrivalLawnRelief` et le placer à l'origine de la scène d'accueil. Ne pas conserver le sol visuel plat sous le nouveau sol du domaine.

Contrôles :

- `npx tsc --noEmit` avant les essais.
- `python scripts/verify-vegetation-authoring.py` contrôle la géométrie produite par les mêmes fonctions, les zones couvertes, les exclusions et les budgets sans exécuter Blender.
- Après les exports : `node scripts/verify-vegetation.mjs` contrôle les GLB réellement livrés, les hauteurs, les empreintes, l'absence de brins dans les chemins et le contact de chaque tige avec sa corolle et le sol.
- Revue visuelle dans l'éditeur natif : vue générale et vue à hauteur humaine près d'une bordure de pelouse dans chaque scène, puis gros plan d'un parterre et d'une urne. Les contrôles géométriques ne remplacent pas ces vues.

Les fichiers `.blend` produits sont `dimensional-lawns.blend` et `rooted-garden-flowers.blend`, avec statistiques et vérification JSON dans ce même dossier.
