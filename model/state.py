import dataclasses
from typing import List, Optional, Dict, Any

@dataclasses.dataclass
class UnitState:
    id: str                # Identifiant unique de l'unité (ex: id(unit))
    unit_type: str         # Type de l'unité (ex: "Knight", "Crossbowman")
    team: str              # Équipe ("A", "B")
    x: float               # Position X
    y: float               # Position Y
    hp: float              # Points de vie actuels
    max_hp: float          # Points de vie max
    cooldown: float        # Cooldown actuel
    intent: Optional[tuple]# Dernière intention (ex: ("attack", target_id))
    radius: float          # Pour le rendu de l'ombre/sélection
    speed: float           # Optionnel, si l'affichage a besoin d'interpoler

@dataclasses.dataclass
class GameState:
    time: float                     # Temps simulé
    running: bool                   # La partie est-elle en cours ?
    winner: Optional[str]           # Gagnant ("A" ou "B")
    units: List[UnitState]          # État de toutes les unités
    map_elevation: Dict[tuple, float] # Elevation (x, y) -> elev (optionnel, si on veut sync)
    # L'élévation de la carte ou les dimensions pourraient être transférées à part 
    # ou une seule fois à l'init. Gardons l'essentiel ici qui change souvent.
