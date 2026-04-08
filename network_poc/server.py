import socket
import json
import time

HOST = '127.0.0.1'
PORT = 5000

def run_server():
    print(f"[*] Démarrage du serveur Python sur {HOST}:{PORT}")
    
    # Création du socket TCP
    # AF_INET = IPv4, SOCK_STREAM = TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Permet de réutiliser le port immédiatement après la fermeture
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server_socket.bind((HOST, PORT))
    server_socket.listen(1) # Attente d'une connexion
    
    print("[*] En attente d'une connexion du programme C...")
    conn, addr = server_socket.accept()
    print(f"[+] Connexion acceptée depuis {addr}")
    
    try:
        # Faux GameState pour la preuve de concept
        fake_state = {
            "game_time": 10.5,
            "running": True,
            "units": [
                {"id": "u1", "type": "Knight", "hp": 100, "x": 10.0, "y": 20.0},
                {"id": "u2", "type": "Pikeman", "hp": 50, "x": 15.0, "y": 25.0}
            ]
        }
        
        # Sérialisation en JSON
        message_str = json.dumps(fake_state)
        
        # Protocole basique : on envoie le JSON suivi d'un délimiteur (\n)
        print(f"[*] Envoi de l'état au client: {message_str}")
        conn.sendall((message_str + "\n").encode('utf-8'))
        
        # Réception de la réponse du C
        print("[*] En attente de la réponse du client...")
        data = conn.recv(1024)
        if data:
            reponse_str = data.decode('utf-8').strip()
            print(f"[+] Réponse reçue du client : {reponse_str}")
            
            # Essayer de parser le JSON reçu
            try:
                reponse_json = json.loads(reponse_str)
                print(f"[+] Python a compris l'action demandée : {reponse_json.get('action')} sur la cible {reponse_json.get('target')}")
            except json.JSONDecodeError:
                print("[-] Le message reçu n'est pas un JSON valide.")
        else:
            print("[-] Le client a fermé la connexion avant de répondre.")
            
    except Exception as e:
        print(f"[-] Erreur : {e}")
    finally:
        print("[*] Fermeture de la connexion.")
        conn.close()
        server_socket.close()

if __name__ == "__main__":
    run_server()
