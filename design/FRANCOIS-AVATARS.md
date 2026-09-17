# Avatars actifs — coupe François Ier et contours d’oreille

Retouche masculine du 13 septembre : moustache abaissée vers la lèvre supérieure,
extrémités raccordées à la barbe dans le même maillage et dans les quinze visèmes.
Asset masculin actif : `moustache-20260913-r1`. Source et vues rapprochées :
`artifacts/avatars/moustache/renaissance-moustache.blend`, `face.png`,
`trois-quarts.png`. La version antérieure et l’avatar féminin sont conservés.

La révision `francois-20260912-r2` remplace les deux GLB actifs. La version précédente
est conservée dans `artifacts/avatars/francois/before/`.

## Modifications

- Coupe masculine courte et dense, inspirée du [portrait de François Ier conservé au Louvre](https://collections.louvre.fr/ark%3A/53355/cl010062204).
- Implantation continue : tempe, patte, arc au-dessus de l’hélix, retour derrière
  le lobe et nuque. Les grandes découpes latérales ont été remplacées par une
  courbe ajustée à l’oreille. Références consultées :
  [profil féminin avec chignon](https://www.twistonline.com/products/diamond-wave-huggie-hoops)
  et [profil masculin](https://i.pinimg.com/originals/5a/4e/96/5a4e964f92eefe5aefef098fa9213436.jpg).
- Barbe intégrée à la topologie du visage, avec une épaisseur progressive sur les
  joues et le menton, une bordure adoucie et une matière mate. La barbe partage les
  quinze visèmes du visage ; sa base ne constitue plus un masque séparé.
- Têtes abaissées de 50 mm en coordonnées d’auteur (47,5 mm pour le modèle féminin
  à l’échelle 0,95), transition continue dans le cou et articulations adaptées.
- Fibres fines, textures de couleur et normales incorporées aux GLB. Chignon haut,
  couleurs des yeux, colliers ajustés et souliers de la révision précédente conservés.

## Cheveux et physique

Le fichier Blender contient trois systèmes de particules éditables avec dynamique
capillaire : 460 parents pour chaque coiffure et 600 pour la barbe, avec 24 enfants
interpolés au rendu. Les racines ont été recalées après la modification du cou.
Écart maximal mesuré à la surface d’émission : 0,277 mm.

Dans l’application, les fibres mobiles utilisent le solveur de particules existant,
avec gravité de 9,81 m/s², inertie et racines attachées à la tête. La masse de la coupe
et le chignon maintiennent la coiffure ; les fibres masculines et les petites mèches
de nuque féminines se déforment. Le volume de collision intérieur a été ajusté aux
guides pour éviter de repousser artificiellement les cheveux au repos.

Contrôle dans le navigateur : erreur d’ancrage nulle, allongement maximal au repos
de 0,421 mm pour l’homme et 0,402 mm pour la femme. Après un changement instantané
de rotation de 0,65 rad et trois images à 72 Hz, allongement transitoire de 9,11 mm
et 0,857 mm respectivement. Ce changement brutal est un contrôle de contrainte ;
les rotations progressives font aussi l’objet d’un test automatisé.

## Livrables et vérification

| Avatar | Triangles | Octets |
| --- | ---: | ---: |
| courtMale | 93 339 | 11 053 564 |
| courtFemale | 97 439 | 10 037 580 |

Source éditable : `artifacts/avatars/francois/renaissance-francois.blend`.
Vues : `portraits.png`, `profiles.png` (90°), `trois-quarts.png`, `duo.png`,
`visemes.png` dans le même dossier. Les références photographiques sont uniquement
des guides de modélisation ; elles ne sont pas utilisées comme textures des avatars.

Contrôles : TypeScript, construction Vite, 38 tests, vérification des GLB incorporés,
poids squelettiques, quatre animations bouclées, quinze visèmes par avatar et
indépendance des clones. Les tests incluent désormais la stabilité du visème de
silence et le comportement des véritables guides exportés sous gravité.
Vérification visuelle dans Blender et dans le navigateur IWSDK ; aucune mesure de
performance sur casque physique n’est déduite de ces contrôles.

Rapports : `validation.json`, `native-particles.json`,
`colliders.json`, `runtime-hair.json`, `tests.log`, `build-app.log`.

## Reconstruction par le MCP Blender

Exécuter dans cet ordre les scripts `blender-francois-avatars.py`,
`blender-francois-finish.py`, `blender-francois-export.py`,
`blender-francois-face-recover.py`, `blender-francois-native.py`,
`blender-francois-colliders.py`, `blender-francois-render.py`,
`blender-francois-visemes.py`, puis `blender-francois-save.py` avec
`scripts/blender-mcp.mjs execute_blender_code` et le `request.json` du dossier.

Le réassemblage facial copie explicitement chaque coordonnée de chaque visème
depuis la sauvegarde anatomique ; il conserve 600 fibres de barbe. Il évite les
ambiguïtés de remappage des shape keys lors d’une suppression BMesh. Les guides
natifs sont réattachés avec les objets et modificateurs évalués, conformément à
l’[API ParticleHairKey de Blender](https://docs.blender.org/api/4.3/bpy.types.ParticleHairKey.html).
Les scripts intermédiaires `finalize`, `optimize`, `basis` ne font pas partie de
cette procédure finale.
