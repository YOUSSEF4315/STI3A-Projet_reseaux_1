#!/usr/bin/env python3
"""
Lancement du jeu pour le Joueur 2.
Utilise le port IPC 50002 (daemon Joueur 2).
"""
import os

# Configurer avant tout import du jeu
os.environ["P2P_PORT"]      = "50002"
os.environ["P2P_PLAYER_ID"] = "B"

# Lancer le menu normalement
import sys
# On ajoute le répertoire courant si besoin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from launch import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
