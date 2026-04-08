# ipc_client.py
"""
Couche réseau Python interne (IPC) mise à jour pour utiliser TCP.
Responsable de communiquer localement avec le daemon C.
Un thread tourne en boucle pour recevoir les messages asynchrones du C
sans bloquer l'affichage ou le moteur de jeu.
"""
import json
import socket
import logging
import threading
from queue import Queue, Empty
import traceback

class IPCClient:
    def __init__(self, host="127.0.0.1", port=50000, local_id="A"):
        """
        :param host: L'adresse locale du daemon C.
        :param port: Le port local du daemon C.
        :param local_id: L'identifiant local de ce process.
        """
        self.host = host
        self.port = port
        self.local_id = local_id
        
        self.sock = None
        self.connected = False
        
        # File de messages atomique pour communication Thread Réseau -> Thread Principal (Jeu)
        self.message_queue = Queue()
        
        # Flag de fin d'exécution
        self.running = True
        
        # Thread d'écoute
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)

    def connect(self):
        """Tente de se connecter au Daemon C."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Désactive l'algorithme de Nagle pour réduire la latence bêtement (important pour du temps réel)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.sock.connect((self.host, self.port))
            self.connected = True
            print(f"[IPC Python] Connecté au Daemon C local ({self.host}:{self.port}) en TCP ! 🔗")
            
            # Démarre le thread d'écoute uniquement si on est bien connecté
            self.listener_thread.start()
            
        except Exception as e:
            print(f"[IPC Python] Échec de la connexion au Daemon C : {e}")
            self.connected = False

    def close(self):
        """Ferme la communication proprement."""
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.connected = False
        print("[IPC Python] Déconnecté.")

    def _listen_loop(self):
        """Boucle infinie tournant dans un thread séparé qui lit le TCP."""
        buffer = ""
        while self.running and self.connected:
            try:
                data = self.sock.recv(4096)
                if not data:
                    print("[IPC Python] Connexion TCP fermée par le serveur.")
                    self.connected = False
                    break
                
                # Le flux TCP peut accrocher plusieurs messages collés. On sépare via newline '\n'
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        try:
                            msg = json.loads(line)
                            self.message_queue.put(msg)
                        except json.JSONDecodeError:
                            logging.error(f"[IPC] Impossible de déchiffrer le JSON : {line}")

            except Exception as e:
                if self.running:
                    logging.error(f"[IPC Python] Erreur socket : {e}")
                self.connected = False
                break

    def _send_message(self, msg_type: str, payload: dict):
        """Méthode interne d'envoi JSON balisé par '\n' pour découpage propre côté C."""
        if not self.connected or not self.sock:
            return

        message = {
            "source": self.local_id,
            "type": msg_type,
            "payload": payload
        }
        data_str = json.dumps(message) + "\n"
        
        try:
            self.sock.sendall(data_str.encode('utf-8'))
        except Exception as e:
            logging.error(f"[IPC Python] Erreur d'envoi TCP: {e}")
            self.connected = False

    # -------------------------------------------------------------
    # API PUBLIQUE UTILISÉE PAR LE MODÈLE DE JEU PYTHON
    # -------------------------------------------------------------

    def send_state_update(self, sync_state: dict):
        """Envoie un dump de toutes les entités locales qu'on possède au C pour broadcast."""
        self._send_message("STATE_UPDATE", sync_state)

    def request_ownership(self, entity_id: str):
        """Demande au P2P l'autorité sur une unité."""
        self._send_message("REQUEST_OWNERSHIP", {"entity_id": entity_id})

    def grant_ownership(self, entity_id: str, to_peer_id: str):
        """Accepte de céder la priorité."""
        self._send_message("GRANT_OWNERSHIP", {"entity_id": entity_id, "new_owner": to_peer_id})

    def poll_messages(self) -> list:
        """
        Lit tous les messages arrivés depuis le Processus C sans bloquer.
        Doit être appelé par le Jeu (game.step) chaque frame.
        """
        messages = []
        while True:
            try:
                # get_nowait ne bloque jamais
                msg = self.message_queue.get_nowait()
                messages.append(msg)
            except Empty:
                break
        return messages
