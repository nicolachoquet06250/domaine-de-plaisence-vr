# Interactions du Domaine de Plaisance — Unity / VRChat

Scène : `Assets/DomainePlaisance/Scenes/Domaine de Plaisance.unity`.
Scripts : `Assets/DomainePlaisance/Interactions/Scripts/`.

## Utilisation

- Les cinq doubles portes du château s'ouvrent à l'approche d'un joueur et se referment deux secondes après son départ. Une interaction permet également de demander leur ouverture.
- La fontaine fonctionne automatiquement : surface du bassin, jet central et six jets latéraux. Les déformations originales des modèles sont conservées.
- À l'accueil, traverser le portail ovale doré au voile turquoise. Le trajet démarre après l'entrée dans le siège et dépose le joueur devant le domaine. Une interaction sur le portail permet également d'embarquer.
- Devant le domaine, traverser le même portail pour le retour avec demi-tour dans l'avant-cour. Les panneaux et textes d'embarquement ont été retirés ; les quatre maillages de chaque portail proviennent de l'export de l'expérience originale.
- Les portails disparaissent localement pendant le voyage et réapparaissent au débarquement. Ils ne réagissent qu'au joueur local.
- Le passager reste dans le carrosse pendant tout le voyage. Le bouton « Descendre » est supprimé ; la sortie par déplacement/saut et le changement de station sont désactivés. Le débarquement est automatique au terminus, puis le carrosse peut être réutilisé.
- Le cercle d'accueil et l'enceinte du château possèdent des murs invisibles continus, y compris devant les ouvertures des grilles. Les portails de téléportation restent accessibles depuis l'intérieur. Les limites ne bloquent pas les voyages en station ni le débarquement automatique.
- Chaque joueur dispose de son propre carrosse local. Le carrosse peut être appelé depuis l'un ou l'autre terminus, même après un déplacement à pied.

## Synchronisation

`DomaineNetworkDoor` utilise un état Udon manuel synchronisé : position de départ, cible ouverte/fermée et horodatage réseau. Le propriétaire réseau observe la proximité de tous les joueurs. L'interpolation se recalcule à partir du temps réseau, et les nouveaux arrivants reçoivent l'état persistant. VRChat exécute ce code sur les clients ; il ne s'agit pas d'un script personnalisé exécuté sur un serveur dédié.

`DomaineLocalCoach`, ses boutons et la fontaine ne synchronisent aucune variable. Aucun `VRCObjectSync` n'est placé sur le carrosse ou ses modèles. La fontaine suit l'horloge réseau sans envoyer de messages d'animation.

`DomaineCoachPortal` rétablit l'embarquement par passage dans le portail, avec une nouvelle tentative si l'attribution du siège n'était pas encore terminée. Son voile est translucide, double face et non éclairé, comme dans la source WebXR.

VRChat doit néanmoins représenter correctement les avatars assis. Une réserve de 100 stations invisibles attribue une place différente à chaque joueur présent. Seuls l'attribution des places et les positions des stations de passagers sont synchronisés. Ces stations ne partagent ni le modèle du carrosse, ni son trajet, ni son état local. Les départs de joueurs libèrent leurs places.

## Géométrie et collisions

Les portes intérieures ne sont plus fusionnées dans le maillage immobile du château : 4 960 faces de portes ont été retirées de la variante `interieur-sans-portes.fbx`. Les portes mobiles utilisent les matériaux précédemment importés. L'intérieur demeure un objet distinct.

Chaque porte possède les collisions des vantaux et un volume bloquant le passage tant que l'ouverture est insuffisante. La scène conserve les autres collisions existantes. Cette adaptation n'ajoute pas des colliders à tous les petits éléments de décor.

Les limites de déplacement comprennent 96 segments chevauchants autour du cercle (rayon 7,91 m) et quatre murs fermant le périmètre du château, dont le grand portail. Ces 100 `BoxCollider` n'ont aucun rendu et s'étendent de -2 à 28 m de hauteur. Les portails et points de débarquement sont dégagés du côté intérieur.

Les 100 stations ont `disableStationExit=true` et `canUseStationFromStation=false`. Les anciens appels `ExitRide` restent sans effet. Une interruption de station liée au rechargement d'un avatar replace le passager sans redémarrer le parcours. La commande globale de réapparition de VRChat conserve son rôle de récupération à l'accueil.

La hauteur cible de la vue du passager (`seatViewHeight`) est de 2,48 m au-dessus de l'origine du carrosse, soit une hausse de 40 cm par rapport au réglage initial. Le recalage à l'embarquement utilise cette hauteur et adapte la position de la station à la hauteur de tête du joueur.

La scène utilise 15 maillages d'eau animés, 148 déformations et les animations `HorseIdle` / `HorseWalk`. Les roues tournent en fonction de la distance parcourue. Les itinéraires reprennent les 4 098 échantillons du parcours source : environ 120,45 m à l'aller et 139,57 m au retour, à 2 m/s avec accélération et freinage.

## Vérification et maintenance

Les rapports initiaux sont conservés dans `DomaineImportReports/interactions-setup.json` et `interactions-runtime.json`. Ils précèdent le verrouillage demandé des voyages. La vérification actuelle est enregistrée dans `DomaineImportReports/deplacements-verrouilles.json` : continuité des murs, déplacement réel du contrôleur du joueur, portails, refus de descente volontaire, récupération d'une interruption de station et trajets complets avec débarquement automatique.

Un test avec deux véritables clients VRChat reste nécessaire pour confirmer la synchronisation réseau en conditions réelles, les arrivées tardives et le confort en casque. ClientSim ne constitue pas ce test réseau.

Le CLI peut relancer le test actuel avec `-executeMethod ValidateDomaineTravelRules.Run`, après fermeture de l'éditeur utilisant ce projet. `ApplyDomaineTravelRules.Run` installe les limites et applique le verrouillage avant ce test. `SetupDomaineInteractions.Run` réalise une première installation et refuse d'écraser une scène déjà configurée. Ne recréez pas la scène à partir du seul FBX statique : les composants Udon, stations et animations sont configurés dans la scène Unity.

`RestoreDomainePortals.Run` applique les portails originaux après l'installation initiale. Leur premier rapport est `DomaineImportReports/portails-validation.json` ; vues : `portail-accueil.png` et `portail-retour.png`. Les anciens tests de sortie anticipée sont remplacés par `ValidateDomaineTravelRules.Run`.

La scène précédant l'installation est conservée dans `DomaineImportReports/scene-before-interactions.unity.backup`. Les FBX statiques originaux et leurs textures restent disponibles dans `Assets/DomainePlaisance/Models` et `Textures`.
