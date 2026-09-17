# Bordures vocales des pseudos

Le microphone actif alimente un AnalyserNode local sans sortie sonore. Une FFT
de 1024 échantillons fournit trois bandes : 80–400 Hz, 400–2000 Hz et 2000–8000 Hz.
Une porte de niveau RMS élimine le silence, avec maintien de 180 ms entre syllabes.
Le prélèvement a lieu à 10 Hz, dans la sérialisation des poses, avec buffers réutilisés.
Référence : [Web Audio AnalyserNode](https://developer.mozilla.org/en-US/docs/Web/API/AnalyserNode).

Le champ facultatif `voice: [grave, medium, aigu]` contient trois nombres entre
0 et 1, arrondis à deux décimales. Le serveur vérifie sa forme et ses bornes puis
le diffuse aux autres membres du salon avec l'identité authentifiée de la connexion.
Les anciens clients qui omettent ce champ restent compatibles et apparaissent
silencieux. Chaque participant est indépendant : plusieurs personnes peuvent
être indiquées simultanément. L'écoute audio et la distance vocale ne conditionnent
pas cet indicateur distribué par WebSocket. Le serveur déployé doit être mis à jour
avec le client pour relayer le nouveau champ.

La bordure varie de 3 à 19 pixels dans la texture du nametag selon une combinaison
des trois bandes (40 %, 40 %, 20 %), avec attaque et retour au repos interpolés.
Le shader du SpriteMaterial conserve le texte et son unique texture ; aucune
rastérisation de texte n'a lieu par frame. Une pose absente depuis 750 ms fait
revenir la bordure au repos. Couper le micro transmet des bandes nulles au prochain
paquet. Les nametags figurent aussi dans les miroirs.

Validation : tests des bandes à 44,1 et 48 kHz, silence/suspension/dispose,
indépendance des bordures, absence de mise à jour de texture par frame, et test
réseau avec deux émetteurs simultanés et un troisième participant. Le runtime
managé a reçu deux sources indépendantes, montré leurs bordures épaisses, puis
les a ramenées au repos. Cette vérification utilisait des niveaux synthétiques,
sans microphone réel. Rapport de 35 tests : `artifacts/mirror-voice/tests.txt`.

La détection de niveau n'identifie pas le locuteur au sein d'un microphone partagé :
le nametag correspond au joueur propriétaire de ce microphone. Un bruit ambiant
assez fort peut également animer sa bordure.
