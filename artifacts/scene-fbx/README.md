# Domaine de Plaisance — scène composée et intérieur séparé

Cette livraison reprend la composition complète de `public/scenes/visit.iwsdk.scene.json` et les versions actuelles des modèles : accueil, terrasse, carrosse, forêt, paysage, chemin, enceinte et portail, jardins, fontaine, château et ses aménagements intérieurs.

## Livrables

- `scene-complete.fbx` : scène complète, 154 objets maillés, 1 443 151 triangles.
- `interieur-chateau.fbx` : l'intérieur, réuni dans **un seul objet maillé `Interieur_Chateau`**, avec ses matériaux et ses lumières ; 500 536 triangles.
- `scene-composee.blend` : composition Blender éditable, organisée en `Scene_Complete`, `Exterieur_Domaine` et `Interieur_Chateau`.
- `Textures/` : textures PNG externes. Les FBX incorporent aussi leurs textures.
- Les trois PNG d'aperçu sont des rendus des fichiers FBX réimportés dans Blender.
- `verification-blender.json`, `verification-unity.json` et les rapports de composition/export détaillent les contrôles et la provenance.

## Séparation de l'intérieur

`Interieur_Chateau` rassemble les planchers, plafonds, cloisons, escaliers et balustrades, aménagements et mobilier, portes des salons et galeries, quatre bustes, surfaces de miroirs et cheminées avec bûches et flammes statiques. Les neuf lumières intérieures restent des enfants de cet objet.

Les façades, murs périphériques de la structure extérieure, toitures, vitrages extérieurs et porte d'entrée restent dans l'extérieur. Le FBX intérieur présente donc les aménagements isolés, sans l'enveloppe extérieure du bâtiment.

Les deux exports conservent les coordonnées de la composition, en mètres. Importés avec la même transformation, ils s'alignent. **La scène complète contient déjà l'intérieur** : pour utiliser le FBX intérieur séparé à sa place, désactiver ou supprimer le `Interieur_Chateau` inclus dans la scène complète afin d'éviter les surfaces superposées.

## Import Unity

Copier les FBX et le dossier `Textures` dans le projet. Le modèle de scène s'importe comme géométrie statique ; aucun rig Humanoid n'est nécessaire. Conserver l'échelle d'import par défaut et vérifier la conversion des unités. Pour ce gros maillage intérieur, conserver le format d'indices automatique ou 32 bits, sans forcer 16 bits.

Extraire les matériaux/textures incorporés si nécessaire. Les fichiers dont le nom contient `normal` ou `Normal` sont des cartes de normales. Vérifier les modes transparent/cutout des matériaux de feuilles, vitrages, eau et flammes ainsi que les réglages de reflets. La lumière ambiante et le ciel de Blender/IWSDK sont à configurer dans Unity.

Les couleurs de sommets de 27 géométries partagées ont été converties en textures UV ; les normales ont été recalculées dans ces UV lorsque nécessaire. Les modèles source du projet et la composition IWSDK n'ont pas été modifiés.

## Portée du FBX

Il s'agit d'une scène modélisée **statique**, évaluée à l'image zéro. Le déplacement du carrosse, l'ouverture automatique des portes, les animations d'eau, la simulation des cheveux, les interactions et les scripts WebXR ne sont pas transférés. Les flammes procédurales utilisent une approximation en texture fixe ; les miroirs nécessitent une réflexion configurée dans Unity. Les interfaces UIKitML et les volumes de collision invisibles sont recensés dans le rapport mais ne deviennent pas des objets visibles du FBX. Les avatars des visiteurs sont créés par l'application et ne font pas partie de la composition statique.

## Contrôles

Réimportation des deux FBX dans Blender : tous les objets maillés, nombres de sommets et triangles conservés ; textures incorporées rechargeables ; intérieur constitué d'un maillage distinct. Écart maximal des limites spatiales : moins de 0,03 mm. Aperçus de l'ensemble, du château et de l'intérieur inspectés. TypeScript du projet : `npx tsc --noEmit` réussi.

**Vérification Unity 2022.3.22f1 réussie**, après activation de la licence : les deux fichiers sont importables, tous les sommets contrôlés sont finis, la scène comporte 154 objets maillés et le FBX intérieur un seul. L'intérieur est séparé et ses limites spatiales s'alignent dans les deux imports, avec un écart inférieur à 0,03 mm. Unity nomme automatiquement la racine du FBX isolé `interieur-chateau` ; dans la scène complète, l'objet reste `Interieur_Chateau`.

Unity rapporte 1 434 267 triangles pour la scène et 495 002 pour l'intérieur après son import, contre 1 443 151 et 500 536 dans Blender. Les rapports conservent ces deux comptages distincts. Le contrôle Unity porte sur l'import, la géométrie et les transformations ; les aperçus visuels livrés proviennent de Blender, et ne constituent pas un rendu Unity ni une validation VRChat.

Le document source a été ouvert et validé par l'éditeur IWSDK sans modification. La capture native a rencontré une perte de disponibilité du navigateur ; les aperçus livrés sont explicitement des contrôles FBX dans Blender.

## Reproduction

Depuis la racine du projet :

1. `node scripts/prepare-composed-scene-fbx.mjs`
2. Blender en arrière-plan avec `--python-exit-code 1 --python scripts/blender-compose-scene-fbx.py`
3. Blender en arrière-plan avec `--python-exit-code 1 --python scripts/blender-export-composed-scene-fbx.py`
4. Blender en arrière-plan avec `--python-exit-code 1 --python scripts/blender-verify-scene-fbx.py`
5. Blender en arrière-plan avec `--python-exit-code 1 --python scripts/blender-preview-scene-fbx.py`

Le projet de contrôle Unity se trouve dans `artifacts/scene-fbx-unity-validation`. Son point d'entrée en mode batch est `ValidateSceneFbx.Run`. Ces scripts utilisent des processus Blender dédiés ; ne pas les exécuter dans une session contenant du travail non enregistré.
