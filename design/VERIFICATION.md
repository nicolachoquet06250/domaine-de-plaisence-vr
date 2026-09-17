# Domaine de Plaisance — Vérification du 6 septembre 2026

## Rambardes de la terrasse

Les deux rambardes reposent désormais sur la quatrième et dernière marche. Base à y=0,66 m, identique à la surface supérieure ; centre en z=6,81 m au lieu de 8,35 m, avec la main courante entièrement derrière le nez de marche z=7,05 m. Les positions sont dérivées des dimensions des marches. Vue native rapprochée oblique vérifiée : absence de vide sous le socle. TypeScript et compilation réussis.

## Restriction des commandes virtuelles aux mobiles

Détection téléphone/tablette, avec exclusion prioritaire des navigateurs de casque (dont Quest/Oculus/Pico/Wolvic) et des ordinateurs Windows/ChromeOS. Les ordinateurs tactiles ne sont plus assimilés à des mobiles. iPadOS en mode ordinateur reste pris en charge. Le paramètre touch=1 a été supprimé. Les contrôles ne sont même pas créés sur les appareils exclus, ni leur adaptateur de déplacement installé. TypeScript et huit tests ciblés passent, dont les profils iPhone/iPad/Android, Mac, Windows tactile et Quest/Pico hors session immersive.

## Commandes mobiles

- Joystick radial gauche et zone de regard droite, pointeurs indépendants, capture/release/cancel/blur/visibilitychange/resize. Toolbar Domaine/Confort/Amis, panneaux mutuellement exclusifs, coordonnées de menus adaptées aux petits écrans et aux encoches. Commandes masquées en XR, retour automatique à la sortie.
- `npx tsc --noEmit` et `npm run build` réussis, 2211 modules. Dix tests passent : quatre confort, trois calcul/assemblage d'axes et trois tests des gestionnaires réels de MobileControlsSystem avec DOM/SDK simulés. Couvrent deux doigts, zone morte, diagonales, menus, annulation, perte de focus, rotation de fenêtre, transitions XR et nettoyage.
- Capture runtime en environnement coarse : joystick et zone de regard visibles, panorama dégagé, HUD du domaine replié. Une seconde capture en session XR montre la disparition de l'interface tactile ; MobileControlsSystem, SlideSystem et MultiplayerSystem initialisés sans erreur dans les logs consultés.
- Limites : aucun essai sur téléphone physique ni mesure de fluidité mobile. Le connecteur de contrôle navigateur ne démarre pas (champ sandboxPolicy manquant), empêchant les gestes tactiles automatisés et les captures à dimensions portrait/paysage exactes. Le pont IWSDK s'est ensuite déconnecté pendant le contrôle complémentaire du déplacement VR ; ce dernier n'a pas pu être achevé. La toolbar a été abaissée après la première capture pour libérer les contrôles de l'émulateur.


## Accès explicite à la VR

Ajout du bouton Entrer en VR au panneau d'accueil, relié directement à World.launchXR() dans le gestionnaire de clic. Il ne dépend pas de l'interface optionnelle offerSession du navigateur. Détection immersive-vr, message pour navigateur sans casque/HTTPS, nettoyage et reconnexion des gestionnaires au changement de niveau. Panneau agrandi et vérifié dans le rendu UIKitML et la capture runtime : bouton lisible, statut « Casque compatible » en émulation. TypeScript et build validés (2208 modules). Le connecteur de clic navigateur reste indisponible ; le clic d'entrée lui-même n'a pas été exécuté par automatisation.

## Correctif château et menu de confort

- Fenêtres : encadrements extrudés avec une ouverture réelle, vitrage en retrait et profondeur distincte de la façade ; même correction pour l'encadrement de la porte. Plan proche de la caméra passé de 0,001 m à 0,05 m pour améliorer la précision du tampon de profondeur. Vues natives rapprochées de face et de biais contrôlées sans surfaces de vitrage concurrentes visibles.
- Menu UIKitML enregistré dans le manifeste, masqué à l'arrivée. M au clavier / B à droite en VR ; fermeture par la même touche, Échap ou le bouton Fermer. Cinq niveaux de 0 à 100 %, appliqués au signal public LocomotionSystem.comfortAssist, sauvegardés localement.
- VR émulée Quest 3 : B ouvre et ferme ; clics par rayon sur 0 %, 100 % et 50 % vérifiés dans ComfortSettings.strength et appliedStrength. Le bouton Fermer fait également passer open à false. Après rechargement, 100 % était conservé et le menu fermé. Valeur initiale de 50 % rétablie après essais. Les essais par commandes séparées dépassant le délai de clic XR ont été remplacés par un appui bref de 150 ms pour le contrôle final.
- Cycle navigateur/VR : à la fermeture, le document UIKit est retiré de la caméra et réattaché à son panneau, avec réinitialisation des dimensions. Le menu fermé n'intercepte plus les interactions. Les classes CSS du menu sont préfixées pour éviter les collisions avec le panneau d'accueil.
- `node --test tests/comfort-menu.test.mjs` : 4/4. Gestionnaires clavier réels testés avec dépendances simulées : ouverture/fermeture, cinq niveaux, saisie de texte et répétition ignorées, restauration du document et stockage invalide ou indisponible.
- `npx tsc --noEmit` et `npm run build` réussis (2207 modules). Prévisualisation native du menu et capture XR conservées dans `design/verify/comfort-menu.png` et `comfort-menu-xr.png`. Éditeur : valid:true, dirty:false, conflict:false, diagnostics:[], runtime.ready:true.
- Limite : le pilotage automatique du navigateur au clavier est indisponible (`sandboxPolicy` absent dans le connecteur). Les raccourcis sont couverts par les tests du système, mais l'ouverture par une frappe physique sur M et les clics souris n'ont pas été vérifiés en direct. Aucun essai sur casque physique.

## Vérification de la création initiale

| Critère | Résultat | Preuve |
| --- | --- | --- |
| Château classique et quatre jardins devant | PASS | Rendus natifs hero.png, top.png, quarter.png, spawn.png ; modules palace/gardens/fountain valid:true, diagnostics vides |
| Fontaine centrale, six jets latéraux et un central | PASS | ECS WaterJet : 7 entités, jet-central kind1 et jet-lateral-1…6 kind0 ; eau visible après correction de la racine de prototype |
| Animation réelle | PASS | ECS jet-central elapsed2460.6135 puis2483.7175 ; même horloge serveur appliquée aux uniforms des tubes, gouttes et eau ; captures runtime |
| Arrivée et déplacement | PASS | Player [0,~0.009,24] ; joystick gauche en VR 1s déplace z24 vers22.3722, sans chute ; vue XR dégagée |
| Deux visiteurs | PASS | Client WebSocket de contrôle reçoit la pose réelle du navigateur [0,1.655,24] ; le navigateur affiche l'avatar à[2,1.65,17] avec deux mains ; RoomConnection visitorCount2 |
| Départ du visiteur | PASS | Fin du client de contrôle : RemoteVisitor total0 et visitorCount1 |
| Salons et validation réseau | PASS | npm run test:rooms :6/6, échanges tête/mains, isolation, départ/reconnexion, paquets invalides, capacité, horloge, limite taille et heartbeat |
| VR | PASS émulation | xr_get_session_status immersive-vr, visible, MetaQuest3 ; capture xr-multiplayer.png |
| Panneau | PASS | ui render-preview valide, panel.png lisible ; copie française compatible avec la police embarquée, sans ressource distante |
| TypeScript et compilation | PASS | npx tsc --noEmit ; npm run build réussi,2205 modules, dist généré |
| Éditeur final | PASS | public/scenes/plaisance.iwsdk.scene.json, dirty:false, conflict:false, diagnostics:[], runtime.ready:true, stale:false |

Rendus sauvegardés dans design/verify/. Les images de l'éditeur valident la composition ; le test d'animation et des avatars a été effectué dans le runtime.

Hash runtime final : sha256:6c3f2f750a97a2936af35f5f07ee460c9731611ee270cbf51edae5c912738ee9.
Matérialisation initiale : composition et sortie aplatie avaient le même hash sha256:cdad381877278d6e3c6f0d7d4657421076a55b64dc880cacdbcf294a749a03cd. Les ajustements ultérieurs concernent uniquement la scène aplatie.

## Corrections de revue
- Toits mansardés : rotation de géométrie avant mise à l'échelle rectangulaire.
- Eau : racine Group pour préserver rotation/hauteur du disque lors de l'instanciation.
- Configuration : suppression de slidingSpeed, propriété système non acceptée par le manifeste projet.
- Collision du château : volumes dédiés ; Locomotor ne développe pas les InstancedMesh et refuse le mélange de géométries indexées et non indexées. Bassin et murets portent leurs collisions statiques.
- Caméra navigateur : pose locale à hauteur humaine face au château, indépendante de la vue de revue élevée.
- Matériaux des jets partagés intentionnellement ; même temps pour les six jets, aucun déphasage écrasé.

## Limites de validation et livraison
- Hébergement Internet non provisionné. Serveur Node et procédure HTTPS/WSS fournis dans README-multiplayer.md ; les liens localhost ne fonctionnent que sur le même ordinateur.
- Pas de mesure sur casque physique. Les compteurs de rendu de bureau ne prouvent pas72–90fps sur Quest. Rendu hero environ289 appels et257k triangles avant passes d'ombre.
- Build : avertissements de taille du bundle IWSDK et annotations Rollup de dépendances, sans erreur de compilation.
- Les anciens avertissements de glyphes vus dans l'historique ont été corrigés et le panneau rerendu. Aucun blocage runtime restant observé après correction des collisions.
- Visite extérieure, avatars simples,12 visiteurs par salon, sans voix ni comptes conformément aux hypothèses de GAME_SPEC.md.

## Collisions sur tous les volumes solides — 6 septembre 2026

- Les 49 placements solides utilisent des prototypes de collision dérivés de leur géométrie réelle : château (marches, rambardes, toits et détails compris), sol, allées, parterres, cyprès, bancs, vases, murets et bassin. Eau, jets et panneaux d'interface restent traversables.
- `static-collision.ts` développe chaque InstancedMesh avec ses matrices et produit une géométrie indexée avec l'attribut position uniquement. Le matériau invisible évite une seconde passe de rendu. Les prototypes sont partagés, les transformations des placements sont héritées.
- `StaticCollisionSystem`, priorité 5 après TransformSystem, active LocomotionEnvironment lorsque la hiérarchie est attachée et ses matrices à jour. Cette attente corrige les obstacles fantômes que produisait l'enregistrement immédiat à l'origine locale des groupes.
- TypeScript : PASS (`npx tsc --noEmit`). Tests : 12/12 (`node --test tests/static-collision.test.mjs`) avec les vraies géométries et le Locomotor installé en mode inline. Couverture des indices, instances, matrices, surfaces, rambardes, escalier/entrée fermée et placements de scène. Les volumes bas peuvent être escaladés ; une collision n'est pas une barrière de hauteur infinie.
- Runtime géré en mode worker : 49/49 entités StaticCollision + LocomotionEnvironment, toutes `_initialized: true`, handle non nul. Session immersive-vr IWER Quest 3 : déplacement depuis [0,0,24], allée libre, montée des marches puis arrêt devant la porte à environ [0.2934,0.51,-20.2025]. Fin de session et axes remis à zéro.
- Éditeur : scène valide, aucun diagnostic, dirty=false, conflict=false, runtime ready et non stale. Capture native de la vue spawn et captures runtime normales/VR contrôlées. Les délais de connexion rencontrés pendant le rechargement sont résolus ; aucun échec d'enregistrement de collision observé.
- Hash source : sha256:49b2394fd60caf47f8e3c58cb5e46df4b45748f6ad9d3cf9c2dd92b2dec2fdb4. Hash runtime : sha256:56061618ad3fcab1cecef42d476fe779c57061704df511d19db00ccb4ce1bb97.
- Aucun essai de performance sur casque physique. Les tests inline et la session VR émulée ne remplacent pas une mesure sur appareil.

## Bancs au bord de l'allée — 6 septembre 2026

Les quatre bancs de la scène finale sont déplacés de x=±6,2 / z=±4,5 vers x=±3,05 / z=±8, à y=0,048 (surface du sable). Ils restent orientés vers l'allée centrale ; leur emprise transversale atteint x=±3,395, à l'intérieur du chemin de largeur 7 m. Les parterres commencent à |x|=5 : les bancs sont dégagés des buissons. Identifiants préservés et enfants de collision héritant des transformations.

Vérifications : TypeScript sans erreur ; vue native en plongée montrant les quatre bancs sans chevauchement ; capture runtime ; quatre collisions initialisées et positions monde confirmées à [±3,05,0,048,±8]. Scène valide, dirty=false, conflict=false, runtime prêt. Hash runtime : sha256:e2a11fbf4190a4301c328694cf5d6b3d2de54ff69c83bcfe3eb26ec507283bcd.
