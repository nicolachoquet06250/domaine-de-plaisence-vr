# Voix de proximité

Fonction ajoutée au salon existant (planification QUICK). Hypothèses : activation volontaire du micro, écoute et micro séparément désactivables, pas d'enregistrement, émission omnidirectionnelle. Volume plein à 1 m, atténuation inverse et extinction progressive entre 20 et 25 m. La position et l'orientation de l'auditeur suivent la tête VR ou la caméra navigateur ; les sources suivent les têtes interpolées des avatars.

## Grounding

- IWSDK 0.5.3 installé : RemoteVisitor et RoomConnection existants, systèmes/priorités et requêtes ECS réutilisés. AudioSource/AudioSystem chargent des fichiers et pools de buffers ; aucun champ MediaStream et listener privé dans les déclarations. Les voix distantes nécessitent donc un graphe Web Audio dédié, sans modifier AudioSystem ni activer une nouvelle feature du monde.
- Reference status : warmupRequired, repli sur les déclarations installées et les spécifications Web.
- WebRTC : https://www.w3.org/TR/webrtc/ et https://webrtc.org/getting-started/peer-connections-advanced. RTCPeerConnection, piste audio sendrecv, SDP et ICE via le WebSocket du salon ; initiateur déterministe par identifiant. Aucun audio dans les messages WebSocket.
- Web Audio : https://www.w3.org/TR/webaudio-1.0/. MediaStreamAudioSourceNode -> PannerNode HRTF -> GainNode de portée -> gain d'écoute -> destination. Contexte démarré par interaction, flux local jamais connecté aux haut-parleurs.
- Contrôles DOM dans le panneau Amis ; mêmes actions dans le panneau UIKitML Confort accessible avec M/B. Déclarations des diagnostics dans un module sans système.

## Architecture et cycle de vie

Signalisation limitée au même salon et destinataire ; identité émettrice imposée par le serveur, validation SDP/ICE et quotas dédiés. Configuration ICE envoyée au welcome ; STUN par défaut, TURN configurable côté serveur via VOICE_ICE_SERVERS. Le relais TURN reste nécessaire pour certains réseaux restrictifs et doit être provisionné par l'hébergeur.

VoiceSession possède les connexions WebRTC, pistes et graphe audio, en lien avec MultiplayerSystem. Son adaptateur ECS met à jour listener/sources après interpolation des avatars. Les événements réseau créent et ferment les pairs. Déconnexion, départ, piste terminée, refus de permission et destruction libèrent les ressources ; une acquisition micro terminée après annulation est immédiatement arrêtée. Aucun tableau d'entités parallèle ni allocation dans la boucle de rendu.

## Vérification prévue

Tests réseau réels pour routage, isolation, limites et reconnexion ; tests de cycle de vie avec API Web substituées ; contrôle de la courbe de volume, pose de l'auditeur et des sources ; TypeScript et build. Preview UIKitML, runtime/ECS et vérification du navigateur géré. Ne pas présenter des doubles d'API ou l'émulation comme un appel vocal entendu sur deux appareils physiques.

## Résultats du 6 septembre 2026

Le test avec de vrais RTCPeerConnection a reproduit deux défauts que les doubles d'API ne détectaient pas : un transceiver créé trop tôt par le répondant restait sans mid négocié (deux transceivers, sendonly/recvonly), puis les paquets reçus n'étaient pas décodés par Chromium sans élément média en lecture. Le répondant réutilise désormais le transceiver créé par l'offre distante et le passe en sendrecv avant sa réponse. Un élément audio muet démarre le décodage ; seul le graphe spatial est audible. Le graphe et cet élément sont libérés ensemble.

Harnais navigateur, deux clients dans un salon aléatoire, micro synthétique activé après connexion : RMS à 1 m 0,058420 ; sens inverse 0,027562 ; à 10 m 0,005842 (ratio 0,099998) ; à 30 m 0 ; après coupure 0 ; après réactivation 0,577152 (nouvelle source synthétique d'amplitude différente). Octets audio reçus dans les deux sens : 12610 et 12295. Aucun micro physique capturé, aucune sortie de test audible. Harnais retiré de l'entrée de l'application après vérification.

22 tests Node réussis, TypeScript sans erreur. Preview UIKitML lisible, ouverture du menu par B et activation/désactivation réelle de l'écoute par rayon de manette vérifiées dans le runtime Meta Quest 3 émulé. Essai physique smartphone / Quest 3 à refaire par l'utilisateur après rechargement des deux pages.
