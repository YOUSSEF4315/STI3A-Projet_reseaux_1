@echo off
echo Compilation du Daemon C - Routeur P2P (Mode TCP)
SET GCC_PATH=C:\msys64\ucrt64\bin\gcc.exe
IF NOT EXIST "%GCC_PATH%" SET GCC_PATH=gcc

"%GCC_PATH%" main.c -lws2_32 -o daemon.exe
if %ERRORLEVEL% EQU 0 (
    echo [OK] Compilation reussie ! daemon.exe cree.
    echo.
    echo Usage:
    echo   daemon.exe              (mode Serveur - attend une connexion)
    echo   daemon.exe 192.168.1.X  (mode Client - rejoint un adversaire)
) else (
    echo [ERREUR] Compilation echouee.
    echo Verifiez que GCC est installe via MSYS2: pacman -S mingw-w64-ucrt-x86_64-gcc
)
pause
