#define _WIN32_WINNT 0x0600
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>

#pragma comment(lib, "ws2_32.lib")

#define BUFFER_SIZE 8192

void set_nonblocking(SOCKET s) {
    u_long mode = 1;
    ioctlsocket(s, FIONBIO, &mode);
}

void set_tcp_nodelay(SOCKET s) {
    int flag = 1;
    setsockopt(s, IPPROTO_TCP, TCP_NODELAY, (char*)&flag, sizeof(int));
}

int main(int argc, char* argv[]) {
    // Usage:
    //   daemon.exe                              -> Joueur 1 (py=50000, net=50001, attend)
    //   daemon.exe <peer_ip>                    -> Joueur 2 (py=50000, net=50001, rejoint peer)
    //   daemon.exe <py_port> <net_port>         -> Joueur 1 avec ports custom
    //   daemon.exe <py_port> <net_port> <peer_ip> <peer_port>  -> Joueur 2 avec ports custom

    int PORT_LOCAL  = 50000;
    int PORT_RESEAU = 50001;
    char peer_ip[64] = "";
    int  peer_port    = 50001;

    if (argc == 2) {
        // daemon.exe <peer_ip>  → rejoindre Joueur 1 sur son port réseau par défaut
        strncpy(peer_ip, argv[1], sizeof(peer_ip) - 1);
    } else if (argc == 3) {
        // daemon.exe <py_port> <net_port>
        PORT_LOCAL  = atoi(argv[1]);
        PORT_RESEAU = atoi(argv[2]);
    } else if (argc == 5) {
        // daemon.exe <py_port> <net_port> <peer_ip> <peer_port>
        PORT_LOCAL  = atoi(argv[1]);
        PORT_RESEAU = atoi(argv[2]);
        strncpy(peer_ip, argv[3], sizeof(peer_ip) - 1);
        peer_port   = atoi(argv[4]);
    }

    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        printf("Erreur Winsock.\n");
        return 1;
    }

    SOCKET py_listener  = INVALID_SOCKET;
    SOCKET net_listener = INVALID_SOCKET;
    SOCKET py_client    = INVALID_SOCKET;
    SOCKET net_client   = INVALID_SOCKET;

    // --- Écoute Python local ---
    py_listener = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    int opt = 1;
    setsockopt(py_listener, SOL_SOCKET, SO_REUSEADDR, (char*)&opt, sizeof(opt));
    struct sockaddr_in py_addr;
    py_addr.sin_family      = AF_INET;
    py_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
    py_addr.sin_port        = htons(PORT_LOCAL);
    if (bind(py_listener, (struct sockaddr*)&py_addr, sizeof(py_addr)) == SOCKET_ERROR) {
        printf("[Daemon C] ERREUR: port %d deja utilise ! (code %d)\n", PORT_LOCAL, WSAGetLastError());
        WSACleanup();
        return 1;
    }
    listen(py_listener, SOMAXCONN);
    set_nonblocking(py_listener);

    // --- Écoute réseau P2P ---
    net_listener = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    setsockopt(net_listener, SOL_SOCKET, SO_REUSEADDR, (char*)&opt, sizeof(opt));
    struct sockaddr_in net_addr;
    net_addr.sin_family      = AF_INET;
    net_addr.sin_addr.s_addr = INADDR_ANY;
    net_addr.sin_port        = htons(PORT_RESEAU);
    if (bind(net_listener, (struct sockaddr*)&net_addr, sizeof(net_addr)) == SOCKET_ERROR) {
        printf("[Daemon C] ERREUR: port reseau %d deja utilise ! (code %d)\n", PORT_RESEAU, WSAGetLastError());
        WSACleanup();
        return 1;
    }
    listen(net_listener, SOMAXCONN);
    set_nonblocking(net_listener);

    printf("========================================\n");
    printf("[Daemon C] Routeur P2P Best-Effort\n");
    printf(" -> Python local : port %d\n", PORT_LOCAL);
    printf(" -> Reseau P2P   : port %d\n", PORT_RESEAU);

    // --- Mode client : connexion vers un pair ---
    if (strlen(peer_ip) > 0) {
        printf(" -> Connexion vers %s:%d ...\n", peer_ip, peer_port);
        net_client = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        struct sockaddr_in target;
        target.sin_family      = AF_INET;
        target.sin_addr.s_addr = inet_addr(peer_ip);
        target.sin_port        = htons(peer_port);
        if (connect(net_client, (struct sockaddr*)&target, sizeof(target)) != SOCKET_ERROR) {
            printf(" -> Connecte au pair P2P !\n");
            set_nonblocking(net_client);
            set_tcp_nodelay(net_client);
        } else {
            printf(" -> Echec connexion (code %d)\n", WSAGetLastError());
            closesocket(net_client);
            net_client = INVALID_SOCKET;
        }
    }
    printf("========================================\n");
    printf("En attente de connexions...\n\n");

    char buffer[BUFFER_SIZE];
    fd_set readfds;

    while (1) {
        FD_ZERO(&readfds);
        FD_SET(py_listener, &readfds);
        FD_SET(net_listener, &readfds);
        if (py_client  != INVALID_SOCKET) FD_SET(py_client,  &readfds);
        if (net_client != INVALID_SOCKET) FD_SET(net_client, &readfds);

        struct timeval timeout = {1, 0};
        int activity = select(0, &readfds, NULL, NULL, &timeout);
        if (activity == SOCKET_ERROR) { printf("Erreur select()\n"); break; }
        if (activity == 0) continue;

        // A. Nouveau Python local
        if (FD_ISSET(py_listener, &readfds)) {
            SOCKET c = accept(py_listener, NULL, NULL);
            if (c != INVALID_SOCKET) {
                if (py_client != INVALID_SOCKET) closesocket(py_client);
                py_client = c;
                set_nonblocking(py_client);
                set_tcp_nodelay(py_client);
                printf("[Daemon C] Python local connecte (port %d)\n", PORT_LOCAL);
            }
        }

        // B. Nouveau pair P2P entrant
        if (FD_ISSET(net_listener, &readfds)) {
            SOCKET c = accept(net_listener, NULL, NULL);
            if (c != INVALID_SOCKET) {
                if (net_client != INVALID_SOCKET) closesocket(net_client);
                net_client = c;
                set_nonblocking(net_client);
                set_tcp_nodelay(net_client);
                printf("[Daemon C] Adversaire P2P connecte (port %d)\n", PORT_RESEAU);
            }
        }

        // C. Python -> Reseau
        if (py_client != INVALID_SOCKET && FD_ISSET(py_client, &readfds)) {
            memset(buffer, 0, BUFFER_SIZE);
            int n = recv(py_client, buffer, BUFFER_SIZE - 1, 0);
            if (n > 0) {
                if (net_client != INVALID_SOCKET) send(net_client, buffer, n, 0);
            } else if (n == 0 || WSAGetLastError() != WSAEWOULDBLOCK) {
                printf("[Daemon C] Python local deconnecte.\n");
                closesocket(py_client); py_client = INVALID_SOCKET;
            }
        }

        // D. Reseau -> Python
        if (net_client != INVALID_SOCKET && FD_ISSET(net_client, &readfds)) {
            memset(buffer, 0, BUFFER_SIZE);
            int n = recv(net_client, buffer, BUFFER_SIZE - 1, 0);
            if (n > 0) {
                if (py_client != INVALID_SOCKET) send(py_client, buffer, n, 0);
            } else if (n == 0 || WSAGetLastError() != WSAEWOULDBLOCK) {
                printf("[Daemon C] Pair P2P deconnecte.\n");
                closesocket(net_client); net_client = INVALID_SOCKET;
            }
        }
    }

    if (py_client  != INVALID_SOCKET) closesocket(py_client);
    if (net_client != INVALID_SOCKET) closesocket(net_client);
    closesocket(py_listener);
    closesocket(net_listener);
    WSACleanup();
    return 0;
}
