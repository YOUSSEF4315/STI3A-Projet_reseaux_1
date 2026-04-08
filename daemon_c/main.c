#define _WIN32_WINNT 0x0600
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>

#pragma comment(lib, "ws2_32.lib")

#define PORT_LOCAL 50000     // Pour parler au Python local
#define PORT_RESEAU 50001    // Pour écouter d'autres joueurs
#define BUFFER_SIZE 8192

// Fonction pour configurer un socket non bloquant
void set_nonblocking(SOCKET s) {
    u_long mode = 1;
    ioctlsocket(s, FIONBIO, &mode);
}

// Désactive l'algorithme de Nagle (pour la réactivité temps réel)
void set_tcp_nodelay(SOCKET s) {
    int flag = 1;
    setsockopt(s, IPPROTO_TCP, TCP_NODELAY, (char*)&flag, sizeof(int));
}

int main(int argc, char* argv[]) {
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("Erreur d'initialisation Winsock.\n");
        return 1;
    }

    SOCKET py_listener = INVALID_SOCKET;
    SOCKET net_listener = INVALID_SOCKET;
    
    SOCKET py_client = INVALID_SOCKET;
    SOCKET net_client = INVALID_SOCKET; // L'adversaire distant
    
    // 1. Démarrer l'écoute Locale (Python)
    py_listener = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    struct sockaddr_in py_addr;
    py_addr.sin_family = AF_INET;
    py_addr.sin_addr.s_addr = inet_addr("127.0.0.1"); // Sécurisé: que du localhost
    py_addr.sin_port = htons(PORT_LOCAL);
    bind(py_listener, (struct sockaddr*)&py_addr, sizeof(py_addr));
    listen(py_listener, SOMAXCONN);
    set_nonblocking(py_listener);
    
    // 2. Démarrer l'écoute Réseau (Adversaires)
    net_listener = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    struct sockaddr_in net_addr;
    net_addr.sin_family = AF_INET;
    net_addr.sin_addr.s_addr = INADDR_ANY; // Ouvert sur toutes les IP locales/publiques
    net_addr.sin_port = htons(PORT_RESEAU);
    bind(net_listener, (struct sockaddr*)&net_addr, sizeof(net_addr));
    listen(net_listener, SOMAXCONN);
    set_nonblocking(net_listener);

    printf("[Daemon C] Lancement du Routeur P2P Best-Effort !\n");
    printf(" -> Ecoute Locale Python sur le port %d\n", PORT_LOCAL);
    printf(" -> Ecoute Reseau Distant sur le port %d\n", PORT_RESEAU);

    // 3. Cas Client : on veut rejoindre la partie de quelqu'un d'autre
    if (argc >= 2) {
        const char* target_ip = argv[1];
        printf("[Daemon C] Tentative de connexion a %s:%d ...\n", target_ip, PORT_RESEAU);
        
        net_client = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        struct sockaddr_in target_addr;
        target_addr.sin_family = AF_INET;
        target_addr.sin_addr.s_addr = inet_addr(target_ip);
        target_addr.sin_port = htons(PORT_RESEAU);
        
        // Bloquant pendant la connexion pour simplifier
        if (connect(net_client, (struct sockaddr*)&target_addr, sizeof(target_addr)) != SOCKET_ERROR) {
            printf("[Daemon C] -> Connecte avec succes au reseau P2P adversaire !\n");
            set_nonblocking(net_client);
            set_tcp_nodelay(net_client);
        } else {
            printf("[Daemon C] Erreur: impossible de joindre %s\n", target_ip);
            closesocket(net_client);
            net_client = INVALID_SOCKET;
        }
    }

    char buffer[BUFFER_SIZE];
    fd_set readfds;

    // Boucle Principale de Routage (Select)
    while (1) {
        FD_ZERO(&readfds);
        FD_SET(py_listener, &readfds);
        FD_SET(net_listener, &readfds);
        
        if (py_client != INVALID_SOCKET) FD_SET(py_client, &readfds);
        if (net_client != INVALID_SOCKET) FD_SET(net_client, &readfds);
        
        // Timeout de sécurité pour éviter de freezer si problème Windows
        struct timeval timeout;
        timeout.tv_sec = 1;
        timeout.tv_usec = 0;

        int activity = select(0, &readfds, NULL, NULL, &timeout);
        
        if (activity == SOCKET_ERROR) {
            printf("Erreur select()\n");
            break;
        }

        if (activity == 0) continue; // Timeout (Silence réseau)

        // A. Nouvelle Connexion d'un Python Local
        if (FD_ISSET(py_listener, &readfds)) {
            SOCKET client = accept(py_listener, NULL, NULL);
            if (client != INVALID_SOCKET) {
                if (py_client != INVALID_SOCKET) closesocket(py_client); // Tolère 1 seul python
                py_client = client;
                set_nonblocking(py_client);
                set_tcp_nodelay(py_client);
                printf("[Daemon C] -> Python Local CONNECTE.\n");
            }
        }

        // B. Nouvelle Connexion d'un Adversaire Distant
        if (FD_ISSET(net_listener, &readfds)) {
            SOCKET client = accept(net_listener, NULL, NULL);
            if (client != INVALID_SOCKET) {
                if (net_client != INVALID_SOCKET) closesocket(net_client); // Tolère 1 seul adversaire pour le moment
                net_client = client;
                set_nonblocking(net_client);
                set_tcp_nodelay(net_client);
                printf("[Daemon C] -> Adversaire Distant CONNECTE !\n");
            }
        }

        // C. Réception de données depuis Python Local -> Routage vers Distant
        if (py_client != INVALID_SOCKET && FD_ISSET(py_client, &readfds)) {
            memset(buffer, 0, BUFFER_SIZE);
            int valread = recv(py_client, buffer, BUFFER_SIZE - 1, 0);
            if (valread > 0) {
                // Pour débug : printf("[Python] -> [Distant] %d bytes\n", valread);
                // Si on a un adversaire connecté, on forwarde tout brutalement.
                if (net_client != INVALID_SOCKET) {
                    send(net_client, buffer, valread, 0);
                }
            } else if (valread == 0 || (valread == SOCKET_ERROR && WSAGetLastError() != WSAEWOULDBLOCK)) {
                printf("[Daemon C] Python Local s'est deconnecte.\n");
                closesocket(py_client);
                py_client = INVALID_SOCKET;
            }
        }

        // D. Réception de données depuis Adversaire Distant -> Routage vers Local Python
        if (net_client != INVALID_SOCKET && FD_ISSET(net_client, &readfds)) {
            memset(buffer, 0, BUFFER_SIZE);
            int valread = recv(net_client, buffer, BUFFER_SIZE - 1, 0);
            if (valread > 0) {
                // Pour débug : printf("[Distant] -> [Python] %d bytes\n", valread);
                // On transfère le JSON à notre instance locale du jeu.
                if (py_client != INVALID_SOCKET) {
                    send(py_client, buffer, valread, 0);
                }
            } else if (valread == 0 || (valread == SOCKET_ERROR && WSAGetLastError() != WSAEWOULDBLOCK)) {
                printf("[Daemon C] Adversaire Distant s'est deconnecte.\n");
                closesocket(net_client);
                net_client = INVALID_SOCKET;
            }
        }
    }

    // Libération des ressources (Normalement inaccessible sans Ctrl+C)
    if (py_client != INVALID_SOCKET) closesocket(py_client);
    if (net_client != INVALID_SOCKET) closesocket(net_client);
    closesocket(py_listener);
    closesocket(net_listener);
    WSACleanup();

    return 0;
}
