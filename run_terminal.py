from views.terminal_view import TerminalView

from scenarios import scenario_lanchester

if __name__ == "__main__":
    # 1. Créer le jeu
    game = scenario_lanchester("knight",50)
    
    # 2. Créer la vue
    view = TerminalView(game)
    
    # 3. Lancer !
    view.start()