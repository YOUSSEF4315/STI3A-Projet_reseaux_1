# Documentation de la Restructuration Architecturale (Préparation Réseau)

## Objectif
L'objectif de cette restructuration était de préparer l'architecture du jeu vidéo pour implémenter un mode multijoueur en réseau. Pour qu'un jeu en réseau fonctionne de manière fluide (sans désynchronisation), il est impératif de séparer :
1. **La logique du jeu** (Moteur de jeu, calculs des dégâts, mouvements).
2. **L'État du jeu** (Les données brutes : positions, points de vie, état des cooldowns).
3. **L'Affichage** (La vue Pygame qui dessine les éléments sur l'écran).

Avant ces modifications, l'affichage lisait directement l'état des objets complexes du moteur de jeu. Cela rendait impossible l'envoi de ces données sur un réseau (on ne peut pas envoyer des objets Python `Guerrier` complexes contenant des méthodes et d'autres références).

## Ce que nous avons fait, étape par étape :

### Étape 1 : Création de l'État Sérialisable (Data Transfer Object)
**Fichier créé :** `model/state.py`
Nous avons créé des classes de données pures (`dataclass`) : `UnitState` et `GameState`.
- Elles ne contiennent aucune méthode de calcul.
- Elles ne contiennent que des types simples (int, float, string).
- Elles représentent une "photographie" à un instant *T* de la bataille. C'est exactement ce paquet d'informations qui transitera plus tard sur le réseau (via JSON ou Pickle).

### Étape 2 : Le moteur de jeu capture son propre État
**Fichier modifié :** `model/game.py`
Nous avons ajouté la méthode `export_state()` à la classe `Game`.
À n'importe quel moment de la simulation, le moteur de jeu peut compiler toutes ses variables internes et ses unités pour créer une instance propre de `GameState`.

### Étape 3 : Isolation Complète de la Vue
**Fichier modifié :** `view/views.py`
La classe `GUI` a été modifiée en profondeur.
- Auparavant, la boucle `draw()` fouillait dans l'objet `Game` (`game.alive_units()`).
- Maintenant, la méthode s'utilise ainsi : `draw(screen, state=mon_game_state)`.
- La vue lit _uniquement_ cet état (`UnitState`) pour récupérer les positions X/Y, la santé et l'intention, et se charge du rendu visuel. Elle n'a plus besoin du moteur de jeu. C'est l'essence même du Client réseau : il reçoit l'état et ne fait que l'afficher !

### Étape 4 : Mise à jour des points d'entrée
**Fichiers modifiés :** `visual_simulation.py` et `presenter/battle.py`
Nous avons mis à jour la boucle principale des applications pour faire la passerelle :
1. Le jeu calcule le nouveau tour (`game.step()`).
2. On extrait l'état : `current_state = game.export_state()`.
3. On envoie cet état à l'affichage : `gui.draw(screen, state=current_state)`.

## Prochaine étape pour le projet réseau
Avec cette architecture, implémenter un serveur est facile :
- **Serveur :** Gère `Game` et `game.step()`. À chaque tour de boucle, il fait `game.export_state()`, transforme cet état en bytes (JSON), et l'envoie sur les Sockets des clients.
- **Client :** Ne crée **pas** le moteur de `Game`. Il ne fait qu'écouter le réseau, recevoir le paquet JSON, créer un objet `GameState` depuis ce texte, et appeler `gui.draw(screen, state)`.
