# Domaine de Plaisance dans Unity / VRChat

Scène : `Assets/DomainePlaisance/Scenes/Domaine de Plaisance.unity`.

Le dossier `Assets/DomainePlaisance` contient le FBX complet dans `Models`, les PNG dans `Textures`, les matériaux éditables dans `Materials`, les shaders PBR dans `Shaders` et le prefab de domaine dans `Prefabs`. `Interieur_Chateau` reste un objet distinct à l'intérieur du modèle complet.

Les matériaux utilisent les couleurs, rugosités, valeurs de métal, normales, alpha et émission de la composition Blender. Les feuilles de chêne utilisent une découpe alpha ; les surfaces d'eau, de verre et de flammes utilisent la transparence. Les faces doubles sont configurées selon les matériaux source.

La scène dédiée contient un VRC Scene Descriptor, un point d'arrivée sur la terrasse, l'éclairage et des colliders statiques sur les sols et les principales surfaces architecturales. Les animations et interactions de l'application WebXR ne sont pas transférées par le FBX.

`DomaineImportReports` à la racine du projet contient le rapport d'import et trois rendus Unity : vue d'ensemble, château et intérieur. Le script de préparation est `Assets/DomainePlaisance/Editor/ImportDomainePlaisance.cs` ; son point d'entrée CLI est `ImportDomainePlaisance.Run`.

Relancer ce script reconstruit la scène dédiée et ses matériaux : conserver les modifications manuelles dans une copie avant de le réexécuter.
