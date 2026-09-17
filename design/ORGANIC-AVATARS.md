# Avatars anatomiques et cheveux simulés — 12 septembre 2026

Version archivée : les assets actifs sont décrits dans [REFINED-AVATARS.md](REFINED-AVATARS.md).

Les assets `courtMale` et `courtFemale` conservent la direction Renaissance stylisée.
Le visage utilise maintenant la topologie anatomique de MakeHuman, avec des mentons
plus projetés et des lèvres modelées dans le visage. Le pourpoint et les manches ont
plus de profondeur ; les mollets masculins sont élargis avec un galbe postérieur.
La femme porte un chignon haut avec mèches libres. L'homme porte une barbe courte
fournie, au contour lissé, et une moustache ; la barbe suit les visèmes.

Les opérations de modélisation ont été exécutées par `execute_blender_code` du MCP
Blender, via `scripts/blender-mcp.mjs`. Aucun opérateur de primitive n'est utilisé.
Le squelette, les mains et les quatre animations existantes sont conservés.

## Référence et licence

Le visage, les globes oculaires, les dents et la langue dérivent de la base officielle
[MakeHuman](https://github.com/makehumancommunity/makehuman/blob/master/makehuman/data/3dobjs/base.obj),
téléchargée le 12 septembre 2026. Le fichier porte explicitement la licence CC0 ;
voir aussi la [politique de licence officielle](https://static.makehumancommunity.org/about/license.html).
La source et sa licence sont conservées dans `artifacts/avatars/organic/reference/`.

## Cheveux et gravité

Le `.blend` contient trois véritables systèmes HAIR persistants : 112 guides de
coiffure masculine, 600 poils de barbe, 128 guides de coiffure féminine, avec
18 enfants interpolés par guide au rendu et Hair Dynamics activé. Les émetteurs
`Particules ...` sont masqués par défaut pour éviter de doubler les surfaces de
mèches de l'aperçu. Pour les coiffer dans Blender, réafficher ces émetteurs et
masquer les surfaces de présentation correspondantes. Le chignon est une masse
attachée avec fibres de surface.

Un GLB ne transporte pas la simulation native de Blender. Les fichiers exportent
donc une surface de mèches, des guides `hairDynamics` et l'attribut `_HAIR_PARTICLE`.
`src/hair-particles.ts` simule réellement ces guides dans l'application : gravité
mondiale de 9,81 m/s², intégration à pas fixe 1/120 s, inertie, amortissement,
contraintes de longueur, racines fixées à l'os Head et collisions ellipsoïdales
approximatives autour du crâne et des épaules. Ce solveur de particules est distinct
des corps rigides Havok ; le projet n'active pas Havok pour cette fonction.

Les cheveux masculins ont 1 008 points simulés ; les mèches libres féminines en ont
180. Le chignon et les cheveux plaqués restent attachés ; la barbe suit la bouche.
Les géométries déformées appartiennent à chaque avatar et sont libérées à son retrait,
sans modifier les ressources partagées. Les déplacements brusques de plus de 50 cm
réinitialisent les mèches pour supporter les téléportations.

## Livrables actifs

| Asset | Triangles | Octets |
| --- | ---: | ---: |
| `public/gltf/avatars/courtMale.glb` | 92 412 | 9 720 516 |
| `public/gltf/avatars/courtFemale.glb` | 99 216 | 8 460 260 |

Le budget du vérificateur passe à 100 000 triangles et 12 Mo pour conserver
l'anatomie et les fibres. Les anciens modèles sont sauvegardés dans
`artifacts/avatars/organic/before/`. Le manifeste utilise une nouvelle version d'URL.

- `artifacts/avatars/organic/renaissance-organic.blend` : scène finale éditable.
- `artifacts/avatars/organic/renaissance-organic-work.blend` : maillages avant optimisation.
- `artifacts/avatars/organic/duo.png`, `portraits.png`, `profiles.png`, `visemes.png` : aperçus.
- `public/scenes/avatars-natural-review.iwsdk.scene.json` : scène de revue avec les assets actifs.

## Vérifications

Compilation TypeScript et build de production réussis. 37 tests couvrent les avatars,
l'IK, les visèmes, la voix, le solveur, le déplacement réel des sommets et la libération
des géométries. `verification.json` valide les GLB réels : poids normalisés, quatre
animations, 15 morphs finis, indépendance des clones et indices des particules.

Le banc temporaire `tests/hair-browser-harness.ts`, exécuté dans le runtime, a été
avancé avec pause/step ECS. Une rotation de ±0,65 rad produit une réponse indépendante
des mèches, sans déplacement des racines ; l'erreur de longueur observée reste sous
2 mm. Résultat : `runtime-hair-diff.json`. Le banc a ensuite été retiré de `src/index.ts`.

Le banc WebRTC local, sans microphone physique, a observé 10 visèmes parlés locaux
et 11 distants, puis la fermeture de la bouche après coupure. Le délai mesuré était
de 3 299 ms pendant un rendu Blender concurrent ; ce résultat ne constitue pas une
mesure de latence audio. Voir `browser-lipsync.json`. Les 15 poses sont aussi contrôlées
directement dans les fichiers et sur la planche Blender.

Les mesures utilisent un navigateur avec XR émulée. Les performances sur casque
physique et la tenue de plusieurs avatars à 72–90 Hz restent à mesurer.

## Scripts de fabrication

`blender-organic-avatars.py` construit les maillages et guides ; `blender-organic-export.py`
optimise et exporte ; `blender-organic-eye-finish.py` préserve les iris et lisse le cou.
Les scripts `native-groom` et `native-style` permettent de reconstruire les caches
persistants des particules dans la scène finale. `render`, `visemes` et `profiles-save`
produisent les aperçus et enregistrent le `.blend`. Tous s'exécutent via le client MCP
avec `scripts/blender-organic-request.json`. Charger au préalable la source des rigs
avec `blender-natural-inspect.py`. Repartir de la construction avant une nouvelle
optimisation : les réductions ne sont pas destinées à s'accumuler.
