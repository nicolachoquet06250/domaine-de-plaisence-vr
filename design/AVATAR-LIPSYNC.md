# Synchronisation labiale des personnages de cour

**Version du 12 septembre 2026 :** les GLB actifs ont été remplacés par les
avatars remodelés via le MCP Blender, sans création de primitives. Le fichier
éditable actuel est `artifacts/avatars/natural/renaissance-natural.blend`.
Voir [la refonte et ses validations](NATURAL-AVATARS.md). La chaîne vocale décrite
ci-dessous est conservée ; les chemins `lipsync/` documentent la version antérieure.

Les deux avatars disposent d'une bouche ouverte en géométrie, de lèvres,
d'une cavité buccale, de dents et d'une langue. Le fichier Blender éditable est
`artifacts/avatars/lipsync/renaissance-court-lipsync.blend`. Les GLB utilisés par
l'application sont `public/gltf/avatars/courtMale.glb` et `courtFemale.glb`.

## Formes et export Blender

Quinze shape keys, compatibles avec les visèmes Oculus, regroupent les sons qui
se ressemblent visuellement. Elles ne représentent pas un alphabet phonétique
exhaustif. Les transitions mélangent les formes et reviennent au repos au silence.

| Shape key | Famille d'articulation |
| --- | --- |
| sil | Repos, bouche fermée |
| PP | P, B, M : lèvres jointes |
| FF | F, V : lèvre inférieure sous les incisives |
| TH | Langue entre les dents |
| DD | T, D : langue levée |
| kk | K, G |
| CH | CH, J |
| SS | S, Z |
| nn | N, L |
| RR | R |
| aa | Voyelle ouverte |
| E | Voyelle intermédiaire étirée |
| I | Voyelle étroite étirée |
| O | Voyelle arrondie ouverte |
| U | Voyelle arrondie fermée |

Le script `scripts/blender-lipsync.py`, exécuté avec le MCP Blender via
`scripts/blender-mcp.mjs` et `scripts/blender-lipsync.json`, repart du fichier
`artifacts/avatars/renaissance-court.blend`. Il préserve les rigs, mains, cheveux
et les quatre animations Idle, Walking, StrafeLeft et StrafeRight. La découpe de
la bouche suit uniquement la surface du visage et son contour réel ; le cou
et les joues conservent une surface fermée. Le rendu de contrôle est
`artifacts/avatars/lipsync/visemes.png`.

## Voix et animation

Le bouton existant « Activer le micro » autorise la capture. `VoiceSession`
branche cette capture vers un AudioWorklet sans sortie audio : le joueur ne
s'entend pas en écho. Les autres joueurs utilisent le flux WebRTC déjà reçu,
sans ajouter de messages d'animation au protocole du salon.

`SpeechVisemes` utilise les caractéristiques MFCC et le classificateur acoustique
HeadAudio distribué avec le projet. Le traitement reste dans le navigateur ;
il n'enregistre pas les propos et ne transmet rien à un service de transcription.
L'audio du salon conserve sa transmission WebRTC habituelle. Le modèle et le
worklet sont chargés une fois par contexte ; les poids sont réutilisés à chaque
image. L'analyse distante est suspendue au-delà de la portée vocale de 25 m.

Un délai de 60 ms est ajouté à l'audio reçu pour rapprocher son rendu de la
fenêtre d'analyse. Les formes sont interpolées indépendamment des animations
du corps et des contraintes des manettes. Le visage local conserve le calque
visible dans les miroirs et caché de la caméra à la première personne.
La coupure du micro détruit sa branche d'analyse. Pour les autres joueurs,
la bouche suit la fin de l'audio, y compris celui déjà présent dans le tampon RTP.

## Validation et limites

- TypeScript, tests de voix, de visèmes, d'avatars et d'IK : 28 tests réussis.
- Vérification des deux GLB : 15 morphs nommés, déformations finies, poids de
  squelette normalisés, quatre animations, clones de squelette et de bouche
  indépendants. Rapport : `artifacts/avatars/lipsync/rig-verification.json`.
- Banc d'essai navigateur : `tests/lipsync-browser-harness.ts`, activation
  temporaire dans `src/index.ts` via `installLipSyncBrowserHarness(world)`.
  Il utilise deux connexions WebRTC réelles dans un salon isolé et une phrase
  française synthétique locale, avec sortie sonore coupée. Il n'utilise aucun
  microphone physique. Retirer cet import après l'essai.
- Dernier essai réussi : 14 formes actives observées localement, 13 sur le flux
  reçu et fermeture après coupure du micro. Les détails sont conservés dans
  `artifacts/avatars/lipsync/browser-verification.json`. Les délais de ce test
  local ne prédisent pas ceux d'une connexion Internet ou d'un casque physique.

La reconnaissance est une estimation acoustique. Le modèle fourni par
[HeadAudio](https://github.com/met4citizen/HeadAudio) est entraîné en anglais :
certains sons français, notamment les voyelles nasales et les variantes du R,
sont approximés. La qualité dépend du micro, de la voix et du bruit ambiant.
La variété des mouvements vérifiée avec une phrase française ne constitue pas
une mesure de précision phonétique. La latence et la charge sur un Quest 3
physique restent à mesurer. Si AudioWorklet est indisponible, la voix continue
et le visage reste au repos.
