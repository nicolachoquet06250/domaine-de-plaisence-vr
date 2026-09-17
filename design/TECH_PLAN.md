# Technical grounding
Evidence: installed @iwsdk/core 0.5.3 dist declarations; bundled api-reference.md; reference search warmup unavailable, documented installed-source fallback used. ws official README https://github.com/websockets/ws and installed ws 8.21.3.
| Mechanic | Class | Implementation |
| Palace/gardens | CUSTOM assets | deterministic Object3D prototypes, shared/instanced geometry, defineAssets manifest, native scene composition |
| Environment | BUILT-IN | level-root DomeGradient and IBLGradient, DirectionalLight |
| Navigation | CONFIGURE | locomotion browserControls true/useWorker, solid LocomotionEnvironment ground, player spawn [0,0,24] |
| Fountain | CUSTOM | WaterJet(kind/phase) query, shader time uniform, 6 lateral + 1 central; pooled drops, no per-frame allocations |
| Friends rooms | CUSTOM | ws room service on /rooms, cryptographic room codes in URL; welcome/snapshot packets server clock, poses 10Hz, 12 visitor limit, validation, reconnect; remote avatar query |
| Visit controls | CUSTOM browser look + BUILT-IN movement | mouse drag to orient camera; browser and XR locomotion |
| Info UI | CONFIGURE/CUSTOM | manifest-backed UIKitML panel, browser invite link control if clipboard interaction requires DOM |
Risks: hosted HTTPS/WSS endpoint required for off-network friends; ship same-origin standalone static+room server and deployment instructions. Quest frame time requires real headset measurement.
# Commandes tactiles — complément

La locomotion, les collisions et la publication des poses restent celles d'IWSDK et du salon existant. L'extension tactile décore `getMoveAxis` du `ActionLocomotionInputProvider` partagé, obtenu via le champ public `TurnSystem.config.inputProvider`, et restaure la méthode à la destruction. Aucun déplacement direct du joueur et aucun faux événement clavier. Zone morte radiale, normalisation des diagonales et identifiants indépendants des deux pointeurs dans `TouchInputState`. Le système de priorité 4 gère une interface DOM tactile avec capture des pointeurs ; le menu de confort reste l'asset UIKitML partagé. Activation uniquement sur téléphone/tablette tactile ; exclusion des navigateurs de casque et des ordinateurs tactiles. Aucun forçage par URL. Désactivation en XR. Les menus et interruptions remettent les axes à zéro. Densité de rendu plafonnée à 1,5 en visite tactile.

# Collisions statiques complètes

Les assets solides possèdent un enfant `*Collision`, avec le composant déclaratif `StaticCollision`. `StaticCollisionSystem` active leur `LocomotionEnvironment` après le rattachement des parents par TransformSystem et calcule les matrices monde avant l'enregistrement. Ne pas remettre directement LocomotionEnvironment dans le JSON de ces enfants : l'enregistrement précoce peut capturer la position locale avant l'attachement des ancêtres.

`createStaticCollision` développe les instances et mélange correctement les géométries indexées/non indexées en une géométrie indexée commune. Chaque triangle solide reste présent, y compris les détails du château et des jardins. La géométrie est construite au chargement du manifeste, jamais par frame ; les placements partagent les buffers. Les matériaux de collision sont invisibles. Le moteur locomoteur commun assure ces collisions pour clavier, contrôles tactiles et VR, sans activer Havok ni modifier le protocole multijoueur.

Pour ajouter un décor solide, enregistrer son prototype de collision dans `src/assets.ts` puis placer l'enfant portant StaticCollision sous le décor dans la scène finale. Le test d'audit échoue si un nouvel asset solide est laissé sans collision.
