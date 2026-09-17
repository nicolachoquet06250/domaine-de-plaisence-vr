# Cour, portraits et paysage

Extension de l'expérience existante, travail autorisé par la demande du 9 septembre 2026. Mode QUICK du guide d'architecture pour l'ajout d'identité/avatar; composition Blender pour les autres lots. Aucun changement du parcours ni des commandes.

Contrats : courtMale/courtFemale glTF skinnés, pieds Y0, face +Z, clips Idle/Walking en place; sélection Homme/Femme avec pseudo persistée et échangée par le protocole existant. AssetManager assure les clones de squelette, AnimationMixer les fondus. L'avatar distant suit les pieds, pas la hauteur absolue de la tête; aperçu à l'accueil [-2,0,-3].

Murs : ouverture intérieure z[2.20,5.40], mur côté arrière prolongé de30cm et avant de10cm; jeu nominal5mm des vantaux, embrasures habillées. Deux bustes historiques indépendants remplacent les silhouettes des chambres sur les socles conservés.

Accueil : GLB au même repère, collision séparée conservée. Pelouse : surfaces modelées et brins opaques par groupes spatiaux, chemins exclus; tiges de fleurs réellement raccordées. Aucun shader d'herbe allouant à chaque image.

Vérifications : typecheck puis tests réseau/identité, clips/skins/clones réels, surfaces/collisions, pelouse/fleurs; rendus natifs de chaque scène et avatars, panneau UIKit isolé, application chargée et build. Les temps navigateur ne prouvent pas les FPS d'un casque physique.

Références visuelles consultées : portrait François Ier, Jean Clouet, Louvre (https://boutique.louvre.fr/en/product/57155-portrait-de-francois-ier-art-prints.html); buste Louis XIV, Bernin1665, Versailles (https://www.chateauversailles.fr/actualites/expositions/genie-majeste-louis-xiv-bernin); Catherine de Médicis, Clouet1555 (https://www.viv-it.org/immagini/f-clouet-ritratto-di-caterina-de-medici-1555). Les portraits sont des interprétations sculptées, sans prétendre à un scan des œuvres. Les costumes se rapportent au XVIe siècle; le portrait de Louis XIV conserve sa perruque et sa draperie du XVIIe.

Livraison, références directes des collections, budgets réels, captures et limites : [artifacts/court/README.md](../artifacts/court/README.md). La sélection des deux avatars a été vérifiée à la gâchette en XR ; les contrôles GLB portent sur les sommets effectivement animés. Les dernières sources Blender adoucissent les volumes des manches et mélangent les poids aux coudes et à la taille. Le rendu des visages reste stylisé.
