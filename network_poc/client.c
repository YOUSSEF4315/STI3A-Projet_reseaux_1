#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define SERVER_IP "127.0.0.1"
#define PORT 5000
#define BUFFER_SIZE 2048

int main() {
    int sock = 0;
    struct sockaddr_in serv_addr;
    char buffer[BUFFER_SIZE] = {0};
    
    printf("[C] Démarrage du client...\n");

    // 1. Création du socket (IPv4, TCP)
    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        printf("[C] Erreur: impossible de créer le socket\n");
        return -1;
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);

    // 2. Conversion de l'adresse IP en binaire binaire exploitable par le réseau
    if (inet_pton(AF_INET, SERVER_IP, &serv_addr.sin_addr) <= 0) {
        printf("[C] Erreur: Adresse IP invalide ou non supportée\n");
        return -1;
    }

    // 3. Connexion au serveur Python
    printf("[C] Tentative de connexion à %s:%d...\n", SERVER_IP, PORT);
    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        printf("[C] Erreur: Connexion échouée. Assurez-vous que le script Python tourne bien.\n");
        return -1;
    }
    printf("[C] Connecté avec succès au serveur Python !\n");

    // 4. Lecture des données envoyées par Python (Le GameState en JSON)
    int valread = read(sock, buffer, BUFFER_SIZE - 1);
    if (valread > 0) {
        buffer[valread] = '\0';
        printf("[C] Reçu du serveur : %s", buffer); // Le texte retourné par python contient déjà \n
        
        // --- LOGIQUE EN C ICI ---
        // Vrai projet: Utiliser cJSON ou jansson pour parser la chaîne 'buffer'
        printf("[C] Analyse (fictive) de l'état du jeu...\n");
        sleep(1); // Simuler une réflexion de l'IA (1 seconde)
        
        // 5. Formulation et envoi d'une réponse en JSON
        // On renvoie un JSON basique pour prouver la communication bidirectionnelle
        const char *response_json = "{\"action\": \"attack\", \"target\": \"u2\"}\n";
        
        printf("[C] Envoi de l'action JSON au serveur : %s", response_json);
        send(sock, response_json, strlen(response_json), 0);
        printf("[C] Message envoyé avec succès.\n");
    } else {
        printf("[C] Erreur lors de la lecture des données ou connexion fermée par le serveur.\n");
    }

    // 6. Fermeture
    close(sock);
    printf("[C] Connexion fermée.\n");
    return 0;
}
