# Corrections des avatars — 12 septembre 2026

Révision archivée. Les avatars actifs sont décrits dans [FRANCOIS-AVATARS.md](FRANCOIS-AVATARS.md).

Les assets actifs `courtMale` et `courtFemale` remplacent la révision organic.
Les anciennes versions sont conservées dans `artifacts/avatars/refined/before/`.
Toutes les opérations de modélisation passent par le MCP Blender, sans primitives.

## Corrections visibles

- Têtes avancées de 45 mm, avec transition dans le cou ; la frontière anatomique
  du cou est prolongée par une surface continue jusqu'au col. L'ancien raccord
  arrière en languette est supprimé. `profiles.png` utilise une rotation de 90°.
- Implantation capillaire découpée autour des oreilles. Les oreilles restent en
  matériau peau. Les coiffures ont 500 guides de présentation, dont 200 répartis
  explicitement sur la ligne frontale, avec 2 mèches fines par guide et des teintes
  variables. Le chignon, la barbe et les mèches libres sont conservés.
- Colliers, médaillons et galons frontaux projetés sur la surface des pourpoints
  après optimisation. Relief mesuré de 3,299995 à 3,300004 mm : voir le rapport
  d'optimisation `artifacts/avatars/refined/budget-report.json`.
- Iris marron pour l'homme et verts pour la femme ; pupilles noires conservées.
- Souliers masculins en cuir espresso, avant arrondi, semelle cousue et talon large.
  Souliers féminins en cuir prune, avant plus effilé, semelle cambrée et talon plus
  étroit et haut. Les brides et boucles sont projetées sur les empeignes.

## Fichiers

| Asset | Triangles | Octets |
| --- | ---: | ---: |
| `public/gltf/avatars/courtMale.glb` | 92 505 | 10 735 580 |
| `public/gltf/avatars/courtFemale.glb` | 97 041 | 9 086 772 |

Source finale : `artifacts/avatars/refined/renaissance-refined.blend`.
Vues : `duo.png`, `portraits.png`, `profiles.png`, `souliers.png`, `talons.png` dans
ce même répertoire. La robe est masquée uniquement dans les vues des souliers.
Le manifeste utilise `refined-20260912-r2` pour renouveler le cache.

## Animation et vérification

Les 15 visèmes et les quatre animations restent présents. Le vérificateur des GLB
réels valide les morphs, les poids, les mouvements et les clones indépendants.
Les 37 tests d'avatars, d'IK, de cheveux et de voix réussissent.

Le solveur existant simule désormais 4 500 points capillaires pour l'homme et
180 pour les mèches libres féminines. Le chignon reste attaché. Dans le banc runtime
avec pause/step ECS et rotation de ±0,65 rad, les racines ne se déplacent pas et
l'erreur de longueur après 3 images est de 0,944 mm pour l'homme et 0,333 mm pour
la femme. Rapport : `runtime-hair.json`. Le banc est retiré de `src/index.ts` après
vérification. Ces observations viennent de XR émulée ; elles ne mesurent pas les
performances d'un casque physique.

Blender conserve des particules HAIR éditables : 300 parents pour chaque coiffure,
600 pour la barbe, avec Hair Dynamics. Les surfaces de présentation complètent les
guides natifs sur la ligne frontale. Les émetteurs sont masqués pour éviter un double
rendu ; les réafficher pour l'édition des particules. La simulation GLB reste le
solveur de mèches décrit dans `ORGANIC-AVATARS.md`.

Fabrication : `blender-refined-avatars.py`, puis `blender-refined-export.py`.
`blender-refined-render.py` et `blender-refined-detail-save.py` génèrent les vues et
enregistrent la scène éditable. Le script `hair-finish` est une correction ponctuelle
de l'ancienne distribution à 4 mèches par guide ; ne pas le relancer après une
construction neuve, qui incorpore déjà la distribution finale. Tous les scripts
s'exécutent via `scripts/blender-mcp.mjs` avec `blender-refined-request.json`.
