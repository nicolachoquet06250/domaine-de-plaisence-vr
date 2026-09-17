# Pseudos (QUICK)

Champ Input UIKit natif juste avant arrival-connect, doublé d'un input HTML dans le panneau Amis mobile/desktop. UIKit.Input.element et onValueChange confirmés dans les déclarations installées ; aucun composant d'entrée personnalisé. Pseudo mémorisé dans localStorage, normalisé et limité à 24 caractères par une fonction partagée client/serveur. Les invités directs réutilisent leur pseudo choisi ou restent à l'accueil solo pour en saisir un. Aucune connexion supplémentaire en solo.

La clé plaisance.nickname.v2 ne stocke que les saisies personnelles. Les anciens pseudos de v1 sont repris, sauf le format automatique Visiteur-xxxx qui nécessite de choisir un pseudo. Une saisie explicite de ce format dans v2 reste acceptée. Le nom de secours d'une création anonyme est limité à la session, jamais enregistré comme un choix.

Le WebSocket transporte le pseudo à la connexion ; le serveur normalise et le fournit dans welcome, join et les snapshots. L'identifiant réseau reste distinct du pseudo, les homonymes sont autorisés. RemoteVisitor.nickname permet l'inspection ECS. Sprite CanvasTexture rattaché à l'avatar, à 0,4 m au-dessus de la tête interpolée, orientation automatique vers chaque caméra (y compris stéréo), texte Unicode sans interprétation HTML. Texture produite à l'arrivée seulement et libérée au départ. Les contrôles de format/bidi invisibles sont supprimés.

Vérification : entrée/persistance/sortie, deux clients WebSocket et arrivées tardives, caractères longs/accents, tag au-dessus de l'avatar en runtime, preview UIKit, TypeScript, tests et build.

Police DM Sans libre embarquée localement avec licence OFL pour la saisie accentuée (les polices bitmap par défaut ne contiennent pas ces glyphes). Les tags utilisent le moteur de texte Canvas du navigateur.

Vérifié : preview réelle du panneau avec Input avant le bouton ; runtime avec deux clients WebSocket synthétiques, tags « Élodie du Jardin » et pseudo long tronqué à 24 caractères au-dessus des bonnes têtes. RemoteVisitor expose le même pseudo reçu. 29 tests ciblés réussis (accueil, pseudo, salon, menu et voix), TypeScript sans erreur. Le harnais réseau manuel tests/nickname-peer.mjs ferme ses deux connexions après 2 minutes.
