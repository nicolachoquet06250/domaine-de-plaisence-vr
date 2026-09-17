# Quatre bustes historiques du château

Les quatre bustes utilisent la topologie anatomique CC0 MakeHuman, retouchée dans Blender via le MCP. Les paupières, les lèvres, les oreilles et le menton appartiennent au maillage anatomique. Aucun opérateur de primitive n'est utilisé par le générateur.

| Identité | Emplacement local au château | Référence observée |
|---|---|---|
| François Ier | Chambre ouest, `[-12.8, 6.14, 1]` | [Portrait de François Ier, Louvre, Clouet](https://collections.louvre.fr/ark%3A/53355/cl010062204) : bonnet incliné à plume, nez allongé, barbe arrondie et moustache raccordée. |
| Louis XIV | Chambre est, `[12.8, 6.14, 1]` | [Portrait par Rigaud, Versailles](https://www.chateauversailles.fr/ressources-pedagogiques/domaines-artistiques/peinture/louis-xiv-grand-costume-royal-hyacinthe-rigaud) : visage plus plein, perruque longue bouclée, cravate et manteau. Image de travail téléchargée depuis [Smarthistory](https://smarthistory.org/rigaud-louis-xiv/). |
| Catherine de Médicis | Salon ouest, `[-6.1, 1.74, -4.25]` | [Portrait d'après Clouet, L'Histoire par l'image](https://histoire-image.org/oeuvres/catherine-medicis) : coiffe en cœur, voile de veuve et petite fraise. |
| Anne de France | Salon est, `[6.1, 1.74, -4.25]` | [Triptyque du Maître de Moulins, Jean Hey](https://www.moulins-tourisme.com/decouvrir/ambiances-bourbonnaises/triptyque-du-maitre-de-moulins/) : visage allongé, coiffe à pans, couronne et encolure. Il s'agit d'Anne de Beaujeu, pas d'Anne de Bretagne. |

Les portraits téléchargés sont dans `artifacts/busts-makehuman/reference`. Ils servent de références visuelles et ne sont pas incorporés aux GLB. La sculpture et les parties non visibles dans ces portraits sont une interprétation, pas une reconstruction mesurée. L'aspect marbre ivoire des bustes existants est conservé.

## Construction et fichiers

- Source éditable : `artifacts/busts-makehuman/bustes-historiques-makehuman.blend`, avec la galerie des quatre modèles et une scène du mobilier nettoyé.
- Génération : `scripts/blender-makehuman-busts.py`, puis `scripts/blender-busts-finish.py` et `scripts/blender-busts-export.py` via `scripts/blender-mcp.mjs`.
- Anatomie : `artifacts/avatars/organic/reference/makehuman-base.obj`, licence MakeHuman conservée au même endroit. Les quatre déformations de visage sont distinctes ; les exports conservent toute la géométrie faciale subdivisée.
- Coiffures : masse continue, contour anatomique autour des oreilles et mèches fines comme les avatars. La barbe de François est un relief du visage, avec fibres enracinées sur ce relief.
- Quatre grooms natifs de cheveux, chacun avec 180 parents, 16 enfants et dynamique/gravité activables, sont conservés et masqués dans la source. Les bustes de marbre de la visite utilisent des maillages statiques ; ils ne simulent pas des cheveux vivants.
- Exports : `public/gltf/castle/bustFrancoisI.glb`, `bustLouisXIV.glb`, `bustCatherineMedici.glb`, `bustAnneFrance.glb`. Cinq primitives de matériau par buste, environ 77 k triangles pour trois modèles et 128 k pour la perruque de Louis.
- Intégration : `src/assets.ts`, scènes `visit`, `plaisance` et module `castle-blender`. Les IDs des deux bustes de chambre sont conservés. Caméras de contrôle `bust-francois`, `bust-louis`, `bust-catherine`, `bust-anne`.

## Contrôles

`node scripts/verify-makehuman-busts.mjs` contrôle les quatre GLB, leurs volumes, leur base à zéro et les quatre références uniques dans chaque scène. Le même contrôle compare les triangles du mobilier avant/après : exactement 4 160 triangles d'anciens bustes retirés et 87 930 triangles restants identiques à 10 µm près, socles compris. Le rapport est `artifacts/busts-makehuman/verification.json`.

`npx tsc --noEmit` et `npm run build` passent. Les avertissements préexistants de taille de bundle et d'annotations tierces restent présents. Les images de l'atelier sont des contrôles de modélisation ; les contrôles d'intégration passent par le rendu IWSDK. Les performances sur casque physique ne sont pas mesurées.

Le rendu IWSDK de la galerie confirme les quatre assets et leurs IDs visibles. Le gros plan final de Louis confirme le visage anatomique conservé après optimisation. Le rendu du module château, caméra `bust-catherine`, confirme le nouveau portrait dans le salon et son contact avec le socle, sans ancien buste superposé. L'ouverture de la scène complète `visit` a ensuite rencontré des pertes de connexion/temporisations de l'éditeur (`scene_open_not_ready`, `browser_not_ready`). La capture runtime de l'accueil fonctionne, mais la série complète de profils et la vérification runtime des quatre pièces n'ont donc pas pu être achevées. Ne pas présenter ces derniers contrôles comme réussis ; `scripts/render-makehuman-busts.mjs` permet de les reprendre quand le bridge de l'éditeur est prêt.
