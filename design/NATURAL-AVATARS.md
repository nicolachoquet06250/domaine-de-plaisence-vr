# Avatars Renaissance remodelés — 12 septembre 2026

Cette version est archivée. Les assets actifs ont été remplacés par la révision
anatomique avec cheveux simulés, décrite dans [ORGANIC-AVATARS.md](ORGANIC-AVATARS.md).

Un courtisan grenat et une dame de cour bleu nuit remplacent les deux GLB utilisés
par l'application. La direction reste Renaissance stylisée : ces personnages
ne sont pas des humains photoréalistes ni des scans anatomiques.

## Construction dans Blender

Toutes les opérations sont exécutées avec `execute_blender_code` du MCP Blender,
via le client existant `scripts/blender-mcp.mjs`. Aucun opérateur de primitive
Blender n'est utilisé. Les nouveaux volumes sont des maillages définis par leurs
sommets et faces : sections anatomiques interpolées, surfaces de paupières,
raccords de lèvres, mèches en rubans et sections de vêtements. Le squelette,
les quatre animations et les maillages de mains déjà retopologisés sont repris.

Le visage comprend une surface continue peau–lèvres–cavité, deux arcades dentaires,
une langue et une déformation distribuée sur le menton. Chaque visage exporte
les 15 noms `viseme_sil`, `viseme_PP`, `viseme_FF`, `viseme_TH`, `viseme_DD`,
`viseme_kk`, `viseme_CH`, `viseme_SS`, `viseme_nn`, `viseme_RR`, `viseme_aa`,
`viseme_E`, `viseme_I`, `viseme_O`, `viseme_U` attendus par le moteur vocal.

Les surfaces hors visage sont réduites et regroupées par matériaux et visibilité
en première personne. La topologie des morphs n'est pas décimée. Les points
d'attache des mains et les métadonnées de prise XR sont conservés.

## Livrables

- `public/gltf/avatars/courtMale.glb` : 57 377 triangles, 3 545 884 octets.
- `public/gltf/avatars/courtFemale.glb` : 59 300 triangles, 3 603 900 octets.
- `artifacts/avatars/natural/renaissance-natural.blend` : scène Blender éditable.
- `artifacts/avatars/natural/renaissance-natural-work.blend` : surfaces avant réduction.
- `artifacts/avatars/natural/duo.png`, `portraits.png`, `visemes.png` : rendus Blender.
- `public/scenes/avatars-natural-review.iwsdk.scene.json` : présentation éditable
  utilisant les deux mêmes assets que l'application.
- `artifacts/avatars/natural/before/` : sauvegarde des anciens GLB.

Le manifeste conserve `courtMale` et `courtFemale`, avec un paramètre de version
d'URL actualisé pour éviter de recharger les anciens modèles en cache.

## Reproduction

Lancer dans cet ordre, avec Blender et son serveur MCP disponibles :

```powershell
node scripts/blender-mcp.mjs execute_blender_code scripts/blender-natural-inspect.py scripts/blender-natural-avatars.json
node scripts/blender-mcp.mjs execute_blender_code scripts/blender-natural-avatars.py scripts/blender-natural-avatars.json
node scripts/blender-mcp.mjs execute_blender_code scripts/blender-natural-export.py scripts/blender-natural-avatars.json
node scripts/blender-mcp.mjs execute_blender_code scripts/blender-natural-render.py scripts/blender-natural-avatars.json
node scripts/blender-mcp.mjs execute_blender_code scripts/blender-natural-visemes.py scripts/blender-natural-avatars.json
node scripts/blender-mcp.mjs execute_blender_code scripts/blender-natural-save.py scripts/blender-natural-avatars.json
```

L'export écrit d'abord dans `artifacts/avatars/natural/`. Copier les GLB validés
vers `public/gltf/avatars/` pour une nouvelle publication locale. Relancer la
construction avant de relancer l'optimisation ; elle ne doit pas s'accumuler.

## Vérification

- `npx tsc --noEmit`.
- Le vérificateur GLB contrôle les 15 morphs, les poids normalisés, les quatre
  animations bouclées, leurs déplacements réels et l'indépendance des clones.
  Rapport : `artifacts/avatars/natural/rig-verification.json`.
- Tests d'avatars, d'IK, de voix et de visèmes : 31 tests réussis. Le test du
  vérificateur réussit aussi après ajout des morphs manquants dans sa fixture
  synthétique historique ; il rejette désormais explicitement leur absence.
- L'éditeur IWSDK valide la scène de présentation sans diagnostic ; les deux
  avatars apparaissent dans `visibleNodeIds`. La vue duo mesure 49 appels de rendu.
- Le banc existant `tests/lipsync-browser-harness.ts` est activé temporairement
  puis retiré de `src/index.ts`. Deux flux WebRTC réels utilisent une phrase
  française synthétique, sans microphone physique ni sortie audible.
  Résultat : 14 formes parlées locales et 14 distantes observées, 939 mises à jour,
  fermeture après coupure en 562 ms. Rapport :
  `artifacts/avatars/natural/browser-verification.json`.

Les mesures de voix proviennent d'un essai local dans le navigateur avec XR émulée.
Elles ne mesurent ni la précision phonétique en français ni les performances
sur casque physique. Les nuances très fines des cheveux et de la peau restent
stylisées ; les limites acoustiques de HeadAudio sont décrites dans AVATAR-LIPSYNC.md.
