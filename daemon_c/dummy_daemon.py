import socket
import json

HOST = '127.0.0.1'
PORT = 50000

print(f"[Dummy Daemon] En attente de connexion sur {HOST}:{PORT} (Mode TCP)...")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    # Désactivation de l'algo Nagle (similaire au code C)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    s.bind((HOST, PORT))
    s.listen()
    
    while True:
        conn, addr = s.accept()
        with conn:
            print(f"\n[Dummy Daemon] Application Python connectée depuis {addr} !")
            buffer = ""
            while True:
                data = conn.recv(4096)
                if not data:
                    print("[Dummy Daemon] Connexion fermée par le Python.")
                    break
                    
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        print(f"\n--- REÇU DE PYTHON ---\n{line}\n----------------------")
                        # Réponse (ACK)
                        ack_msg = '{"type": "ACK", "status": "Message bien recu par le Daemon de Substitution"}\n'
                        conn.sendall(ack_msg.encode('utf-8'))
