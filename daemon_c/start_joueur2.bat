@echo off
title JOUEUR 2 - Daemon P2P
echo ==========================================
echo  JOUEUR 2 : Daemon P2P (Client)
echo  Python port : 50002
echo  Reseau port : 50003
echo  Connexion vers Joueur 1 sur 127.0.0.1:50001
echo ==========================================
echo.
daemon.exe 50002 50003 127.0.0.1 50001
pause
