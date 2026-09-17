# Avatars Renaissance — export FBX

Export du 13 septembre 2026, Blender 5.2.1 LTS.

## Fichiers

- `courtMale/courtMale.fbx` : homme, dernière correction de moustache, 93 339 triangles.
- `courtFemale/courtFemale.fbx` : femme, 97 439 triangles.
- Chaque dossier `Textures` contient les PNG du visage, des fibres capillaires et les textures de couleur/normales des cheveux. Les textures sont également incorporées au FBX.
- `preview-fbx.png` : aperçu obtenu après réimportation des deux FBX dans Blender.
- `verification-blender.json` : résultats des contrôles de réimportation.
- `export-report.json` : provenance, empreintes SHA-256 et paramètres des matériaux.

Source : `artifacts/avatars/moustache/renaissance-moustache.blend`, qui contient les deux avatars. Le fichier source et les assets WebXR restent inchangés. Les couleurs de sommets du visage et des fibres ont été converties en textures UV de 2 048 × 2 048 pixels pour faciliter le transfert des matériaux.

## Import dans Unity

1. Créer un projet Avatars avec VRChat Creator Companion et sa version de Unity prise en charge.
2. Copier les dossiers complets `courtMale` et `courtFemale` dans `Assets`.
3. Pour chaque FBX, ouvrir **Rig**, choisir **Humanoid**, puis **Create From This Model** et **Apply**. Vérifier **Configure** ; utiliser **Pose > Enforce T-Pose** si nécessaire. La pose de repos exportée conserve les bras abaissés de la source.
4. Conserver **Import BlendShapes** activé. Les quatre animations existantes sont `Idle`, `Walking`, `StrafeLeft` et `StrafeRight` (le nom peut être préfixé par celui du modèle). VRChat peut utiliser ses propres animations de déplacement.
5. Dans **Materials**, extraire les matériaux si nécessaire et vérifier les textures. Les PNG `*-color-*` servent de couleur de base ; `*-hair-normal.png` doit être importé comme **Normal map** et affecté à la normale du matériau capillaire. Le rapport donne la rugosité et le métal de chaque matériau ; dans un shader utilisant Smoothness, partir de `1 - roughness`.
6. Ajouter un **VRC Avatar Descriptor**, régler le point de vue entre les yeux et sélectionner **Viseme Blend Shape** pour la parole. Affecter le Skinned Mesh Renderer du visage et associer les quinze formes `viseme_*` aux visèmes correspondants.

Correspondances du squelette si Unity ne les détecte pas automatiquement :

| Unity | Os FBX |
| --- | --- |
| Hips, Spine, Chest, Neck, Head | mêmes noms |
| Left / Right Upper Arm | UpperArm.L / UpperArm.R |
| Left / Right Lower Arm | Forearm.L / Forearm.R |
| Left / Right Hand | Hand.L / Hand.R |
| Left / Right Upper Leg | Thigh.L / Thigh.R |
| Left / Right Lower Leg | Shin.L / Shin.R |
| Left / Right Foot | Foot.L / Foot.R |

`Root` reste un os racine supplémentaire. Le squelette existant n'a pas d'os individuels pour les doigts, les yeux, les épaules ou les orteils. Les expressions de bouche utilisent les blend shapes, sans os de mâchoire. Cet export n'ajoute pas de nouvelles articulations.

## Validation et limites

Réimportation FBX dans Blender réussie pour les deux modèles : 18 os par avatar, géométrie conservée, aucun sommet sans poids, 15 visèmes non vides, quatre animations présentes, textures rechargeables et échelle humaine conservée (environ 1,77 m et 1,76 m). Aperçu visuel vérifié après réimportation. `npx tsc --noEmit` réussi.

Le test automatisé dans Unity 2022.3.22f1 n'a pas pu démarrer : l'éditeur signale « No valid Unity Editor license found ». La reconnaissance Humanoid et la validation par le SDK VRChat restent donc à effectuer ; ces fichiers ne constituent pas un package VRChat prêt à publier.

La simulation capillaire spécifique au navigateur n'est pas exportée. Les surfaces de cheveux suivent la tête ; une dynamique VRChat devra être configurée séparément. Les matériaux demandent un contrôle dans Unity, notamment pour les normales et les reflets. Les modèles conservent leur niveau de détail initial ; ils ne sont pas optimisés pour Quest autonome.

Guide officiel : https://creators.vrchat.com/avatars/creating-your-first-avatar/

## Reproduire l'export

Depuis la racine du projet, lancer Blender en arrière-plan avec `--python-exit-code 1 --python scripts/blender-export-avatar-fbx.py`, puis `scripts/blender-verify-avatar-fbx.py`. `scripts/blender-preview-avatar-fbx.py` produit l'aperçu. Ne pas exécuter ces scripts dans une session Blender contenant du travail non enregistré : ils chargent les sources dans leur propre processus d'arrière-plan.
