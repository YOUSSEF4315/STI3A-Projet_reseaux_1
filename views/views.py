import pygame

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

class GUI:
    def __init__(self, game_instance):
        self.game = game_instance
        self.map = getattr(game_instance, 'map', None)
        
        self.camera_x = SCREEN_W // 2
        self.camera_y = 50
        
        # État de la minimap
        self.show_minimap = True
        
        self.assets = {}
        self._load_assets()

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
        keys = pygame.key.get_pressed()
        s = 20
        # Caméra Clavier
        if keys[pygame.K_LEFT]: self.camera_x += s
        if keys[pygame.K_RIGHT]: self.camera_x -= s
        if keys[pygame.K_UP]: self.camera_y += s
        if keys[pygame.K_DOWN]: self.camera_y -= s

        if keys[pygame.K_m]: pass 

        # --- GESTION SOURIS MINIMAP ---
        if self.show_minimap and pygame.mouse.get_pressed()[0] and self.map:
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
            
            # Décalage monde
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
        """ Dessine la minimap isométrique ajustée """
        if not self.show_minimap or not self.map:
            return

        max_rows = getattr(self.map, 'rows', 120)
        max_cols = getattr(self.map, 'cols', 120)

        # --- CALCULS DE PROJECTION ---
        iso_width = (max_cols + max_rows) * TILE_WIDTH / 2
        iso_height = (max_cols + max_rows) * TILE_HEIGHT / 2
        
        # Echelle pour tenir dans MINIMAP_WIDTH
        scale = MINIMAP_WIDTH / iso_width
        
        # Hauteur calculée (Sur Mesure)
        mini_height = iso_height * scale

        # Position sur l'écran (Bas Droite)
        rect_x = SCREEN_W - MINIMAP_WIDTH - MINIMAP_MARGIN
        rect_y = SCREEN_H - mini_height - MINIMAP_MARGIN
        
        # Décalage X monde
        offset_x_world = max_rows * TILE_WIDTH / 2

        # Fonction locale de conversion
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
        p1 = to_mini(0, 0)
        p2 = to_mini(0, max_cols)
        p3 = to_mini(max_rows, max_cols)
        p4 = to_mini(max_rows, 0)
        
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
        container_rect = pygame.Rect(rect_x, rect_y, MINIMAP_WIDTH, mini_height)
        
        # Dessin du cadre (non clippé pour voir où on est même si hors map)
        pygame.draw.rect(screen, COLOR_VIEWPORT, camera_rect, 1)

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
            u_x = getattr(unit, 'x', 0)
            u_y = getattr(unit, 'y', 0)
            x_iso, y_iso = self.cart_to_iso(u_x, u_y)
            screen_x = x_iso + self.camera_x + 8
            screen_y = y_iso + self.camera_y - 20

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

        # MINIMAP
        self.draw_minimap(screen)