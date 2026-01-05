import math
from typing import List, Tuple, Optional

class SmartAI:    
    def __init__(self, team: str, decision_interval: float = 0.3):
        self.team = team
        self.decision_interval = decision_interval
        self.formation_set = False
    
    # Calculs de dégats
    
    def get_damage_i_deal(self, my_unit, enemy) -> float:
        #Calcule les dégâts que je fais
        damage = my_unit.calculer_degats(enemy, k_elev=1.0)
        
        # Ajuste la précision pour Crossbowman vu qu'il peut rater
        from crossbowman import Crossbowman
        if isinstance(my_unit, Crossbowman):
            damage *= (my_unit.accuracy / 100.0)
        
        return damage
    
    def get_damage_i_receive(self, my_unit, enemy) -> float:
        #Calcule les dégâts que je reçois
        damage = enemy.calculer_degats(my_unit, k_elev=1.0)
        
        # Si ennemi = Crossbowman : ajuste aussi la précision 
        from crossbowman import Crossbowman
        if isinstance(enemy, Crossbowman):
            damage *= (enemy.accuracy / 100.0)
        
        return damage
    
    def calculate_efficiency_ratio(self, my_unit, enemy) -> float:
        #Si le ratio d'efficacité > 1.0 = bon matchup, < 1.0 = mauvais matchup 
        damage_dealt = self.get_damage_i_deal(my_unit, enemy)
        damage_received = self.get_damage_i_receive(my_unit, enemy)
        
        if damage_received == 0:
            return float('inf') 
        
        if damage_dealt == 0:
            return 0.0 
        
        return damage_dealt / damage_received
    
    # Choix de cible
    
    def choose_best_target(self, attacker, enemies: List) -> Optional: # type: ignore
        if not enemies:
            return None
        
        # Trouve l'ennemi avec le meilleur ratio d'efficacité
        best_target = max(enemies, key=lambda e: self.calculate_efficiency_ratio(attacker, e))
        
        # Attaque seulement si on peut faire des dégâts
        if self.calculate_efficiency_ratio(attacker, best_target) > 0:
            return best_target
        
        return None
    
    # Logique de retraite
    
    def should_retreat(self, unit, enemies: List, game) -> Tuple[bool, object | None]:
        """2 Conditions de fuite:
        1. KITING: Archer avec mêlée trop proche
        2. MATCHUP PERDANT: Ennemi me tue bien plus vite"""
        from knight import Knight
        from pikeman import Pikeman
        from crossbowman import Crossbowman
        
        for enemy in enemies:
            distance = game.map.distance(unit, enemy)
            
            # CAS 1: KITING (Archer doit garder ses distances)
            if isinstance(unit, Crossbowman) and isinstance(enemy, (Knight, Pikeman)):
                speed_ratio = enemy.speed / unit.speed if unit.speed > 0 else 1.0
                
                # Zone dangereuse
                threat_distance = enemy.get_reach() * (1 + speed_ratio * 0.5)
                
                if distance < threat_distance:
                    return (True, enemy)
            
            # CAS 2: MATCHUP PERDANT
            my_damage = self.get_damage_i_deal(unit, enemy)
            enemy_damage = self.get_damage_i_receive(unit, enemy)
            
            # Impossible de blesser l'ennemi donc fuir s'il approche
            if my_damage <= 0:
                if distance < enemy.get_reach() * 3:
                    return (True, enemy)
                continue
            
            # Ennemi ne peut pas me blesser donc pas de danger
            if enemy_damage <= 0:
                continue
            
            # Calcul du temps pour tuer
            shots_to_kill_enemy = math.ceil(enemy.hp / my_damage)
            shots_enemy_kills_me = math.ceil(unit.hp / enemy_damage)
            
            time_i_kill_enemy = shots_to_kill_enemy * unit.reloadTime
            time_enemy_kills_me = shots_enemy_kills_me * enemy.reloadTime
            
            # Fuite si: il me tue en - 80% du temps que je le tue
            losing_badly = time_enemy_kills_me < time_i_kill_enemy * 0.8
            enemy_is_close = distance < unit.range * 1.5
            
            if losing_badly and enemy_is_close:
                return (True, enemy)
        
        return (False, None)
    
    def get_retreat_position(self, unit, danger, game) -> Tuple[float, float]:
        # Direction opposée au danger
        dx = unit.x - danger.x
        dy = unit.y - danger.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            dx /= distance  # Normaliser
            dy /= distance
            
            # Distance de retraite = max(4, portée de l'unité)
            retreat_distance = max(4.0, unit.range)
            dx *= retreat_distance
            dy *= retreat_distance
        
        new_x = unit.x + dx
        new_y = unit.y + dy
        
        # Rester dans les limites de la carte
        new_x = max(0.0, min(game.map.cols - 1, new_x))
        new_y = max(0.0, min(game.map.rows - 1, new_y))
        
        return (new_x, new_y)
    
    # Formation
    
    def setup_formation(self, units: List, game):
        """Positionne les unités avec cette tactique:
        - Knights devant (HP élevée, mêlée)
        - Pikemen au milieu (HP moyenne, mêlée)
        - Crossbowmen derrière (HP faible, distance)"""
        from knight import Knight
        from pikeman import Pikeman
        from crossbowman import Crossbowman
        
        knights = [u for u in units if isinstance(u, Knight)]
        pikemen = [u for u in units if isinstance(u, Pikeman)]
        crossbows = [u for u in units if isinstance(u, Crossbowman)]
        
        if not units:
            return
        
        # Centre de la formation
        center_x = sum(u.x for u in units) / len(units)
        center_y = sum(u.y for u in units) / len(units)
        
        # Knights à l'avant
        y = center_y - len(knights)
        for knight in knights:
            knight.intent = ("move_to", center_x, y)
            y += 2.0
        
        # Pikemen au milieu (2 tuiles en arrière)
        y = center_y - len(pikemen)
        for pikeman in pikemen:
            pikeman.intent = ("move_to", center_x - 2.0, y)
            y += 2.0
        
        # Crossbowmen derrière (4 tuiles en arrière)
        y = center_y - len(crossbows)
        for crossbow in crossbows:
            crossbow.intent = ("move_to", center_x - 4.0, y)
            y += 2.0
    
    # Décision principale
    
    def decide_actions(self, game) -> List:
        """Pour chaque unité:
        1. Vérifier si doit fuir
        2. Sinon, choisir meilleure cible
        3. Attaquer si en portée, sinon avancer"""
        my_units = game.alive_units_of_team(self.team)
        enemies = game.enemy_units_of(self.team)
        
        if not enemies:
            return []
        
        # Formation initiale
        if not self.formation_set and my_units:
            self.setup_formation(my_units, game)
            self.formation_set = True
            return []
        
        # Décision pour chaque unité
        for unit in my_units:
            # Dois-je fuir ?
            should_flee, danger = self.should_retreat(unit, enemies, game)
            
            if should_flee and danger:
                retreat_x, retreat_y = self.get_retreat_position(unit, danger, game)
                unit.intent = ("move_to", retreat_x, retreat_y)
                continue
            
            # Choisir meilleure cible
            target = self.choose_best_target(unit, enemies)
            
            if not target:
                continue
            
            distance = game.map.distance(unit, target)
            
            # En portée ? Attaquer : Avancer
            if unit.in_range(distance):
                unit.intent = ("attack", target)
            else:
                unit.intent = ("move_to", target.x, target.y)
        
        return []