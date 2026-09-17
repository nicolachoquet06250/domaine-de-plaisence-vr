# Avatars Renaissance pour VRChat

Projet cible : `Bienvenue au domaine - Avatars`, Unity 2022.3.22f1, SDK Avatars 3.10.5.

## Utilisation

Ouvrir `Assets/DomaineAvatars/Avatars-Renaissance.unity` dans Unity. La scène contient les deux avatars, une caméra et un éclairage de présentation.

Utiliser les prefabs configurés, plutôt que glisser directement les FBX dans une autre scène :

- `Assets/DomaineAvatars/courtMale/courtMale-VRChat.prefab`
- `Assets/DomaineAvatars/courtFemale/courtFemale-VRChat.prefab`

Chaque prefab possède un Animator Humanoid, un VRC Avatar Descriptor et un Pipeline Manager sans identifiant de publication. Les couches d'animation VRChat restent sur leurs réglages par défaut.

## Configuration

- FBX et textures copiés depuis les exports Renaissance locaux, sans modifier les sources.
- Matériaux Standard extraits, couleurs et normales reliées ; métal et rugosité repris du rapport Blender.
- Deux os d'épaules ajoutés dans chaque prefab pour respecter la hiérarchie demandée par le SDK. Avatar Humanoid séparé avec pose de référence des bras horizontale, pose du modèle conservée.
- Point de vue centré sur les yeux : environ 1,60 m pour l'homme et 1,52 m pour la femme.
- Mode Lip Sync : `Viseme Blend Shape` ; renderer du visage relié.
- Les 15 entrées suivent l'ordre VRChat : `sil, PP, FF, TH, DD, kk, CH, SS, nn, RR, aa, E, I, O, U`, associées à `viseme_*`.
- Les animations FBX `Idle`, `Walking`, `StrafeLeft`, `StrafeRight` sont conservées. La locomotion utilise les couches VRChat par défaut.

## Vérification

Les rapports se trouvent dans `Logs/domaine-avatars-import.json` et `Logs/domaine-avatars-validation.txt`. L'aperçu Unity est `Logs/domaine-avatars-preview.png`.

Le validateur recharge les prefabs, vérifie le Humanoid, la hiérarchie des épaules, la pose des os par rapport au FBX, les références des matériaux et les 15 déformations réelles du visage via `SkinnedMeshRenderer.BakeMesh`.

Validation locale dans Unity ; aucun test en jeu ni upload VRChat effectué. Ces modèles conservent leur densité d'origine (environ 93 000 et 97 000 triangles, 20 et 23 renderers, 25 matériaux chacun). Aucune optimisation Quest, articulation des doigts ou dynamique des cheveux ajoutée.

Le menu `Domaine > Importer et configurer les avatars Renaissance` régénère les matériaux, les prefabs et la scène de présentation : ne pas le relancer après des personnalisations à conserver.
