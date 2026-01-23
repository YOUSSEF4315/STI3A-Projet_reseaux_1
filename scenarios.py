from game import Game
from map import BattleMap
from ai import CaptainBraindead, MajorDaft,AssasinJack,PredictEinstein
from knight import Knight
from pikeman import Pikeman
from crossbowman import Crossbowman
from smartAI import GeneralStrategus

def scenario_simple_vs_braindead() -> Game:
    # 1. LA TAILLE LÉGALE (120x120)
    rows, cols = 120, 120 
    battle_map = BattleMap(rows=rows, cols=cols)

    controllers = {
        "A": MajorDaft("A"),
        "B": PredictEinstein("B"),
        
    }

    game = Game(battle_map, controllers)

    # 2. CALCUL DU CENTRE
    center_r = rows // 2
    center_c = cols // 2

    # Espacement entre les unités pour qu'elles ne soient pas collées
    SPACING = 2 

    # ---------------------------------------------------------
    # ARMÉE A (Bleus) - Gauche
    # ---------------------------------------------------------
    # On positionne l'armée autour de la colonne 40
    base_col_A = center_c - 20
    
    # MUR DE PIQUIERS (3 colonnes x 20 lignes = 60 unités)
    # Ils sont en première ligne
    for c in range(base_col_A + 4, base_col_A + 7): 
        for r in range(center_r - 20, center_r + 20, 2): 
            game.add_unit(Pikeman(), "A", row=r, col=c)

    # CHEVALIERS (2 colonnes x 10 lignes = 20 unités)
    # Juste derrière les piquiers
    for c in range(base_col_A, base_col_A + 3, 2):
        for r in range(center_r - 10, center_r + 10, 2):
            game.add_unit(Knight(), "A", row=r, col=c)

    # ARBALÉTRIERS (1 colonne large à l'arrière)
    for r in range(center_r - 25, center_r + 25, 2):
        game.add_unit(Crossbowman(), "A", row=r, col=base_col_A - 4)


    # ---------------------------------------------------------
    # ARMÉE B (Rouges) - Droite
    # ---------------------------------------------------------
    # On positionne l'armée autour de la colonne 80
    base_col_B = center_c + 20
    
    # MUR DE PIQUIERS (Face à l'ennemi)
    for c in range(base_col_B - 7, base_col_B - 4):
        for r in range(center_r - 20, center_r + 20, 2):
            game.add_unit(Pikeman(), "B", row=r, col=c)

    # CHEVALIERS
    for c in range(base_col_B - 3, base_col_B, 2):
        for r in range(center_r - 10, center_r + 10, 2):
            game.add_unit(Knight(), "B", row=r, col=c)

    # ARBALÉTRIERS (Fond)
    for r in range(center_r - 25, center_r + 25, 2):
        game.add_unit(Crossbowman(), "B", row=r, col=base_col_B + 4)

    print(f"Scénario généré : {len(game.units)} unités prêtes au combat sur {rows}x{cols}.")
    return game
def scenario_small_terminal() -> Game:
    """ 
    Petit Scénario (30x15) MAIS dense pour la vue Terminal.
    Plus de guerriers pour une vraie mêlée immédiate.
    Les unités sont centrées autour de la colonne 15.
    """
    rows, cols = 120, 120
    battle_map = BattleMap(rows=rows, cols=cols)

    controllers = {
        "A": MajorDaft("A"),
        "B": CaptainBraindead("B"),
    }

    game = Game(battle_map, controllers)
    
    # Calcul du centre exact
    mid_r = rows // 2   # ~7
    mid_c = cols // 2   # ~15

    # --- ÉQUIPE A (Gauche) - Centrée vers mid_c - 5 ---
    # Arbalétriers en fond (Centre - 7)
    for r in range(mid_r - 4, mid_r + 5): 
        game.add_unit(Crossbowman(), "A", r, mid_c - 11)
    
    # Chevaliers au milieu (Centre - 5)
    for r in range(mid_r - 3, mid_r + 4): 
        game.add_unit(Knight(), "A", r, mid_c - 7)

    # Piquiers devant (Centre - 3) -> Prêts au contact
    for r in range(mid_r - 5, mid_r + 6): 
        game.add_unit(Pikeman(), "A", r, mid_c - 5)


    # --- ÉQUIPE B (Droite) - Centrée vers mid_c + 5 ---
    # Piquiers devant (Centre + 3) -> Face à face !
    for r in range(mid_r - 5, mid_r + 6):
        game.add_unit(Pikeman(), "B", r, mid_c + 5)

    # Chevaliers au milieu (Centre + 5)
    for r in range(mid_r - 3, mid_r + 4):
        game.add_unit(Knight(), "B", r, mid_c + 7)

    # Arbalétriers en fond (Centre + 7)
    for r in range(mid_r - 4, mid_r + 5):
        game.add_unit(Crossbowman(), "B", r, mid_c +11 )

    print(f"Scénario 'Terminal Dense Centré' généré : {len(game.units)} unités sur {rows}x{cols}.")
    return game

def scenario_lanchester(unit_type_str: str, N: int) -> Game:
    """
    Crée un scénario N vs 2N pour vérifier les lois de Lanchester.
    Les armées sont placées horizontalement et bien espacées.
    """
    
    # 1. Configuration de la Map (Plus large pour l'espacement)
    rows, cols = 120, 120
    battle_map = BattleMap(rows=rows, cols=cols)

    # 2. Les IA
    controllers = {
        "A": MajorDaft("A"),
        "B": MajorDaft("B"), 
    }

    game = Game(battle_map, controllers)

    # 3. Sélection de la classe
    unit_class = None
    if unit_type_str == "knight": unit_class = Knight
    elif unit_type_str == "pikeman": unit_class = Pikeman
    elif unit_type_str == "crossbowman": unit_class = Crossbowman
    else: 
        print(f"Type inconnu '{unit_type_str}', défaut sur Pikeman")
        unit_class = Pikeman

    # 4. Placement Équipe A (N unités) - Gauche
    center_row = rows // 2
    
    # Position de départ très à gauche (colonne 5)
    start_col_A = 5
    
    # Formation Horizontale : On remplit les colonnes (X) avant les lignes (Y)
    line_length = 10 # Longueur de la ligne horizontale
    
    for i in range(N):
        # Changement ici : c_offset bouge vite, r_offset bouge doucement
        c_offset = (i % line_length) * 2  # S'étend horizontalement
        r_offset = (i // line_length) * 2 # S'empile verticalement
        
        u = unit_class() 
        # On centre verticalement avec center_row
        game.add_unit(u, "A", center_row - 2 + r_offset, start_col_A + c_offset)

    # 5. Placement Équipe B (2*N unités) - Droite
    # Position de départ très à droite (colonne 90)
    start_col_B = cols - 5
    count_B = 2 * N
    
    for i in range(count_B):
        c_offset = (i % line_length) * 2
        r_offset = (i // line_length) * 2
        
        u = unit_class()
        # Pour B, on recule vers la gauche (start_col - c_offset)
        game.add_unit(u, "B", center_row - 2 + r_offset, start_col_B - c_offset)

    print(f"⚔️ Scénario Lanchester (Horizontal) : {N} vs {2*N} sur map {rows}x{cols}")
    return game
