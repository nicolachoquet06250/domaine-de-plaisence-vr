# Accueil solo et sortie de salon (QUICK)

La racine sans roomId (ou ancien paramètre room) affiche une terrasse solo sans WebSocket ni capture micro. Un bouton explicite crée un salon privé et ouvre le château ; les invitations valides ouvrent directement le château. Les liens room existants restent acceptés, roomId devient le paramètre des nouvelles invitations. Sur tous les chemins sans identifiant, aucune création de salon, connexion, modification d'URL ou transition de map n'est déclenchée au démarrage. Un identifiant invalide affiche l'accueil avec une explication.

La sortie ferme immédiatement transport, reconnexions, avatars et voix, enlève les paramètres de salon et charge la terrasse. Réutiliser World.loadLevel (LevelSystem atomique, dispose des anciennes entités, applique player.transform, conserve la session XR). Aucun World.create reconstruit : iwsdk.config choisit la terrasse initiale et reste la source de vérité.

Une invitation valide sans pseudo enregistré reste sur l'accueil solo. Le salon demandé est gardé en attente sans WebSocket ni modification de l'URL. « Accéder à la room » remplace la création dans les panneaux et le menu jusqu'à la connexion explicite avec un pseudo non vide. La saisie seule ne connecte pas. Un échec de chargement conserve l'invitation pour réessayer ; une déconnexion l'efface. Avec un pseudo enregistré, l'invitation entre directement comme auparavant.

Assets déterministes : terrasse circulaire en pierre avec parapet, portique et plantations existantes ; collision fusionnée via StaticCollision existant. Une scène plate dédiée avec point de départ libre. UIKitML pour le panneau d'accueil et les commandes du menu M/B ; panneau DOM Amis fournit la même entrée sur mobile. Les abonnements activeLevel relient les boutons après chaque changement de scène.

Vérification : URL sans identifiant inchangée et aucun socket, liens room/roomId, création explicite, quitter ferme voix/socket et supprime avatars sans reconnexion, aller-retour de niveaux en VR, collision terrasse, previews scène/UI, TypeScript, tests ciblés et build.

## Observations

Scène validée et rendue dans l'éditeur (hero), diagnostics vides ; runtimeHash `sha256:b4305b4b7f7c522325911fd0cd50ca366a2222026e2edc58a5b2bc081c630a2a`. Previews isolées des deux panneaux lisibles. Trois objets de collision initialisés avec LocomotionEnvironment sur la plateforme et les deux arbres.

Essai runtime Meta Quest 3 émulé : accueil avec RoomConnection.status=solo, roomId vide, 0 visiteur, micro off. Clic au rayon sur arrival-connect : château chargé, salon connecté. Bouton B puis clic sur comfort-session : terrasse de nouveau visible, status=solo, roomId vide, écoute false, micro off, aucun RemoteVisitor, session XR toujours active et même génération de page. Tests de cycle de vie vérifient aussi l'absence de socket au démarrage, les invitations anciennes/nouvelles et l'absence de reconnexion après sortie.

Validation finale : `npx tsc --noEmit` réussi ; `node --test tests/*.test.mjs` : 46 tests réussis, aucun échec (accueil, menu, mobile, collisions, signalisation, voix).
