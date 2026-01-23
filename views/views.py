import pygame
import webbrowser
import os
import pickle

# --- CONSTANTES DE BASE ---
TILE_WIDTH = 64
TILE_HEIGHT = 32
DEFAULT_SCREEN_W = 1024
DEFAULT_SCREEN_H = 768

# Configuration Minimap
MINIMAP_WIDTH = 300
MINIMAP_MARGIN = 20
MINIMAP_BORDER = 2

# Couleurs
COLOR_TEAM_A = (0, 80, 255)
COLOR_TEAM_B = (220, 20, 60)
COLOR_MINIMAP_BG = (30, 30, 30)
COLOR_VIEWPORT = (255, 255, 255)
COLOR_PANEL_BG = (0, 0, 0, 180)
COLOR_TEXT = (255, 255, 255)

class GUI:
    def __init__(self, game_instance, screen_width=DEFAULT_SCREEN_W, screen_height=DEFAULT_SCREEN_H):
        self.game = game_instance
        self.map = getattr(game_instance, 'map', None)
        
        self.screen_w = screen_width
        self.screen_h = screen_height
        
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 2.0
        
        self.center_camera_on(10, 10)
        
        # --- SOLUTION DRAG & DROP ---
        self.is_dragging = False  # L'interrupteur magique
        
        # UI States
        self.show_minimap = True
        self.show_panel_a = True
        self.show_panel_b = True
        self.show_details = True
        self.show_ui_master = True
        self.last_toggle_time = 0
        
        self.assets = {}
        self._load_assets()

        pygame.font.init()
        self.font_ui = pygame.font.SysFont("Arial", 14)
        self.font_title = pygame.font.SysFont("Arial", 16, bold=True)
        
        # Purge du mouvement initial
        pygame.mouse.get_rel()

    def _load_assets(self):
        try:
            img = pygame.image.load("assets/grass.png").convert()
            img.set_colorkey(img.get_at((0,0)))
            self.assets['grass'] = pygame.transform.scale(img, (TILE_WIDTH, TILE_HEIGHT))
        except:
            s = pygame.Surface((TILE_WIDTH, TILE_HEIGHT)); s.fill((34, 139, 34))
            self.assets['grass'] = s

        try:
            img_k = pygame.image.load("assets/knight.png").convert_alpha()
            self.assets['knight'] = pygame.transform.scale(img_k, (50, 50))
        except:
            s = pygame.Surface((30, 30), pygame.SRCALPHA); pygame.draw.circle(s, (200, 0, 0), (15, 15), 15)
            self.assets['knight'] = s

        for name in ["pikeman", "crossbowman"]:
            try:
                img = pygame.image.load(f"assets/{name}.png").convert_alpha()
                self.assets[name] = pygame.transform.scale(img, (40, 40))
            except:
                s = pygame.Surface((30, 30), pygame.SRCALPHA); pygame.draw.circle(s, (100, 100, 100), (15, 15), 12)
                self.assets[name] = s

    def get_scaled_tile_size(self):
        return TILE_WIDTH * self.zoom, TILE_HEIGHT * self.zoom

    def cart_to_iso(self, row, col):
        w, h = self.get_scaled_tile_size()
        iso_x = (col - row) * (w / 2)
        iso_y = (row + col) * (h / 2)
        return iso_x, iso_y

    def iso_to_grid(self, x, y):
        w, h = self.get_scaled_tile_size()
        adj_x = x - self.camera_x
        adj_y = y - self.camera_y
        half_w = w / 2
        half_h = h / 2
        col = (adj_y / half_h + adj_x / half_w) / 2
        row = (adj_y / half_h - adj_x / half_w) / 2
        return int(row), int(col)

    def center_camera_on(self, row, col):
        target_x, target_y = self.cart_to_iso(row, col)
        self.camera_x = (self.screen_w // 2) - target_x
        self.camera_y = (self.screen_h // 2) - target_y

    # --- 1. GESTION DES CLICS (EVENTS) ---
    def handle_events(self, event):
        """ Gère les actions 'one-shot' : Clic, Relâchement, Zoom, Resize """
        
        # Redimensionnement
        if event.type == pygame.VIDEORESIZE:
            self.screen_w, self.screen_h = event.w, event.h

        # Zoom (Molette Scroll)
        elif event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                self.zoom = min(self.max_zoom, self.zoom + 0.1)
            elif event.y < 0:
                self.zoom = max(self.min_zoom, self.zoom - 0.1)

        # DÉBUT DU CLIC (Appui)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # 3 = Clic Droit, 2 = Clic Molette (Bouton du milieu)
            if event.button == 3 or event.button == 2:
                self.is_dragging = True
                pygame.mouse.get_rel() # Important : On remet le compteur de mouvement à zéro ici !

        # FIN DU CLIC (Relâchement)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3 or event.button == 2:
                self.is_dragging = False

    # --- 2. GESTION CONTINUE (BOUCLE) ---
    def handle_input(self):
        """ Gère le mouvement continu tant que le bouton est actif """
        keys = pygame.key.get_pressed()
        
        # Clavier
        s = 20 / self.zoom 
        if keys[pygame.K_LEFT]: self.camera_x += s
        if keys[pygame.K_RIGHT]: self.camera_x -= s
        if keys[pygame.K_UP]: self.camera_y += s
        if keys[pygame.K_DOWN]: self.camera_y -= s

        # Souris (Si l'interrupteur est ON)
        if self.is_dragging:
            dx, dy = pygame.mouse.get_rel()
            self.camera_x += dx
            self.camera_y += dy
        else:
            # On vide le buffer de mouvement même si on ne bouge pas la caméra
            # pour éviter un saut au prochain clic
            pygame.mouse.get_rel()

        # Raccourcis UI
        current_time = pygame.time.get_ticks()
        if current_time - self.last_toggle_time > 200:
            if keys[pygame.K_F1]: self.show_panel_a = not self.show_panel_a; self.last_toggle_time = current_time
            if keys[pygame.K_F2]: self.show_panel_b = not self.show_panel_b; self.last_toggle_time = current_time
            if keys[pygame.K_F3]: self.show_details = not self.show_details; self.last_toggle_time = current_time
            if keys[pygame.K_F4]: self.show_ui_master = not self.show_ui_master; self.last_toggle_time = current_time
            if keys[pygame.K_m]: self.show_minimap = not self.show_minimap; self.last_toggle_time = current_time
            if keys[pygame.K_F11]: self._quick_save(); self.last_toggle_time = current_time
            if keys[pygame.K_F12]: self._quick_load(); self.last_toggle_time = current_time

        # Minimap (Clic Gauche standard)
        if self.show_minimap and self.show_ui_master and pygame.mouse.get_pressed()[0] and not self.is_dragging:
            self._handle_minimap_click()

    # ... (Le reste des méthodes est identique et n'a pas besoin de changer) ...
    def _quick_save(self):
        try:
            with open("quicksave.pkl", "wb") as f: pickle.dump(self.game, f)
            print("💾 Sauvegardé"); pygame.display.set_caption("Age of Python - SAUVEGARDÉ")
        except Exception as e: print(f"Erreur Save: {e}")

    def _quick_load(self):
        if os.path.exists("quicksave.pkl"):
            try:
                with open("quicksave.pkl", "rb") as f:
                    loaded = pickle.load(f)
                    self.game.__dict__.update(loaded.__dict__)
                    self.map = self.game.map
                print("📂 Chargé")
            except Exception as e: print(f"Erreur Load: {e}")

    def _handle_minimap_click(self):
        if not self.map: return
        mx, my = pygame.mouse.get_pos()
        max_rows = getattr(self.map, 'rows', 120); max_cols = getattr(self.map, 'cols', 120)
        base_iso_w = (max_cols + max_rows) * TILE_WIDTH / 2; base_iso_h = (max_cols + max_rows) * TILE_HEIGHT / 2
        scale = MINIMAP_WIDTH / base_iso_w; mini_height = base_iso_h * scale
        rect_x = self.screen_w - MINIMAP_WIDTH - MINIMAP_MARGIN; rect_y = self.screen_h - mini_height - MINIMAP_MARGIN
        
        if rect_x <= mx <= rect_x + MINIMAP_WIDTH and rect_y <= my <= rect_y + mini_height:
            rel_x = mx - rect_x; rel_y = my - rect_y
            offset_x_world = max_rows * TILE_WIDTH / 2
            world_x = (rel_x / scale) - offset_x_world; world_y = rel_y / scale
            self.camera_x = (self.screen_w // 2) - world_x; self.camera_y = (self.screen_h // 2) - world_y

    def draw_minimap(self, screen):
        if not self.show_minimap or not self.map or not self.show_ui_master: return

        # 1. Calculs de base
        max_rows = getattr(self.map, 'rows', 120)
        max_cols = getattr(self.map, 'cols', 120)
        
        base_iso_w = (max_cols + max_rows) * TILE_WIDTH / 2
        base_iso_h = (max_cols + max_rows) * TILE_HEIGHT / 2
        
        scale = MINIMAP_WIDTH / base_iso_w
        mini_height = base_iso_h * scale
        
        rect_x = self.screen_w - MINIMAP_WIDTH - MINIMAP_MARGIN
        rect_y = self.screen_h - mini_height - MINIMAP_MARGIN
        offset_x_world = max_rows * TILE_WIDTH / 2

        def to_mini(r, c):
            wx = (c - r) * (TILE_WIDTH // 2)
            wy = (r + c) * (TILE_HEIGHT // 2)
            mx = rect_x + (wx + offset_x_world) * scale
            my = rect_y + wy * scale
            return mx, my

        # 2. Dessin Fond et Carte
        pygame.draw.rect(screen, COLOR_MINIMAP_BG, (rect_x, rect_y, MINIMAP_WIDTH, mini_height))
        pygame.draw.rect(screen, (255, 255, 255), (rect_x, rect_y, MINIMAP_WIDTH, mini_height), MINIMAP_BORDER)
        
        p1 = to_mini(0, 0); p2 = to_mini(0, max_cols); p3 = to_mini(max_rows, max_cols); p4 = to_mini(max_rows, 0)
        pygame.draw.polygon(screen, (34, 139, 34), [p1, p2, p3, p4])
        pygame.draw.polygon(screen, (100, 200, 100), [p1, p2, p3, p4], 1)

        # 3. Dessin Unités
        units = getattr(self.game, 'alive_units', lambda: [])()
        for unit in units:
            px, py = to_mini(getattr(unit, 'x', 0), getattr(unit, 'y', 0))
            color = COLOR_TEAM_A if getattr(unit, 'team', '?') == "A" else COLOR_TEAM_B
            pygame.draw.circle(screen, color, (int(px), int(py)), 3)

        # 4. Dessin du Cadre Caméra (CORRIGÉ)
        # On divise par le zoom pour obtenir les vraies coordonnées monde
        view_w_world = self.screen_w / self.zoom
        view_h_world = self.screen_h / self.zoom
        
        # --- LA CORRECTION EST ICI ---
        cam_world_x = -self.camera_x / self.zoom
        cam_world_y = -self.camera_y / self.zoom
        # -----------------------------

        mini_cam_x = rect_x + (cam_world_x + offset_x_world) * scale
        mini_cam_y = rect_y + cam_world_y * scale
        
        mini_cam_w = view_w_world * scale
        mini_cam_h = view_h_world * scale
        
        pygame.draw.rect(screen, COLOR_VIEWPORT, (mini_cam_x, mini_cam_y, mini_cam_w, mini_cam_h), 1)

    def draw_army_stats(self, screen):
        if not self.show_ui_master: return
        counts = {'A': {}, 'B': {}}; totals = {'A': 0, 'B': 0}
        units = getattr(self.game, 'alive_units', lambda: [])()
        for u in units:
            team = getattr(u, 'team', '?'); u_type = type(u).__name__
            if team not in counts: counts[team] = {}
            counts[team][u_type] = counts[team].get(u_type, 0) + 1; totals[team] += 1
        if self.show_panel_a: self._draw_single_panel(screen, "Équipe A", counts.get('A', {}), totals.get('A', 0), 20, 20, COLOR_TEAM_A)
        if self.show_panel_b: self._draw_single_panel(screen, "Équipe B", counts.get('B', {}), totals.get('B', 0), self.screen_w - 220, 20, COLOR_TEAM_B)

    def _draw_single_panel(self, screen, title, data, total, x, y, color):
        h = 35
        if self.show_details: h += len(data) * 20 + 5
        s = pygame.Surface((200, h), pygame.SRCALPHA); s.fill(COLOR_PANEL_BG); screen.blit(s, (x, y))
        pygame.draw.rect(screen, color, (x, y, 4, h))
        title_surf = self.font_title.render(f"{title}: {total}", True, COLOR_TEXT); screen.blit(title_surf, (x + 10, y + 8))
        if self.show_details:
            y_off = 35
            for u_type, count in sorted(data.items()):
                icon = self.assets.get(u_type.lower())
                txt_x = x + 10
                if icon:
                    try: icon_ui = pygame.transform.scale(icon, (16, 16)); screen.blit(icon_ui, (x + 10, y + y_off)); txt_x = x + 30
                    except: pass
                txt_surf = self.font_ui.render(f"{u_type}: {count}", True, (200, 200, 200)); screen.blit(txt_surf, (txt_x, y + y_off)); y_off += 20

    def draw(self, screen):
        screen.fill((20, 20, 20))
        tw, th = self.get_scaled_tile_size()
        if self.map:
            rows = getattr(self.map, 'rows', 20); cols = getattr(self.map, 'cols', 20)
            scaled_grass = pygame.transform.scale(self.assets['grass'], (int(tw), int(th)))
            for row in range(rows):
                for col in range(cols):
                    x, y = self.cart_to_iso(row, col); final_x = x + self.camera_x; final_y = y + self.camera_y
                    if -tw < final_x < self.screen_w and -th < final_y < self.screen_h: screen.blit(scaled_grass, (final_x, final_y))
        units = getattr(self.game, 'alive_units', lambda: [])()
        for unit in units:
            u_x = getattr(unit, 'x', 0); u_y = getattr(unit, 'y', 0)
            x_iso, y_iso = self.cart_to_iso(u_x, u_y)
            screen_x = x_iso + self.camera_x; screen_y = y_iso + self.camera_y 
            if -100 < screen_x < self.screen_w and -100 < screen_y < self.screen_h:
                u_type = type(unit).__name__.lower(); orig_img = self.assets.get(u_type, self.assets.get('knight'))
                if orig_img:
                    img_w = int(orig_img.get_width() * self.zoom); img_h = int(orig_img.get_height() * self.zoom)
                    scaled_img = pygame.transform.scale(orig_img, (img_w, img_h))
                    team = getattr(unit, 'team', '?')
                    if team == "A": scaled_img = pygame.transform.flip(scaled_img, True, False)
                    draw_x = screen_x + (tw // 2) - (img_w // 2); draw_y = screen_y - (img_h // 1.5)
                    ellipse_w = int(30 * self.zoom); ellipse_h = int(8 * self.zoom)
                    pygame.draw.ellipse(screen, COLOR_TEAM_A if team == "A" else COLOR_TEAM_B, (screen_x + (tw//2) - ellipse_w//2, screen_y + (th//2) - ellipse_h//2, ellipse_w, ellipse_h))
                    screen.blit(scaled_img, (draw_x, draw_y))
                    hp = getattr(unit, 'hp', 0)
                    if hp > 0:
                        bar_w = int(40 * self.zoom); bar_h = int(4 * self.zoom); life_w = min(bar_w, max(0, int(hp / 2.5 * self.zoom)))
                        pygame.draw.rect(screen, (0,0,0), (draw_x, draw_y - bar_h - 2, bar_w, bar_h))
                        pygame.draw.rect(screen, (0, 255, 0), (draw_x, draw_y - bar_h - 2, life_w, bar_h))
        self.draw_minimap(screen)
        self.draw_army_stats(screen)