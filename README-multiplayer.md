# Visites entre amis

À la racine du domaine sans identifiant de salon, la visite commence sur une
**plateforme solo**, sans connexion multijoueur ni capture micro. Le bouton
**Créer un salon et entrer** ouvre le château et crée un salon aléatoire de 128 bits
dans l’adresse `?roomId=…`. Les liens `?roomId=…` et les anciens liens `?room=…`
ouvrent directement le salon correspondant si un pseudo est déjà enregistré.
Sinon, l'accueil solo permet de choisir son pseudo : le bouton devient
**Accéder à la room** et rejoint le salon de l'invitation après le clic.
Un pseudo vide ne permet pas de rejoindre cette invitation. Un identifiant invalide reste en solo.
Les anciens noms automatiques `Visiteur-xxxx` ne comptent pas comme un pseudo choisi :
ils déclenchent également cette étape. Seule une saisie personnelle est mémorisée
par la nouvelle version ; les anciens pseudos personnalisés sont conservés.

Sur toute URL de map sans identifiant de salon, aucun salon n'est créé et aucune
redirection ni connexion multijoueur n'est déclenchée. L'adresse et la map chargée
restent en place jusqu'à une action explicite sur **Créer un salon et entrer**.

Dans le menu **M** au clavier / **B** sur la manette droite, **Se déconnecter**
ferme le salon, les voix et le micro puis ramène sur la plateforme solo à la racine.
La session VR reste active. Le même bouton est disponible dans le panneau Amis,
y compris sur mobile. Il n'y a aucune reconnexion automatique après cette sortie
volontaire ; un nouveau salon peut ensuite être créé depuis l'accueil.

Le champ **Votre pseudo**, juste au-dessus de **Créer un salon et entrer**, accepte
jusqu'à 24 caractères et conserve le choix sur cet appareil. Il existe dans le
panneau 3D et dans le panneau Amis. Chaque avatar distant porte son pseudo à
40 cm au-dessus de la tête ; l'étiquette se tourne vers l'observateur. Une invitation
directe réutilise le pseudo mémorisé, ou demande de le personnaliser à l'accueil. Le pseudo
n'est pas ajouté au lien partagé et n'est pas un identifiant de compte unique.

Le bouton **Copier le lien du salon** permet d’inviter jusqu’à 12 visiteurs au total.
Les personnes ouvrant le même lien voient leurs avatars et leurs déplacements, y compris
les mains en VR. Le lien donne accès au salon : partagez-le avec vos invités.

Le serveur relaie les poses à 10 Hz et fournit une horloge commune à la fontaine.
Les avatars sont interpolés, retirés à la déconnexion et recréés après reconnexion.
Les salons restent en mémoire ; un salon vide est supprimé. Pas de compte, de stockage
des déplacements ni d'enregistrement des voix. Un redémarrage du serveur interrompt
brièvement la présence, puis les clients rejoignent automatiquement le même lien.

## Lancer localement

```sh
npm install
npm run dev
```

Le plugin Vite raccorde les salons WebSocket au serveur géré IWSDK sur `/rooms`.
Ouvrir le lien du salon dans deux onglets permet de vérifier la présence à deux.
`npm run preview` prend aussi en charge les salons après construction.

## Héberger pour des amis sur Internet

```sh
npm run build
npm start
```

Si l'hébergement reçoit le dossier `package/`, reconstruire ce dossier avec
`npm run build:package:ps1` sous Windows avant de l'envoyer : `npm run build`
met uniquement `dist/` à jour. Une compilation locale ne met pas le site public
à jour ; il faut transférer la livraison sur l'hébergement.

Le serveur Node sert `dist/` et les salons sur le même port (`PORT`, 8081 par défaut).
Il faut déployer ce processus sur un hébergement Node acceptant des connexions WebSocket
durables, avec une adresse publique **HTTPS**. Le navigateur utilise automatiquement
**WSS** pour `/rooms`. Le proxy doit transmettre les requêtes Upgrade et conserver le
nom d’hôte d’origine ; prévoir un délai d’inactivité supérieur à 30 secondes.
HTTPS est également nécessaire pour la VR sur casque hors de localhost.

Un lien `localhost` est utilisable sur le même ordinateur uniquement. Un lien contenant
une adresse LAN exige le même réseau ; pour des amis à distance, copiez le lien depuis
le domaine public hébergé. L’hébergement public n’est pas provisionné par le projet.

Utiliser **une seule instance Node**, ou configurer le proxy avec une affinité par code
de salon : la liste des participants n’est pas partagée entre processus. Le service
limite les poses à 2 Ko et la signalisation vocale à 32 Ko, leur fréquence, les files d’envoi, 12 visiteurs par salon,
512 salons et 1 024 connexions au total. Il valide les poses et refuse les origines
navigateur différentes de l’hôte servi. Une exposition à grande échelle demanderait
un service de présence partagé et des limites supplémentaires au niveau du proxy.

## Vérification

```sh
npm run typecheck
npm run test:rooms
```

Les tests ouvrent de vraies connexions WebSocket sur un port éphémère : présence à
deux, séparation des salons, poses de tête/mains, départ et retour, capacité, paquets
invalides ou trop grands, horloge et expiration des connexions silencieuses.

## Voix de proximité

Dans le panneau **Amis**, chaque joueur clique sur **Activer le micro**, puis autorise
son navigateur. Le même bouton permet de le couper et arrête la capture. **Écouter
les voix** permet aussi de recevoir sans activer son micro ; **Couper l'écoute**
coupe les voix entrantes. Ces commandes existent également dans le menu **M** au
clavier / **B** sur la manette droite en VR, et dans le panneau Amis sur mobile.
Si le navigateur suspend le son, **Reprendre l'écoute** permet de le relancer.

Pour un essai téléphone / Quest 3 sur le même Wi-Fi : rechargez la page sur les
deux appareils, ouvrez exactement le même lien de salon HTTPS, puis activez le
micro sur chacun. Le panneau doit indiquer **2 visiteurs** et **1 liaison**.
Restez proches dans le jardin pour le premier essai.

Les voix sont spatialisées à la tête de chaque avatar. Volume plein jusqu'à 1 m,
atténuation inverse ensuite, fondu vers le silence entre 20 et 25 m. Tourner la tête
change la direction du son. Les casques audio permettent d'entendre cet effet et
d'éviter que les haut-parleurs soient repris par les micros ; l'annulation d'écho
du navigateur est également demandée. Le flux local ne repasse pas dans sa propre
sortie audio.

L'audio passe par WebRTC entre les visiteurs du même salon ; le serveur WebSocket
relaie seulement SDP et ICE vers le destinataire validé. Le micro démarre uniquement
sur action du joueur. À la déconnexion, il est arrêté : réactivez-le après le retour
dans le salon. Aucune voix n'est enregistrée par l'application.

### Réseaux et relais TURN

HTTPS est obligatoire pour demander le micro hors de localhost. Le serveur fournit
un serveur STUN par défaut. Pour assurer la voix entre réseaux qui bloquent les
connexions directes (certains réseaux mobiles, entreprises ou NAT), configurez un
relais **TURN** dans l'environnement du processus Node/Vite, puis redémarrez-le :

```powershell
$env:VOICE_ICE_SERVERS = '[{"urls":"stun:stun.l.google.com:19302"},{"urls":["turn:turn.example.com:3478?transport=udp","turns:turn.example.com:5349?transport=tcp"],"username":"UTILISATEUR_TURN","credential":"MOT_DE_PASSE_TURN"}]'
npm start
```

Remplacer ces valeurs par celles du relais provisionné ; aucun compte TURN n'est
fourni avec le projet. Ces identifiants sont transmis aux clients WebRTC : utiliser
des identifiants à durée limitée lorsque le service TURN le permet. Le service
utilise un maillage direct (jusqu'à 11 connexions audio par visiteur).

Les tests de transport et de cycle de vie s'exécutent avec :

```sh
node --test tests/rooms.test.mjs tests/voice-session.test.mjs tests/comfort-menu.test.mjs
```

Le harnais `tests/voice-browser-harness.ts` vérifie aussi les vrais flux WebRTC
dans le navigateur géré : deux clients WebSocket, deux sources sonores synthétiques,
analyse du son reçu dans les deux sens, distance, coupure et réactivation. Il ne
demande pas le micro physique et sa sortie finale est silencieuse. Pour le relancer,
importer temporairement `installVoiceBrowserHarness` dans `src/index.ts`, l'appeler
avec `world` après les inscriptions des systèmes, puis entrer en XR pour fournir
le geste de démarrage audio. Lire `RoomConnection.status` et `voiceError` sur
l'entité `Vérification voix WebRTC`. Retirer l'import après l'essai ; il n'est pas
inclus dans l'application livrée.
