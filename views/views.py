import pygame
import webbrowser
import os
import pickle  # Module pour sauvegarder/charger les objets Python

# --- CONSTANTES ---
TILE_WIDTH = 64
TILE_HEIGHT = 32
SCREEN_W = 1024
SCREEN_H = 768

# Configuration Minimap
MINIMAP_WIDTH = 300     # On fixe la largeur, la hauteur sera calculée automatiquement
MINIMAP_MARGIN = 20     # Marge depuis le bord de l'écran
MINIMAP_BORDER = 2      # Épaisseur bordure blanche

# Couleurs
COLOR_TEAM_A = (0, 80, 255)   # Bleu
COLOR_TEAM_B = (220, 20, 60)  # Rouge
COLOR_MINIMAP_BG = (30, 30, 30) # Gris Foncé
COLOR_VIEWPORT = (255, 255, 255) # Cadre blanc caméra

# Nouvelles couleurs pour l'UI
COLOR_PANEL_BG = (0, 0, 0, 180) # Noir semi-transparent
COLOR_TEXT = (255, 255, 255) # Blanc

class GUI:
    def __init__(self, game_instance):
        self.game = game_instance
        self.map = getattr(game_instance, 'map', None)
        
        self.camera_x = SCREEN_W // 2
        self.camera_y = 50
        
        # État de la minimap
        self.show_minimap = True
        
        # --- NOUVEAU : États des panneaux de stats ---
        self.show_panel_a = True   # F1
        self.show_panel_b = True   # F2
        self.show_details = True   # F3
        self.show_ui_master = True # F4
        
        # Timer pour éviter le "rebond" des touches (clignotement)
        self.last_toggle_time = 0
        
        self.assets = {}
        self._load_assets()

        # Polices d'écriture pour l'UI
        pygame.font.init()
        self.font_ui = pygame.font.SysFont("Arial", 14)
        self.font_title = pygame.font.SysFont("Arial", 16, bold=True)

    def _load_assets(self):
        # 1. SOL
        try:
            img = pygame.image.load("assets/grass.png").convert()
            img.set_colorkey(img.get_at((0,0)))
            self.assets['grass'] = pygame.transform.scale(img, (TILE_WIDTH, TILE_HEIGHT))
        except:
            s = pygame.Surface((TILE_WIDTH, TILE_HEIGHT)); s.fill((34, 139, 34))
            self.assets['grass'] = s

        # 2. KNIGHT
        try:
            img_k = pygame.image.load("assets/knight.png").convert_alpha()
            coin = img_k.get_at((0,0))
            if coin.a == 255: img_k.set_colorkey(coin)
            self.assets['knight'] = pygame.transform.scale(img_k, (50, 50))
        except:
            s = pygame.Surface((30, 30), pygame.SRCALPHA); pygame.draw.circle(s, (200, 0, 0), (15, 15), 15)
            self.assets['knight'] = s

        # 3. AUTRES
        for name in ["pikeman", "crossbowman"]:
            try:
                img = pygame.image.load(f"assets/{name}.png").convert_alpha()
                self.assets[name] = pygame.transform.scale(img, (40, 40))
            except:
                s = pygame.Surface((30, 30), pygame.SRCALPHA); pygame.draw.circle(s, (100, 100, 100), (15, 15), 12)
                self.assets[name] = s

    def cart_to_iso(self, row, col):
        """ Conversion Grille -> Pixels Isométriques """
        iso_x = (col - row) * (TILE_WIDTH // 2)
        iso_y = (row + col) * (TILE_HEIGHT // 2)
        return iso_x, iso_y

    def iso_to_grid(self, x, y):
        """ Conversion inverse : Pixels Iso -> Grille """
        half_w = TILE_WIDTH / 2
        half_h = TILE_HEIGHT / 2
        col = (y / half_h + x / half_w) / 2
        row = (y / half_h - x / half_w) / 2
        return row, col

    def center_camera_on(self, row, col):
        """ Téléporte la caméra pour centrer la case (row, col) """
        target_x, target_y = self.cart_to_iso(row, col)
        self.camera_x = (SCREEN_W // 2) - target_x
        self.camera_y = (SCREEN_H // 2) - target_y

    def handle_input(self):
        """ Gère toutes les entrées (Clavier et Souris) """
        keys = pygame.key.get_pressed()
        
        # 1. Caméra Clavier (Maintenu)
        s = 20
        if keys[pygame.K_LEFT]: self.camera_x += s
        if keys[pygame.K_RIGHT]: self.camera_x -= s
        if keys[pygame.K_UP]: self.camera_y += s
        if keys[pygame.K_DOWN]: self.camera_y -= s

        # 2. Touches "Toggle" (Appui unique)
        # On utilise un délai (cooldown) de 200ms pour éviter le clignotement rapide
        current_time = pygame.time.get_ticks()
        if current_time - self.last_toggle_time > 200:
            
            # F1 - F4 : Gestion UI
            if keys[pygame.K_F1]:
                self.show_panel_a = not self.show_panel_a
                self.last_toggle_time = current_time
            if keys[pygame.K_F2]:
                self.show_panel_b = not self.show_panel_b
                self.last_toggle_time = current_time
            if keys[pygame.K_F3]:
                self.show_details = not self.show_details
                self.last_toggle_time = current_time
            if keys[pygame.K_F4]:
                self.show_ui_master = not self.show_ui_master
                self.last_toggle_time = current_time
            
            # M : Minimap
            if keys[pygame.K_m]:
                self.show_minimap = not self.show_minimap
                self.last_toggle_time = current_time

            # --- SAUVEGARDE ET CHARGEMENT (F11 / F12) ---
            
            # F11 : Sauvegarde Rapide (Quick Save)
            if keys[pygame.K_F11]:
                try:
                    # On sauvegarde l'objet 'game' complet dans un fichier
                    with open("quicksave.pkl", "wb") as f:
                        pickle.dump(self.game, f)
                    print("💾 Partie sauvegardée dans 'quicksave.pkl'")
                    # Petit hack visuel : on utilise le titre pour confirmer
                    pygame.display.set_caption("Age of Python - PARTIE SAUVEGARDÉE !")
                except Exception as e:
                    print(f"❌ Erreur sauvegarde : {e}")
                self.last_toggle_time = current_time

            # F12 : Chargement Rapide (Quick Load)
            if keys[pygame.K_F12]:
                if os.path.exists("quicksave.pkl"):
                    try:
                        with open("quicksave.pkl", "rb") as f:
                            loaded_game = pickle.load(f)
                        
                        # ASTUCE : On met à jour l'objet game existant avec les données chargées
                        # Cela permet de ne pas briser la référence dans la boucle principale
                        self.game.__dict__.update(loaded_game.__dict__)
                        
                        # On met à jour la référence de la map dans la GUI
                        self.map = self.game.map
                        
                        print("📂 Partie chargée avec succès !")
                        pygame.display.set_caption("Age of Python - PARTIE CHARGÉE !")
                    except Exception as e:
                        print(f"❌ Erreur chargement : {e}")
                else:
                    print("⚠️ Aucune sauvegarde trouvée.")
                self.last_toggle_time = current_time


        # --- GESTION SOURIS MINIMAP ---
        if self.show_minimap and self.show_ui_master and pygame.mouse.get_pressed()[0] and self.map:
            mx, my = pygame.mouse.get_pos()
            
            # Récupération dimensions
            max_rows = getattr(self.map, 'rows', 120)
            max_cols = getattr(self.map, 'cols', 120)
            
            # --- CALCUL TAILLE SUR MESURE ---
            iso_width = (max_cols + max_rows) * TILE_WIDTH / 2
            iso_height = (max_cols + max_rows) * TILE_HEIGHT / 2
            
            # Facteur d'échelle basé sur la largeur fixe
            scale = MINIMAP_WIDTH / iso_width
            
            # Hauteur ajustée (Plus de carré forcé !)
            mini_height = iso_height * scale
            
            # Coordonnées écran
            mini_x = SCREEN_W - MINIMAP_WIDTH - MINIMAP_MARGIN
            mini_y = SCREEN_H - mini_height - MINIMAP_MARGIN
            offset_x_world = max_rows * TILE_WIDTH / 2
            
            # Si on clique DANS la zone ajustée
            if mini_x <= mx <= mini_x + MINIMAP_WIDTH and mini_y <= my <= mini_y + mini_height:
                
                # Position relative dans le rectangle
                rel_x = mx - mini_x
                rel_y = my - mini_y
                
                # Conversion Minimap -> World Iso
                # mx = (wx + offset) * scale  => wx = (mx/scale) - offset
                world_click_x = (rel_x / scale) - offset_x_world
                world_click_y = rel_y / scale
                
                # On centre la caméra
                self.camera_x = (SCREEN_W // 2) - world_click_x
                self.camera_y = (SCREEN_H // 2) - world_click_y

    def draw_minimap(self, screen):
        """ Dessine la minimap rectangulaire en bas à droite """
        if not self.show_minimap or not self.map or not self.show_ui_master:
            return

        max_rows = getattr(self.map, 'rows', 120)
        max_cols = getattr(self.map, 'cols', 120)

        # --- CALCULS DE PROJECTION ---
        iso_width = (max_cols + max_rows) * TILE_WIDTH / 2
        iso_height = (max_cols + max_rows) * TILE_HEIGHT / 2
        scale = MINIMAP_WIDTH / iso_width
        mini_height = iso_height * scale

        rect_x = SCREEN_W - MINIMAP_WIDTH - MINIMAP_MARGIN
        rect_y = SCREEN_H - mini_height - MINIMAP_MARGIN
        offset_x_world = max_rows * TILE_WIDTH / 2

        def to_mini(r, c):
            wx, wy = self.cart_to_iso(r, c)
            mx = rect_x + (wx + offset_x_world) * scale
            my = rect_y + (wy) * scale
            return mx, my

        # 1. Fond Gris Foncé (Rectangle ajusté)
        pygame.draw.rect(screen, COLOR_MINIMAP_BG, (rect_x, rect_y, MINIMAP_WIDTH, mini_height))
        # Bordure Blanche
        pygame.draw.rect(screen, (255, 255, 255), (rect_x, rect_y, MINIMAP_WIDTH, mini_height), MINIMAP_BORDER)

        # 2. Losange Vert (Map)
        p1 = to_mini(0, 0); p2 = to_mini(0, max_cols); p3 = to_mini(max_rows, max_cols); p4 = to_mini(max_rows, 0)
        
        # On dessine le losange vert par dessus le gris (optionnel, ou on garde juste le gris)
        pygame.draw.polygon(screen, (34, 139, 34), [p1, p2, p3, p4]) # Vert un peu plus foncé
        pygame.draw.polygon(screen, (100, 200, 100), [p1, p2, p3, p4], 1) # Contour map

        # 3. Points des Unités
        units = getattr(self.game, 'alive_units', lambda: [])()
        for unit in units:
            u_row = getattr(unit, 'x', 0) 
            u_col = getattr(unit, 'y', 0) 
            
            px, py = to_mini(u_row, u_col)

            team = getattr(unit, 'team', '?')
            color = COLOR_TEAM_A if team == "A" else COLOR_TEAM_B
            
            # Petit cercle
            pygame.draw.circle(screen, color, (int(px), int(py)), 3)

        # 4. Cadre de la Caméra
        # Position du coin haut-gauche de la caméra dans le monde
        cam_world_x = -self.camera_x
        cam_world_y = -self.camera_y
        
        mini_cam_x = rect_x + (cam_world_x + offset_x_world) * scale
        mini_cam_y = rect_y + (cam_world_y) * scale
        
        mini_cam_w = SCREEN_W * scale
        mini_cam_h = SCREEN_H * scale
        
        # On dessine le rectangle de vue
        # On utilise un clipping pour qu'il ne sorte pas du cadre gris (esthétique)
        camera_rect = pygame.Rect(mini_cam_x, mini_cam_y, mini_cam_w, mini_cam_h)
        
        # Dessin du cadre (non clippé pour voir où on est même si hors map)
        pygame.draw.rect(screen, COLOR_VIEWPORT, camera_rect, 1)

    # --- NOUVEAU : Méthode pour dessiner les stats ---
    def draw_army_stats(self, screen):
        """ Affiche les panneaux de statistiques des armées """
        if not self.show_ui_master: return

        # 1. Calcul des comptes en temps réel
        counts = {'A': {}, 'B': {}}
        totals = {'A': 0, 'B': 0}

        units = getattr(self.game, 'alive_units', lambda: [])()
        for u in units:
            team = getattr(u, 'team', '?')
            u_type = type(u).__name__
            
            if team not in counts: counts[team] = {}
            
            counts[team][u_type] = counts[team].get(u_type, 0) + 1
            totals[team] += 1

        # 2. Dessin Panneau A (Gauche)
        if self.show_panel_a:
            self._draw_single_panel(screen, "Équipe A (Bleu)", counts.get('A', {}), totals.get('A', 0), 20, 20, COLOR_TEAM_A)

        # 3. Dessin Panneau B (Droite)
        if self.show_panel_b:
            self._draw_single_panel(screen, "Équipe B (Rouge)", counts.get('B', {}), totals.get('B', 0), SCREEN_W - 220, 20, COLOR_TEAM_B)

    def _draw_single_panel(self, screen, title, data, total, x, y, color):
        # Hauteur dynamique
        h = 35
        if self.show_details:
            h += len(data) * 20 + 5

        # Fond
        s = pygame.Surface((200, h), pygame.SRCALPHA)
        s.fill(COLOR_PANEL_BG) 
        screen.blit(s, (x, y))
        
        # Bordure de couleur
        pygame.draw.rect(screen, color, (x, y, 4, h))

        # Titre
        title_surf = self.font_title.render(f"{title}: {total}", True, COLOR_TEXT)
        screen.blit(title_surf, (x + 10, y + 8))

        # Détails
        if self.show_details:
            y_off = 35
            for u_type, count in sorted(data.items()):
                # Icône
                icon = self.assets.get(u_type.lower())
                txt_x = x + 10
                if icon:
                    icon_small = pygame.transform.scale(icon, (16, 16))
                    screen.blit(icon_small, (x + 10, y + y_off))
                    txt_x = x + 30
                
                txt_surf = self.font_ui.render(f"{u_type}: {count}", True, (200, 200, 200))
                screen.blit(txt_surf, (txt_x, y + y_off))
                y_off += 20

    def draw(self, screen):
        screen.fill((20, 20, 20))

        # MAP
        if self.map:
            rows = getattr(self.map, 'rows', 20)
            cols = getattr(self.map, 'cols', 20)
            for row in range(rows):
                for col in range(cols):
                    x, y = self.cart_to_iso(row, col)
                    final_x = x + self.camera_x
                    final_y = y + self.camera_y
                    if -64 < final_x < SCREEN_W and -32 < final_y < SCREEN_H:
                        screen.blit(self.assets['grass'], (final_x, final_y))

        # UNITÉS
        units = getattr(self.game, 'alive_units', lambda: [])()
        for unit in units:
            u_x = getattr(unit, 'x', 0); u_y = getattr(unit, 'y', 0)
            x_iso, y_iso = self.cart_to_iso(u_x, u_y)
            screen_x = x_iso + self.camera_x + 8; screen_y = y_iso + self.camera_y - 20

            team = getattr(unit, 'team', '?')
            color = COLOR_TEAM_A if team == "A" else COLOR_TEAM_B
            pygame.draw.ellipse(screen, color, (screen_x + 5, screen_y + 40, 30, 8))

            u_type = type(unit).__name__.lower()
            img = self.assets.get(u_type, self.assets.get('knight'))
            
            if img:
                if team == "A":
                    img = pygame.transform.flip(img, True, False)
                screen.blit(img, (screen_x, screen_y))
            
            hp = getattr(unit, 'hp', 0)
            if hp > 0:
                pygame.draw.rect(screen, (0,0,0), (screen_x, screen_y - 5, 40, 4))
                w = min(40, max(0, int(hp / 2.5))) 
                pygame.draw.rect(screen, (0, 255, 0), (screen_x, screen_y - 5, w, 4))

        # --- DESSIN DES PANNEAUX UI (EN DERNIER) ---
        self.draw_minimap(screen)
        self.draw_army_stats(screen)