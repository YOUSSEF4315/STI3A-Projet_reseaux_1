from __future__ import annotations
from typing import List, Any
import math

from game import Game
from ai import BaseController


class SmartAI(BaseController):
    """
    PROBLÈME : Les archers ne peuvent PAS kite les knights (trop lents)
    SOLUTION : Formation défensive + Focus Fire INTELLIGENT
    """

    def __init__(self, team: str, decision_interval: float = 0.1):
        super().__init__(team, decision_interval)
        
    def decide_actions(self, game: Game) -> List[tuple[Any, ...]]:
        actions: List[tuple[Any, ...]] = []
        my_units = game.alive_units_of_team(self.team)
        enemies = game.enemy_units_of(self.team)
        
        if not my_units or not enemies:
            return actions
        
        # Séparer par type
        my_crossbows = [u for u in my_units if u.__class__.__name__ == "Crossbowman"]
        my_pikemen = [u for u in my_units if u.__class__.__name__ == "Pikeman"]
        my_knights = [u for u in my_units if u.__class__.__name__ == "Knight"]
        
        enemy_crossbows = [e for e in enemies if e.__class__.__name__ == "Crossbowman"]
        enemy_pikemen = [e for e in enemies if e.__class__.__name__ == "Pikeman"]
        enemy_knights = [e for e in enemies if e.__class__.__name__ == "Knight"]
        
        # STRATÉGIE DIFFÉRENTE selon la composition
        if my_crossbows and enemy_knights:
            # On a des archers vs des knights -> DANGER
            self._anti_knight_strategy(my_crossbows, my_pikemen, my_knights, 
                                      enemy_knights, enemies, game)
        elif my_crossbows:
            # On a des archers -> Focus fire sur cibles prioritaires
            self._archer_focus_fire(my_crossbows, enemies, game)
        
        # Comportement des pikemen
        for pike in my_pikemen:
            self._pikeman_behavior(pike, enemy_knights, enemies, game)
        
        # Comportement des knights
        for knight in my_knights:
            self._knight_behavior(knight, enemies, game)
        
        return actions
    
    def _anti_knight_strategy(self, my_crossbows, my_pikemen, my_knights,
                             enemy_knights, all_enemies, game):
        """
        Stratégie anti-knight :
        1. Les pikemen BLOQUENT les knights (bonus +8 dmg vs knights)
        2. Les crossbows tirent sur les knights depuis derrière
        3. Formation serrée pour se protéger
        """
        if not my_crossbows:
            return
        
        # Trouver le knight ennemi le plus proche de nos archers
        closest_knight = None
        min_dist = float("inf")
        
        for knight in enemy_knights:
            avg_dist = sum(game.map.distance(cb, knight) for cb in my_crossbows) / len(my_crossbows)
            if avg_dist < min_dist:
                min_dist = avg_dist
                closest_knight = knight
        
        if closest_knight is None:
            closest_knight = enemy_knights[0] if enemy_knights else all_enemies[0]
        
        # TOUS les crossbows tirent sur le knight le plus proche
        for cb in my_crossbows:
            dist = game.map.distance(cb, closest_knight)
            
            if hasattr(cb, "in_range") and cb.in_range(dist):
                # À portée -> TIRER
                cb.intent = ("attack", closest_knight)
            else:
                # Hors portée -> Avancer LÉGÈREMENT (juste assez pour tirer)
                if dist > 5.5:  # Un peu au-delà de la portée
                    target_x = float(getattr(closest_knight, "x", 0.0))
                    target_y = float(getattr(closest_knight, "y", 0.0))
                    cb.intent = ("move_to", target_x, target_y)
                else:
                    # Rester en position et attendre la portée
                    cb.intent = ("attack", closest_knight)
    
    def _archer_focus_fire(self, archers, enemies, game):
        """
        Focus fire intelligent pour les archers :
        1. Priorité aux archers ennemis (1v1 archer)
        2. Puis pikemen (faciles à tuer)
        3. Enfin knights (tanks)
        """
        # Trouver la meilleure cible
        target = self._choose_archer_target(archers, enemies, game)
        
        if target is None:
            return
        
        # TOUS les archers tirent sur cette cible
        for archer in archers:
            dist = game.map.distance(archer, target)
            
            if hasattr(archer, "in_range") and archer.in_range(dist):
                archer.intent = ("attack", target)
            else:
                # Avancer pour tirer
                target_x = float(getattr(target, "x", 0.0))
                target_y = float(getattr(target, "y", 0.0))
                archer.intent = ("move_to", target_x, target_y)
    
    def _choose_archer_target(self, my_archers, enemies, game):
        """Choisit la meilleure cible pour les archers"""
        if not enemies:
            return None
        
        best_target = None
        best_score = -float("inf")
        
        for enemy in enemies:
            score = 0.0
            hp = float(getattr(enemy, "hp", 100))
            max_hp = 100.0  # Approximation
            
            enemy_type = enemy.__class__.__name__
            
            # PRIORITÉ 1 : Archers ennemis (menace directe)
            if enemy_type == "Crossbowman":
                score += 150
            
            # PRIORITÉ 2 : Ennemis à faible HP (finition)
            hp_ratio = hp / max_hp
            if hp_ratio < 0.3:
                score += 100
            elif hp_ratio < 0.5:
                score += 60
            
            # PRIORITÉ 3 : Pikemen (faciles, pas de armor pierce)
            if enemy_type == "Pikeman":
                score += 40
            
            # PRIORITÉ 4 : Knights en dernier (tanks)
            if enemy_type == "Knight":
                score += 10
            
            # Bonus proximité
            avg_dist = sum(game.map.distance(a, enemy) for a in my_archers) / len(my_archers)
            score += max(0, 30 - avg_dist * 2)
            
            if score > best_score:
                best_score = score
                best_target = enemy
        
        return best_target
    
    def _pikeman_behavior(self, pike, enemy_knights, all_enemies, game):
        """
        Pikemen = ANTI-KNIGHTS (+8 dmg bonus)
        Ils doivent BLOQUER et TUER les knights
        """
        # Si des knights ennemis existent, les cibler en priorité
        if enemy_knights:
            target = min(enemy_knights, key=lambda k: game.map.distance(pike, k))
        else:
            # Sinon, cible la plus proche
            target = min(all_enemies, key=lambda e: game.map.distance(pike, e))
        
        dist = game.map.distance(pike, target)
        
        if hasattr(pike, "in_range") and pike.in_range(dist):
            pike.intent = ("attack", target)
        else:
            target_x = float(getattr(target, "x", 0.0))
            target_y = float(getattr(target, "y", 0.0))
            pike.intent = ("move_to", target_x, target_y)
    
    def _knight_behavior(self, knight, enemies, game):
        """
        Knights = RUSH
        Foncent sur la cible la plus dangereuse
        """
        # Priorité : archers > pikemen > knights
        target = None
        
        # Chercher des archers ennemis
        enemy_archers = [e for e in enemies if e.__class__.__name__ == "Crossbowman"]
        if enemy_archers:
            target = min(enemy_archers, key=lambda a: game.map.distance(knight, a))
        else:
            # Sinon plus proche
            target = min(enemies, key=lambda e: game.map.distance(knight, e))
        
        dist = game.map.distance(knight, target)
        
        if hasattr(knight, "in_range") and knight.in_range(dist):
            knight.intent = ("attack", target)
        else:
            target_x = float(getattr(target, "x", 0.0))
            target_y = float(getattr(target, "y", 0.0))
            knight.intent = ("move_to", target_x, target_y)