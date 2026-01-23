#!/usr/bin/env python3
"""
battle.py - CLI Entry Point for MedievAIl Battle Simulator

Usage:
    battle run <scenario> <AI1> <AI2> [-t] [-d DATAFILE]
    battle load <savefile>
    battle tourney [-G AI1 AI2...] [-S SCENARIO1 SCENARIO2] [-N=10] [-na]
    battle plot <AI> <plotter> <scenario(arg1,...)> <range> [-N=10]
"""

import argparse
import pickle
import sys
import os

# --- IMPORTS ---
from game import Game
from map import BattleMap
from ai import CaptainBraindead, MajorDaft, AssasinJack, PredictEinstein
from smartAI import GeneralStrategus
from scenarios import (
    scenario_simple_vs_braindead,
    scenario_small_terminal,
    scenario_lanchester,
)

# --- REGISTRES ---
AVAILABLE_AIS = {
    "Braindead": CaptainBraindead,
    "Daft": MajorDaft,
    "GeneralStrategus": GeneralStrategus,
    "AssasinJack": AssasinJack,
    "PredictEinstein": PredictEinstein,
}

AVAILABLE_SCENARIOS = {
    "Scenario_Standard": scenario_small_terminal,
    "Scenario_Dur": scenario_simple_vs_braindead,
}


def run_battle(scenario_name, ai1_name, ai2_name, terminal_mode=False, datafile=None, savefile=None):
    """
    Exécute une bataille entre deux IA sur un scénario donné.
    """
    # 1. Création du scénario de base (pour récupérer la map)
    if scenario_name in AVAILABLE_SCENARIOS:
        base_game = AVAILABLE_SCENARIOS[scenario_name]()
    else:
        # Permet d'utiliser eval() pour des scénarios avec paramètres
        try:
            base_game = eval(scenario_name)
        except Exception as e:
            print(f"Erreur : Scénario '{scenario_name}' inconnu ou invalide. {e}")
            return None

    # 2. Remplacer les contrôleurs par les IA demandées
    if ai1_name not in AVAILABLE_AIS:
        print(f"Erreur : IA '{ai1_name}' inconnue. Disponibles : {list(AVAILABLE_AIS.keys())}")
        return None
    if ai2_name not in AVAILABLE_AIS:
        print(f"Erreur : IA '{ai2_name}' inconnue. Disponibles : {list(AVAILABLE_AIS.keys())}")
        return None

    # On recrée le game avec les bonnes IA
    controllers = {
        "A": AVAILABLE_AIS[ai1_name]("A"),
        "B": AVAILABLE_AIS[ai2_name]("B"),
    }
    base_game.controllers = controllers

    # 3. Lancer la simulation
    if terminal_mode:
        # Mode Terminal (curses)
        from views.terminal_view import TerminalView
        view = TerminalView(base_game)
        view.start()
    else:
        # Mode GUI (pygame)
        import pygame
        from views.views import GUI

        pygame.init()
        screen = pygame.display.set_mode((1024, 768), pygame.RESIZABLE)
        pygame.display.set_caption(f"Battle: {ai1_name} vs {ai2_name}")
        clock = pygame.time.Clock()
        gui = GUI(base_game, 1024, 768)

        auto_play = True
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                gui.handle_events(event)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        auto_play = not auto_play
                    if event.key == pygame.K_SPACE:
                        base_game.step(dt=0.1)
                    if event.key == pygame.K_F9:
                        # Switch to terminal mode
                        pygame.quit()
                        from views.terminal_view import TerminalView
                        view = TerminalView(base_game)
                        view.start()
                        return base_game

            if not base_game.is_finished() and auto_play:
                base_game.step(dt=0.1)

            gui.handle_input()
            gui.draw(screen)
            pygame.display.flip()
            clock.tick(60)

            if base_game.is_finished():
                # Attendre un peu avant de quitter
                pygame.time.wait(2000)
                running = False

        pygame.quit()

    # 4. Écriture des données si demandé
    if datafile:
        summary = base_game.get_battle_summary()
        with open(datafile, "w", encoding="utf-8") as f:
            f.write(str(summary))
        print(f"Données écrites dans {datafile}")

    # 5. Sauvegarde de l'état complet si demandé
    if savefile:
        with open(savefile, "wb") as f:
            pickle.dump(base_game, f)
        print(f"État du jeu sauvegardé dans {savefile}")

    return base_game


def load_game(savefile):
    """Charge une partie sauvegardée."""
    if not os.path.exists(savefile):
        print(f"Erreur : Fichier '{savefile}' introuvable.")
        return

    with open(savefile, "rb") as f:
        game = pickle.load(f)

    print(f"Partie chargée depuis {savefile}")
    print(f"Temps simulé : {game.time:.1f}s, Unités en vie : {len(game.alive_units())}")

    # Lancer en mode GUI
    import pygame
    from views.views import GUI

    pygame.init()
    screen = pygame.display.set_mode((1024, 768), pygame.RESIZABLE)
    pygame.display.set_caption("Partie chargée")
    clock = pygame.time.Clock()
    gui = GUI(game, 1024, 768)

    auto_play = False
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            gui.handle_events(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    auto_play = not auto_play

        if not game.is_finished() and auto_play:
            game.step(dt=0.1)

        gui.handle_input()
        gui.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def run_tournament(generals, scenarios, rounds=10, alternate=True):
    """
    Lance un tournoi complet entre les généraux spécifiés.
    """
    from tournament import Tournament

    if not generals:
        generals = list(AVAILABLE_AIS.keys())
    if not scenarios:
        scenarios = list(AVAILABLE_SCENARIOS.keys())

    print(f"\n{'='*50}")
    print(f"TOURNOI AUTOMATIQUE")
    print(f"Généraux : {generals}")
    print(f"Scénarios : {scenarios}")
    print(f"Rounds par matchup : {rounds}")
    print(f"Alternance des positions : {alternate}")
    print(f"{'='*50}\n")

    t = Tournament(generals, scenarios, rounds=rounds)
    t.run()


def run_plot(ai_name, plotter_name, scenario_expr, range_expr, rounds=10):
    """
    Génère des graphiques basés sur les lois de Lanchester.
    """
    import matplotlib.pyplot as plt
    from collections import defaultdict

    # Parse le range
    try:
        values = eval(range_expr)
    except Exception as e:
        print(f"Erreur évaluation range : {e}")
        return

    # Parse les types d'unités
    try:
        # scenario_expr format: "Lanchester [Knight,Crossbow]" or just unit types
        if "[" in scenario_expr:
            unit_types = eval(scenario_expr.split("[")[1].rstrip("]"))
        else:
            unit_types = ["knight"]
    except:
        unit_types = ["knight"]

    print(f"\n{'='*50}")
    print(f"PLOT LANCHESTER")
    print(f"IA : {ai_name}")
    print(f"Types : {unit_types}")
    print(f"Range N : {list(values)}")
    print(f"{'='*50}\n")

    # Données à collecter
    data = defaultdict(list)

    for unit_type in unit_types:
        for N in values:
            print(f"Test {unit_type} N={N}...", end=" ")

            # Créer le scénario Lanchester
            game = scenario_lanchester(unit_type.lower(), N)

            # Simuler jusqu'à la fin
            while not game.is_finished() and game.time < 300:
                game.step(dt=0.2)

            summary = game.get_battle_summary()
            
            # Pertes du côté victorieux (équipe avec 2N = B)
            losses_B = summary["losses"].get("B", {}).get("units", 0)
            
            data[unit_type].append((N, losses_B))
            print(f"Pertes B (2N) = {losses_B}")

    # Générer le graphique
    plt.figure(figsize=(10, 6))
    for unit_type, points in data.items():
        Ns = [p[0] for p in points]
        losses = [p[1] for p in points]
        plt.plot(Ns, losses, marker='o', label=unit_type.capitalize())

    plt.xlabel("N (taille armée A)")
    plt.ylabel("Pertes de l'armée B (2N)")
    plt.title("Lois de Lanchester - Pertes en fonction de N")
    plt.legend()
    plt.grid(True)
    plt.savefig("lanchester_plot.png", dpi=150)
    plt.show()
    print("\nGraphique sauvé dans lanchester_plot.png")


def main():
    parser = argparse.ArgumentParser(
        prog="battle",
        description="MedievAIl Battle Simulator - CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  battle run Scenario_Standard Daft Braindead -t
  battle run Scenario_Dur Daft GeneralStrategus -s final_state.pkl
  battle load quicksave.pkl
  battle tourney -G Daft Braindead GeneralStrategus -N 5
  battle plot Daft Lanchester "Lanchester [knight,crossbowman]" "range(1,20)"
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")

    # --- RUN ---
    run_parser = subparsers.add_parser("run", help="Lancer une bataille")
    run_parser.add_argument("scenario", help="Nom du scénario")
    run_parser.add_argument("ai1", help="IA du joueur A")
    run_parser.add_argument("ai2", help="IA du joueur B")
    run_parser.add_argument("-t", "--terminal", action="store_true", help="Mode terminal")
    run_parser.add_argument("-d", "--datafile", help="Fichier de données de sortie (résumé texte)")
    run_parser.add_argument("-s", "--savefile", help="Fichier de sauvegarde (.pkl) pour l'état complet")

    # --- LOAD ---
    load_parser = subparsers.add_parser("load", help="Charger une sauvegarde")
    load_parser.add_argument("savefile", help="Fichier de sauvegarde (.pkl)")

    # --- TOURNEY ---
    tourney_parser = subparsers.add_parser("tourney", help="Lancer un tournoi")
    tourney_parser.add_argument("-G", "--generals", nargs="+", help="Liste des IA")
    tourney_parser.add_argument("-S", "--scenarios", nargs="+", help="Liste des scénarios")
    tourney_parser.add_argument("-N", "--rounds", type=int, default=10, help="Rounds par matchup")
    tourney_parser.add_argument("-na", "--no-alternate", action="store_true", help="Ne pas alterner les positions")

    # --- PLOT ---
    plot_parser = subparsers.add_parser("plot", help="Générer un graphique Lanchester")
    plot_parser.add_argument("ai", help="IA à utiliser")
    plot_parser.add_argument("plotter", help="Type de graphique (ex: Lanchester)")
    plot_parser.add_argument("scenario", help="Expression du scénario")
    plot_parser.add_argument("range", help="Range des valeurs (ex: range(1,20))")
    plot_parser.add_argument("-N", "--rounds", type=int, default=10, help="Répétitions")

    args = parser.parse_args()

    if args.command == "run":
        run_battle(args.scenario, args.ai1, args.ai2, args.terminal, args.datafile, args.savefile)

    elif args.command == "load":
        load_game(args.savefile)

    elif args.command == "tourney":
        run_tournament(
            args.generals,
            args.scenarios,
            args.rounds,
            not args.no_alternate
        )

    elif args.command == "plot":
        run_plot(args.ai, args.plotter, args.scenario, args.range, args.rounds)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
