@echo off
title JOUEUR 1 - Daemon P2P
echo ==========================================
echo  JOUEUR 1 : Daemon P2P (Serveur)
echo  Python port : 50000
echo  Reseau port : 50001
echo ==========================================
echo Attendez que le Joueur 2 se connecte...
echo.
daemon.exe 50000 50001
pause
