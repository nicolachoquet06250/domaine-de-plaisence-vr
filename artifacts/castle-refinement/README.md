# Corrections du château

Modèles créés et corrigés dans Blender 5.2 via le MCP local, puis exportés aux mêmes URL du manifeste pour remplacer les modèles dans la scène existante. Source éditable : `../castle/chateau-plaisance.blend`.

- Dallage du vestibule jointif, raccord des galeries et perron découpé suivant les ailes : aucun recouvrement des 432 triangles des finitions de sol vérifiés dans les GLB.
- Palier intermédiaire et galerie arrière prolongés jusqu'à la face intérieure du mur, à z = −5,78 m dans le repère du château.
- Marches de 24 cm d'épaisseur avec dessous en gradins. Six colonnes cannelées, bases moulurées, bagues dorées et chapiteaux à volutes. Collisions des rampes affinées pour dégager l'espace inférieur.
- Balustrades de façade enrichies de profils, anneaux, panneaux décoratifs et couronnements. Extrémités à x = ±13,68 m, avant le retour du mur à ±13,78 m.
- Deux chambres et deux salles de bains : lits, quatre chevets, lampes, commodes, miroirs, armoires, baignoires creuses sur pieds sculptés, toilettes avec cuvette ouverte, vasques, robinetterie et linge. Bureaux, tabourets et quatre bustes sur socles complètent les pièces.

Optimisation : géométries regroupées par matériau, textures intégrées, réduction ciblée des petits ornements métalliques, collisions séparées. Façade 81 794 triangles / 10 appels de dessin ; intérieur 96 142 / 23 ; vitrage 5 280 / 1 ; paire de portes 1 240 / 6, réutilisée cinq fois. Les quatre fichiers totalisent 8 950 368 octets. Ce budget est un contrôle de ressources, pas une mesure de FPS sur casque.

Tests : TypeScript, build Vite, `scripts/verify-castle.mjs` et `scripts/verify-castle-floors.mjs`. Le test de locomotion utilise la capsule réelle IWSDK et monte les deux volées jusqu'à la pièce de l'étage ; il vérifie aussi le raccord arrière et les passages entre colonnes. Les deux clips de charnières à 105° restent présents. Le système d'interaction des portes n'a pas été modifié. Les données du jardin et de la fontaine sont conservées.

Les PNG de ce dossier sont des captures natives de l'éditeur, sauf `runtime-bedroom.png`, capturé dans l'application. Les vues de chambre, salle de bains, sanitaires, palier, escalier et balustrade sont enregistrées dans les caméras d'auteur de la scène. Le contrôle des sols est une analyse géométrique des surfaces, complétée par les vues, et ne représente pas une mesure temporelle de chaque pixel.

La régénération complète est documentée dans `../castle/README.md`. Les scripts ponctuels de correction ne doivent pas être rejoués après la génération complète : leurs ajustements ont déjà été reportés dans `blender-castle-furnishings.py`.
