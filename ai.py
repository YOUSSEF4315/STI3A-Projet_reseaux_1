# ai.py
from __future__ import annotations
from typing import List, Any

from game import Game


class BaseController:
    def __init__(self, team: str, decision_interval: float = 0.5):
        """
        :param team: identifiant de l'équipe ("A", "B", etc.)
        :param decision_interval: temps simulé minimal entre deux décisions (en secondes)
        """
        self.team = team
        self.decision_interval = float(decision_interval)

    def decide_actions(self, game: Game) -> List[tuple[Any, ...]]:
        """
        Doit renvoyer une liste d'actions sous la forme :
        - ("move", unit, target_x, target_y)
        - ("attack", attacker, target)
        """
        raise NotImplementedError


class CaptainBraindead(BaseController):
    """
    Captain BRAINDEAD (IA n°1)
    - Ne donne aucun ordre de déplacement.
    - Les unités n'attaquent que si un ennemi est déjà dans leur ligne de vue
      et (idéalement) à portée.
    - Sinon elles ne font rien.
    """

    def __init__(self, team: str, decision_interval: float = 0.7):
        # Par défaut, Braindead décide assez rarement
        super().__init__(team, decision_interval)

    def decide_actions(self, game: Game) -> List[tuple[Any, ...]]:
        actions: List[tuple[Any, ...]] = []
        my_units = game.alive_units_of_team(self.team)
        enemies = game.enemy_units_of(self.team)

        for u in my_units:
            if not enemies:
                continue

            best_target = None
            best_dist = float("inf")

            los = float(getattr(u, "lineOfSight", 0.0))

            # On ne considère que les ennemis dans la line of sight
            for e in enemies:
                dist = game.map.distance(u, e)
                if dist <= los and dist < best_dist:
                    best_dist = dist
                    best_target = e

            if best_target is None:
                # Rien en vue -> aucune action / aucune intention
                continue

            # S'il est dans la portée d'attaque, on donne l'intention "attack"
            if hasattr(u, "in_range") and u.in_range(best_dist):
                u.intent = ("attack", best_target)
            # Sinon, Braindead ne bouge pas → il ne met pas d'intention de move

        # Plus besoin de renvoyer des actions, tout passe par intent
        return actions



class MajorDaft(BaseController):
    """
    Major DAFT (IA n°2)
    - Ordonne à chaque unité d'attaquer l'ENNEMI LE PLUS PROCHE,
      sans aucune autre considération.
    - Si l'ennemi est à portée -> attaque.
    - Sinon -> l'unité se déplace en ligne droite vers cet ennemi.
    - Le moteur de jeu (_do_move) se charge de limiter la distance
      parcourue à speed * dt.
    """

    def __init__(self, team: str, decision_interval: float = 0.3):
        # Daft réagit un peu plus souvent que Braindead
        super().__init__(team, decision_interval)


    def decide_actions(self, game: Game) -> List[tuple[Any, ...]]:
        actions: List[tuple[Any, ...]] = []
        my_units = game.alive_units_of_team(self.team)

        for u in my_units:
            # Trouver l'ennemi le plus proche
            target = game.find_closest_enemy(u)
            if target is None:
                continue

            # Distance réelle (euclidienne) entre u et target
            dist = game.map.distance(u, target)

            # Si on peut frapper, on frappe
            if hasattr(u, "in_range") and u.in_range(dist):
                u.intent = ("attack", target)
                continue

            # Sinon, on demande un mouvement vers la position de la cible
            target_x = float(getattr(target, "x", 0.0))
            target_y = float(getattr(target, "y", 0.0))
            u.intent = ("move_to", target_x, target_y)



        return actions



class AssasinJack(BaseController):
    """
    Assasin Jack (IA n°4)
    - Ordonne à chaque unité d'attaquer l'ennemi avec le moin de hp,
      sans aucune autre considération.
    - Si l'ennemi est à portée -> attaque.
    - Sinon -> l'unité se déplace en ligne droite vers cet ennemi.
    - Le moteur de jeu (_do_move) se charge de limiter la distance
      parcourue à speed * dt.
    """

    def __init__(self, team: str, decision_interval: float = 0.3):
        # Daft réagit un peu plus souvent que Braindead
        super().__init__(team, decision_interval)


    def decide_actions(self, game: Game) -> List[tuple[Any, ...]]:
        actions: List[tuple[Any, ...]] = []
        my_units = game.alive_units_of_team(self.team)

        for u in my_units:
            # 1. Chercher d'abord les ennemis faibles À PROXIMITÉ
            # On récupère tous les ennemis
            enemies = game.enemy_units_of(self.team)
            if not enemies:
                continue

            target = None
            best_score = float("inf") # On cherche le plus petit score (HP)
            
            # Paramètres
            MAX_CHASE_DIST = 15.0  # Ne pas chasser les faibles trop loin
            
            # On regarde les ennemis proches d'abord
            closest_enemy = None
            closest_dist = float("inf")

            for e in enemies:
                d = game.map.distance(u, e)
                hp = float(getattr(e, "hp", 100))
                
                # Garder trace du plus proche absolu (fallback)
                if d < closest_dist:
                    closest_dist = d
                    closest_enemy = e

                # Si l'ennemi est raisonnablement proche, on considère ses HP
                if d < MAX_CHASE_DIST:
                    # Score = HP (on veut le min)
                    if hp < best_score:
                        best_score = hp
                        target = e
            
            # Si aucun ennemi faible à portée, on se rabat sur le plus proche (Survie !)
            if target is None:
                target = closest_enemy

            if target is None:
                continue

            # Distance réelle (euclidienne) entre u et target
            dist = game.map.distance(u, target)

            # Si on peut frapper, on frappe
            if hasattr(u, "in_range") and u.in_range(dist):
                u.intent = ("attack", target)
                continue

            # Sinon, on demande un mouvement vers la position de la cible
            target_x = float(getattr(target, "x", 0.0))
            target_y = float(getattr(target, "y", 0.0))
            u.intent = ("move_to", target_x, target_y)

        return actions

class PredictEinstein(BaseController):
    """
    Predict Einstein (IA n°5)
    - Prédit dans 5 actions d'une unité si elle peut tuer une unité adverse
    - Ordonne à chaque unité d'attaquer l'ennemi auquel le moin d'actions sera
    nécessaire pour le tuer ( si cela est possible en moin de 5 actions ) 
    - Sinon , copie MajorDaft
        - Ordonne à chaque unité d'attaquer l'ENNEMI LE PLUS PROCHE,
      sans aucune autre considération.
        - Si l'ennemi est à portée -> attaque.
        - Sinon -> l'unité se déplace en ligne droite vers cet ennemi.
    - Le moteur de jeu (_do_move) se charge de limiter la distance
      parcourue à speed * dt.
    """

    def __init__(self, team: str, decision_interval: float = 0.3):
        # Daft réagit un peu plus souvent que Braindead
        super().__init__(team, decision_interval)


    def decide_actions(self, game: Game) -> List[tuple[Any, ...]]:
        actions: List[tuple[Any, ...]] = []
        my_units = game.alive_units_of_team(self.team)

        for u in my_units:
            # Trouver l'ennemi avec le moin de tours a faire pour le tuer ( en 5 ou moin )
            target = None
            tours_necessaires_min = float("inf")
            team = getattr(u, "team", None)
            enemies = game.enemy_units_of(team)
            for e in enemies:
                # Réinitialiser la position simulée pour chaque ennemi testé
                x = u.x
                y = u.y
                i = 0
                total_damage = 0
                while i < 5:
                    i = i + 1
                    """Renvoie le nombre de tours i nécessaire a tuer l'ennemi , jusqu'a essayer 5 tours."""
                    dx = e.x - x
                    dy = e.y - y
                    dist = (dy**2 + dx**2)**0.5
                    if dist > u.range :
                        speed = u.speed
                        dt = 1.0
                        step = speed * dt
                        if step >= dist:
                            x = e.x
                            y = e.y
                        else:
                            ux = dx / dist
                            uy = dy / dist
                            x = x + ux * step
                            y = y + uy * step
                        continue
                    total_damage += u.calculer_degats(e,1)
                    if total_damage >= e.hp:
                        if i < tours_necessaires_min:
                            tours_necessaires_min = i
                            target = e
                        break
                    continue
                    
            if target is None:
                # Trouver l'ennemi le plus proche
                target = game.find_closest_enemy(u)
                if target is None:
                     continue

            # Distance réelle (euclidienne) entre u et target
            dist = game.map.distance(u, target)

            # Si on peut frapper, on frappe
            if hasattr(u, "in_range") and u.in_range(dist):
                u.intent = ("attack", target)
                continue

            # Sinon, on demande un mouvement vers la position de la cible
            target_x = float(getattr(target, "x", 0.0))
            target_y = float(getattr(target, "y", 0.0))
            u.intent = ("move_to", target_x, target_y)



        return actions





class SimpleAI(MajorDaft):
    """
    Alias de MajorDaft pour compatibilité avec l'ancien code.
    Même comportement que MajorDaft.
    """
    pass
