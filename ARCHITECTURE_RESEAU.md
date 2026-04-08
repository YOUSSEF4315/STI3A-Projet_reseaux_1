# Documentation de la Restructuration Architecturale (Préparation Réseau)

## Objectif
L'objectif de cette restructuration était de préparer l'architecture du jeu vidéo pour implémenter un mode multijoueur en réseau. Pour qu'un jeu en réseau fonctionne de manière fluide (sans désynchronisation), il est impératif de séparer :
1. **La logique du jeu** (Moteur de jeu, calculs des dégâts, mouvements).
2. **L'État du jeu** (Les données brutes : positions, points de vie, état des cooldowns).
3. **L'Affichage** (La vue Pygame qui dessine les éléments sur l'écran).

Avant ces modifications, l'affichage lisait directement l'état des objets complexes du moteur de jeu. Cela rendait impossible l'envoi de ces données sur un réseau (on ne peut pas envoyer des objets Python `Guerrier` complexes contenant des méthodes et d'autres références).

---

## Qu'avons-nous fait ? (Étape par étape)

### Partie 1 : Séparation de l'Architecture

#### Étape 1 : Création de l'État Sérialisable (Data Transfer Object)
**Fichier créé :** `model/state.py`
Nous avons créé des classes de données pures (`dataclass`) : `UnitState` et `GameState`.
- Elles ne contiennent aucune méthode de calcul.
- Elles ne contiennent que des types simples (int, float, string).
- Elles représentent une "photographie" à un instant *T* de la bataille. C'est exactement ce paquet d'informations qui transitera plus tard sur le réseau (via JSON ou Pickle).

#### Étape 2 : Le moteur de jeu capture son propre État
**Fichier modifié :** `model/game.py`
Nous avons ajouté la méthode `export_state()` à la classe `Game`.
À n'importe quel moment de la simulation, le moteur de jeu peut compiler toutes ses variables internes et ses unités pour créer une instance propre de `GameState`.

#### Étape 3 : Isolation Complète de la Vue
**Fichier modifié :** `view/views.py`
La classe `GUI` a été modifiée en profondeur.
- Auparavant, la boucle `draw()` fouillait dans l'objet `Game` (`game.alive_units()`).
- Maintenant, la méthode s'utilise ainsi : `draw(screen, state=mon_game_state)`.
- La vue lit _uniquement_ cet état (`UnitState`) pour récupérer les positions X/Y, la santé et l'intention, et se charge du rendu visuel. Elle n'a plus besoin du moteur de jeu. C'est l'essence même du Client réseau : il reçoit l'état et ne fait que l'afficher !

#### Étape 4 : Mise à jour des points d'entrée
**Fichiers modifiés :** `visual_simulation.py` et `presenter/battle.py`
Nous avons mis à jour la boucle principale des applications pour faire la passerelle :
1. Le jeu calcule le nouveau tour (`game.step()`).
2. On extrait l'état : `current_state = game.export_state()`.
3. On envoie cet état à l'affichage : `gui.draw(screen, state=current_state)`.


### Partie 2 : Développement du Pont Réseau (Preuve de Concept)

Pour valider que la communication entre le jeu Python et une IA externe (en C) est possible, nous avons suivi les consignes (utiliser **TCP**, un port local `5000` et **JSON**) en créant un mini-projet de test indépendant dans le dossier `network_poc`.

#### Étape 5 : Le Serveur Python
**Fichier créé :** `network_poc/server.py`
Un script simple qui ouvre un socket TCP (`localhost:5000`). Dès qu'un client se connecte, il "simule" un `GameState`, le convertit en texte JSON, et l'envoie sur le réseau. Puis, il attend une réponse JSON en retour.

#### Étape 6 : Le Client C
**Fichiers créés :** `network_poc/client.c` et `network_poc/Makefile`
Un véritable programme C, compilé en exécutable. Il utilise les sockets POSIX pour se connecter au serveur `127.0.0.1:5000`. 
Il réceptionne le texte JSON envoyé par Python, le lit, puis envoie en retour sa propre décision encapsulée dans un JSON (ex: `{"action": "attack", "target": "u2"}`).

> **Résultat :** Lors du test, le C lit parfaitement le monde simulé par Python, et Python décode instantanément l'action que l'IA C lui ordonne. La boucle complète Réseau + Données est validée !

---

### Partie 3 : Connexion P2P en C (Joueur contre Joueur)

Afin de permettre à deux programmes C de s'affronter sur le même réseau local, nous avons conçu un noeud P2P complet en C.

#### Étape 7 : Le Noeud Peer-to-Peer (`p2p_node.c`)
Vu que deux exécutables C doivent communiquer, l'un des deux doit impérativement devenir le serveur de la conversation. Le fichier `network_poc/p2p_node.c` contient l'implémentation des deux modes. Il est paramétrable via les arguments du terminal :

- **Pour le Joueur 1 (Hôte) :** `./p2p_node --host 5000` (Écoute et attend une connexion).
- **Pour le Joueur 2 (Client) :** `./p2p_node --connect 192.168.1.X 5000` (Se connecte à l'adresse IP de l'hôte).

Les deux échangent avec succès des JSON en `C-to-C` !

---

## Prochaine étape pour le projet grand format
Maintenant que ces concepts sont démontrés indépendamment, l'objectif sera de les fusionner :
- Modifier `visual_simulation.py` (ou créer un `server_main.py`) pour tourner le vrai jeu et envoyer via Socket son vériable `game.export_state()`.
- Programmer votre IA en C de manière à ce qu'elle lise en boucle les données réseaux, calcule une stratégie, et renvoie de ses nouvelles intentions.
