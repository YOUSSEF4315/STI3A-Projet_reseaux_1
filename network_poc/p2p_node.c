#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>

#define BUFFER_SIZE 2048

void run_server(int port) {
    int server_fd, new_socket;
    struct sockaddr_in address;
    int opt = 1;
    int addrlen = sizeof(address);
    char buffer[BUFFER_SIZE] = {0};

    printf("[Serveur] Démarrage de l'hôte C sur le port %d...\n", port);

    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        perror("Socket failed");
        exit(EXIT_FAILURE);
    }

    // Permet de relancer rapidement le serveur sur le même port si plantage
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt))) {
        perror("setsockopt");
        exit(EXIT_FAILURE);
    }

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY; // Écoute sur toutes les interfaces réseau (locales et distantes)
    address.sin_port = htons(port);

    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("Bind failed");
        exit(EXIT_FAILURE);
    }

    if (listen(server_fd, 3) < 0) {
        perror("Listen failed");
        exit(EXIT_FAILURE);
    }

    printf("[Serveur] En attente de la connexion d'un autre joueur (P2P)...\n");
    // Acceptation bloquante jusqu'à ce qu'un client s'y connecte
    if ((new_socket = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen)) < 0) {
        perror("Accept failed");
        exit(EXIT_FAILURE);
    }

    printf("[Serveur] L'autre joueur est connecté !\n");

    // Exemple de communication : Le serveur a l'initiative
    const char *hello = "{\"action\": \"handshake\", \"role\": \"host\"}\n";
    send(new_socket, hello, strlen(hello), 0);
    printf("[Serveur] Message de bienvenue envoyé au client.\n");

    // On attend la réponse du client
    int valread = read(new_socket, buffer, BUFFER_SIZE - 1);
    if (valread > 0) {
        buffer[valread] = '\0';
        printf("[Serveur] Reçu du client : %s", buffer);
    }

    close(new_socket);
    close(server_fd);
    printf("[Serveur] Connexion terminée.\n");
}

void run_client(const char* ip, int port) {
    int sock = 0;
    struct sockaddr_in serv_addr;
    char buffer[BUFFER_SIZE] = {0};

    printf("[Client] Démarrage... Tentative de connexion à %s:%d\n", ip, port);

    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        printf("[Client] Erreur de création du socket\n");
        return;
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(port);

    // Conversion IP textuelle (ex: "192.168.1.50") en format réseau binaire
    if (inet_pton(AF_INET, ip, &serv_addr.sin_addr) <= 0) {
        printf("[Client] Adresse IP invalide : %s\n", ip);
        return;
    }

    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        printf("[Client] La connexion a échoué. Assurez-vous que l'IP et le port sont bons et que le serveur C est lancé.\n");
        return;
    }

    printf("[Client] Connecté au joueur hébergeur !\n");

    // On attend la réception des données du serveur
    int valread = read(sock, buffer, BUFFER_SIZE - 1);
    if (valread > 0) {
        buffer[valread] = '\0';
        printf("[Client] Reçu de l'hôte : %s", buffer);

        // Réponse au serveur
        const char *response_json = "{\"action\": \"handshake\", \"role\": \"client\"}\n";
        printf("[Client] Envoi de confirmation : %s", response_json);
        send(sock, response_json, strlen(response_json), 0);
    }

    close(sock);
    printf("[Client] Connexion terminée.\n");
}

int main(int argc, char const *argv[]) {
    // Aide à l'utilisation
    if (argc < 2) {
        printf("--- MedievAIl - Communication Réseau C (P2P) ---\n\n");
        printf("Usage:\n");
        printf("  Mode Serveur (Héberger) : ./p2p_node --host <port>\n");
        printf("  Mode Client (Rejoindre) : ./p2p_node --connect <IP_DISTANTE> <port>\n");
        printf("\nExemple pour jouer avec un ami en LAN:\n");
        printf("  L'ami lance   : ./p2p_node --host 5000\n");
        printf("  Vous lancez   : ./p2p_node --connect 192.168.x.x 5000\n");
        return 1;
    }

    // Traitement des arguments
    if (strcmp(argv[1], "--host") == 0) {
        int port = (argc >= 3) ? atoi(argv[2]) : 5000;
        run_server(port);
    } 
    else if (strcmp(argv[1], "--connect") == 0) {
        if (argc < 4) {
            printf("Erreur: arguments manquants.\nUsage: ./p2p_node --connect <IP> <port>\n");
            return 1;
        }
        const char* ip = argv[2];
        int port = atoi(argv[3]);
        run_client(ip, port);
    } 
    else {
        printf("Option %s non reconnue. Utilisez --host ou --connect.\n", argv[1]);
    }

    return 0;
}
