"""
Script de lancement rapide pour le Joueur 2 (port IPC = 50002).
Configure la variable d'environnement P2P_PORT avant de lancer le jeu.
"""
import os
import sys

# Indiquer au jeu quel port IPC utiliser (celui du daemon Joueur 2)
os.environ["P2P_PORT"] = "50002"
os.environ["P2P_PLAYER_ID"] = "B"

# Lancer le launcher normal
import launch
