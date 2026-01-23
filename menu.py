#!/usr/bin/env python3
"""
menu.py - Menu de démarrage graphique pour MedievAIl Battle Simulator

Interface principale avec sélection de scénarios, IA, et options.
"""

import pygame
import sys
import os
import pickle

from scenarios import scenario_simple_vs_braindead, scenario_small_terminal, scenario_lanchester
from ai import CaptainBraindead, MajorDaft, AssasinJack, PredictEinstein
from smartAI import GeneralStrategus
from views.views import GUI

# --- CONSTANTES ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BG_COLOR = (20, 20, 30)
PANEL_COLOR = (40, 40, 60)
BUTTON_COLOR = (60, 80, 120)
BUTTON_HOVER = (40, 50, 80) # Darker than normal
BUTTON_ACTIVE = (100, 140, 200)
TEXT_COLOR = (255, 255, 255)
ACCENT_COLOR = (255, 215, 0)

# --- REGISTRES ---
AVAILABLE_AIS = {
    "Captain BRAINDEAD": CaptainBraindead,
    "Major DAFT": MajorDaft,
    "General STRATEGUS": GeneralStrategus,
    "Assasin JACK": AssasinJack,
    "Predict EINSTEIN": PredictEinstein,
}

AVAILABLE_SCENARIOS = {
    "Standard (Rapide)": scenario_small_terminal,
    "Grande Bataille": scenario_simple_vs_braindead,
}

AI_DESCRIPTIONS = {
    "Captain BRAINDEAD": "Statique - N'attaque que si ennemi en vue",
    "Major DAFT": "Agressive - Attaque le plus proche",
    "General STRATEGUS": "Tactique - Ciblage intelligent par type",
    "Assasin JACK": "Focus - Cible le plus faible",
    "Predict EINSTEIN": "Prédictive - Simule 5 coups à l'avance",
}


class Button:
    def __init__(self, x, y, width, height, text, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.hovered = False
        self.active = False

    def draw(self, screen):
        color = BUTTON_ACTIVE if self.active else (BUTTON_HOVER if self.hovered else BUTTON_COLOR)
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, TEXT_COLOR, self.rect, 2, border_radius=8)

        text_surf = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event):
        return self.hovered and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1


class DropdownMenu:
    def __init__(self, x, y, width, height, options, font, default=0):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.font = font
        self.selected_index = default
        self.expanded = False
        self.option_rects = []

    def get_selected(self):
        return self.options[self.selected_index]

    def draw(self, screen):
        # Bouton principal
        color = BUTTON_HOVER if self.expanded else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, TEXT_COLOR, self.rect, 2, border_radius=5)

        text = self.get_selected()
        if len(text) > 25:
            text = text[:22] + "..."
        text_surf = self.font.render(text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        screen.blit(text_surf, text_rect)

        # Flèche
        arrow = "▼" if not self.expanded else "▲"
        arrow_surf = self.font.render(arrow, True, TEXT_COLOR)
        arrow_rect = arrow_surf.get_rect(midright=(self.rect.right - 10, self.rect.centery))
        screen.blit(arrow_surf, arrow_rect)

        # Options déroulantes
        if self.expanded:
            self.option_rects = []
            for i, option in enumerate(self.options):
                opt_rect = pygame.Rect(
                    self.rect.x,
                    self.rect.bottom + i * self.rect.height,
                    self.rect.width,
                    self.rect.height
                )
                self.option_rects.append(opt_rect)

                color = BUTTON_HOVER if i == self.selected_index else PANEL_COLOR
                pygame.draw.rect(screen, color, opt_rect)
                pygame.draw.rect(screen, TEXT_COLOR, opt_rect, 1)

                opt_text = option
                if len(opt_text) > 25:
                    opt_text = opt_text[:22] + "..."
                opt_surf = self.font.render(opt_text, True, TEXT_COLOR)
                opt_text_rect = opt_surf.get_rect(midleft=(opt_rect.x + 10, opt_rect.centery))
                screen.blit(opt_surf, opt_text_rect)

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(mouse_pos):
                self.expanded = not self.expanded
                return True

            if self.expanded:
                for i, opt_rect in enumerate(self.option_rects):
                    if opt_rect.collidepoint(mouse_pos):
                        self.selected_index = i
                        self.expanded = False
                        return True
                # Clic en dehors = fermer
                self.expanded = False
        return False


class MainMenu:
    def __init__(self):
        pygame.init()
        # Fullscreen Desktop with Resizable option
        # Fallback to standard FULLSCREEN if FULLSCREEN_DESKTOP (Pygame 2.0+) is missing
        try:
            flags = pygame.FULLSCREEN | pygame.RESIZABLE
        except AttributeError:
            flags = pygame.FULLSCREEN

        # Use (0,0) to use current desktop resolution
        self.screen = pygame.display.set_mode((0, 0), flags)
        self.w, self.h = self.screen.get_size()
        pygame.display.set_caption("MedievAIl Battle - Menu Principal")

        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "main"  # main, setup, load, options

        # Fonts
        self.font_title = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_button = pygame.font.SysFont("Arial", 24)
        self.font_small = pygame.font.SysFont("Arial", 16)
        self.font_tiny = pygame.font.SysFont("Arial", 14)

        # Background
        try:
            bg_path = "assets/menu_background/backgroung.webp"
            if os.path.exists(bg_path):
                self.bg_raw = pygame.image.load(bg_path).convert()
            else:
                self.bg_raw = None
        except Exception as e:
            print(f"BG Load Error: {e}")
            self.bg_raw = None
        self.bg_scaled = None

        # Boutons du menu principal (Positions will be set in recalc_layout)
        self.btn_play = Button(0, 0, 300, 60, "NOUVELLE BATAILLE", self.font_button)
        self.btn_load = Button(0, 0, 300, 60, "CHARGER", self.font_button)
        self.btn_options = Button(0, 0, 300, 60, "OPTIONS", self.font_button)
        self.btn_quit = Button(0, 0, 300, 60, "QUITTER", self.font_button)

        # Setup screen
        self.setup_ai_a = DropdownMenu(0, 0, 400, 40, list(AVAILABLE_AIS.keys()), self.font_small, default=1)
        self.setup_ai_b = DropdownMenu(0, 0, 400, 40, list(AVAILABLE_AIS.keys()), self.font_small, default=0)
        self.setup_scenario = DropdownMenu(0, 0, 400, 40, list(AVAILABLE_SCENARIOS.keys()), self.font_small)
        self.btn_start = Button(0, 0, 300, 50, "LANCER LA BATAILLE", self.font_button)
        self.btn_back = Button(20, 20, 100, 40, "< RETOUR", self.font_small)

        # Load screen
        self.save_files = []
        self.selected_save = 0
        self.refresh_save_files()

        # Options
        self.speed_options = ["Lent (10 FPS)", "Normal (30 FPS)", "Rapide (60 FPS)", "Très Rapide (120 FPS)"]
        self.opt_speed = DropdownMenu(0, 0, 400, 40, self.speed_options, self.font_small, default=1)
        self.opt_auto_play = True
        
        # Checkbox rect (placeholder, updated in recalc)
        self.chk_rect = pygame.Rect(0, 0, 30, 30)

        # Custom Pointer
        try:
             p_img = pygame.image.load("assets/Pointer/attack48x48 (Copy).webp").convert_alpha()
             self.pointer_img = pygame.transform.scale(p_img, (32, 32))
        except Exception as e:
             print(f"Menu Pointer Error: {e}")
             self.pointer_img = None
        
        pygame.mouse.set_visible(False)
        
        self.recalc_layout()

    def recalc_layout(self):
        """Recalcule les positions des éléments basé sur la taille de l'écran"""
        self.w, self.h = self.screen.get_size()
        cx, cy = self.w // 2, self.h // 2
        
        # Update Background
        if self.bg_raw:
            self.bg_scaled = pygame.transform.smoothscale(self.bg_raw, (self.w, self.h))

        # Main Menu
        start_y = cy - 100
        gap = 80
        self.btn_play.rect.center = (cx, start_y)
        self.btn_load.rect.center = (cx, start_y + gap)
        self.btn_options.rect.center = (cx, start_y + gap*2)
        self.btn_quit.rect.center = (cx, start_y + gap*3)
        
        # Setup Screen
        # Labels are hardcoded in draw(), need to adjust them too or just center everything relative to buttons
        # For Dropdowns, we update their internal rects
        self.setup_ai_a.rect.center = (cx, 200); self.setup_ai_a.rect.x = cx - 200 # Fixed width 400
        self.setup_ai_b.rect.center = (cx, 280); self.setup_ai_b.rect.x = cx - 200
        self.setup_scenario.rect.center = (cx, 360); self.setup_scenario.rect.x = cx - 200
        
        self.btn_start.rect.center = (cx, 480)
        self.btn_back.rect.topleft = (20, 20)
        
        # Options
        self.opt_speed.rect.center = (cx, 200); self.opt_speed.rect.x = cx - 200
        self.chk_rect.topleft = (cx - 50, 280) # auto play checkbox

    def refresh_save_files(self):
        """Scan les fichiers .pkl dans le dossier"""
        self.save_files = []
        if os.path.exists("quicksave.pkl"):
            self.save_files.append("quicksave.pkl")

        for file in os.listdir("."):
            if file.endswith(".pkl") and file != "quicksave.pkl":
                self.save_files.append(file)

        if not self.save_files:
            self.save_files = ["Aucune sauvegarde trouvée"]

    def run(self):
        while self.running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return None

                self.handle_events(event, mouse_pos)

            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        return None

    def handle_events(self, event, mouse_pos):
        if event.type == pygame.VIDEORESIZE:
             # Use current flags or just RESIZABLE for windowed resize?
             # If we are strictly full screen, resize event might not happen or might be resolution change.
             # Let's simple reuse flags.
             flags = pygame.FULLSCREEN | pygame.RESIZABLE
             self.screen = pygame.display.set_mode((event.w, event.h), flags)
             self.recalc_layout()

        if self.state == "main":
            self.btn_play.update(mouse_pos)
            self.btn_load.update(mouse_pos)
            self.btn_options.update(mouse_pos)
            self.btn_quit.update(mouse_pos)

            if self.btn_play.is_clicked(event):
                self.state = "setup"
            elif self.btn_load.is_clicked(event):
                self.refresh_save_files()
                self.state = "load"
            elif self.btn_options.is_clicked(event):
                self.state = "options"
            elif self.btn_quit.is_clicked(event):
                self.running = False

        elif self.state == "setup":
            consumed = False
            if self.setup_ai_a.handle_event(event, mouse_pos): consumed = True
            elif self.setup_ai_b.handle_event(event, mouse_pos): consumed = True
            elif self.setup_scenario.handle_event(event, mouse_pos): consumed = True
            
            if not consumed:
                self.btn_back.update(mouse_pos)
                self.btn_start.update(mouse_pos)

                if self.btn_back.is_clicked(event):
                    self.state = "main"
                elif self.btn_start.is_clicked(event):
                    self.launch_battle()

        elif self.state == "load":
            self.btn_back.update(mouse_pos)

            if self.btn_back.is_clicked(event):
                self.state = "main"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                cx = self.w // 2
                for i, file in enumerate(self.save_files):
                    # Dynamic rect for hit testing? Or stored?
                    # Ideally stored, but here we can just rebuild it for click logic
                    # Or better: use a centered rect logic.
                    rect = pygame.Rect(0, 0, 400, 45)
                    rect.center = (cx, 150 + i * 50)
                    if rect.collidepoint(mouse_pos) and file != "Aucune sauvegarde trouvée":
                        self.load_save(file)

        elif self.state == "options":
            self.btn_back.update(mouse_pos)

            if self.btn_back.is_clicked(event):
                self.state = "main"

            self.opt_speed.handle_event(event, mouse_pos)

            # Toggle auto-play
            # self.chk_rect updated in recalc
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.chk_rect.collidepoint(mouse_pos):
                    self.opt_auto_play = not self.opt_auto_play

    def draw(self):
        if self.bg_scaled:
             self.screen.blit(self.bg_scaled, (0, 0))
        else:
             self.screen.fill(BG_COLOR)

        if self.state == "main":
            self.draw_main_menu()
        elif self.state == "setup":
            self.draw_setup_screen()
        elif self.state == "load":
            self.draw_load_screen()
        elif self.state == "options":
            self.draw_options_screen()
            
        # Draw Custom Pointer
        if self.pointer_img:
            mx, my = pygame.mouse.get_pos()
            self.screen.blit(self.pointer_img, (mx, my))

    def draw_main_menu(self):
        cx, cy = self.w // 2, self.h // 2
        # Titre
        title = self.font_title.render("MedievAIl BATTLE", True, ACCENT_COLOR)
        title_rect = title.get_rect(center=(cx, cy - 200))
        self.screen.blit(title, title_rect)

        subtitle = self.font_small.render("Simulateur de Batailles Médiévales", True, (0, 0, 0))
        subtitle_rect = subtitle.get_rect(center=(cx, cy - 150))
        self.screen.blit(subtitle, subtitle_rect)

        # Boutons
        self.btn_play.draw(self.screen)
        self.btn_load.draw(self.screen)
        self.btn_options.draw(self.screen)
        self.btn_quit.draw(self.screen)

        # Footer
        footer = self.font_tiny.render(" Python 3 | Pygame", True, (100, 100, 120))
        footer_rect = footer.get_rect(center=(cx, self.h - 20))
        self.screen.blit(footer, footer_rect)

    def draw_setup_screen(self):
        cx, cy = self.w // 2, self.h // 2
        # Titre
        title = self.font_button.render("CONFIGURATION DE LA BATAILLE", True, ACCENT_COLOR)
        title_rect = title.get_rect(center=(cx, 50))
        self.screen.blit(title, title_rect)

        # Labels - Align with the left edge of dropdowns (cx - 200)
        left_align = cx - 200
        labels = [
            ("Équipe A (Bleu)", 200),
            ("Équipe B (Rouge)", 280),
            ("Scénario", 360)
        ]

        for label_text, y in labels:
            label = self.font_small.render(label_text, True, TEXT_COLOR)
            self.screen.blit(label, (left_align, y - 25))

        # Boutons (D'abord pour qu'ils soient couverts par les menus déroulants)
        self.btn_start.draw(self.screen)
        self.btn_back.draw(self.screen)

        # Descriptions IA (Dessinées avant les menus)
        # Position relative to dropdowns
        desc_a = AI_DESCRIPTIONS.get(self.setup_ai_a.get_selected(), "")
        desc_b = AI_DESCRIPTIONS.get(self.setup_ai_b.get_selected(), "")

        desc_a_surf = self.font_tiny.render(desc_a, True, (180, 180, 200))
        desc_b_surf = self.font_tiny.render(desc_b, True, (180, 180, 200))

        self.screen.blit(desc_a_surf, (left_align + 10, 245))
        self.screen.blit(desc_b_surf, (left_align + 10, 325))

        # Dropdowns (Ordre inversé pour que celui du haut dessine PAR DESSUS celui du bas)
        self.setup_scenario.draw(self.screen)
        self.setup_ai_b.draw(self.screen)
        self.setup_ai_a.draw(self.screen)

    def draw_load_screen(self):
        cx = self.w // 2
        # Titre
        title = self.font_button.render("CHARGER UNE PARTIE", True, ACCENT_COLOR)
        title_rect = title.get_rect(center=(cx, 50))
        self.screen.blit(title, title_rect)

        # Liste des sauvegardes
        for i, file in enumerate(self.save_files):
            rect = pygame.Rect(0, 0, 400, 45)
            rect.center = (cx, 150 + i * 50)

            if file == "Aucune sauvegarde trouvée":
                color = (60, 60, 60)
            else:
                mouse_pos = pygame.mouse.get_pos()
                color = BUTTON_HOVER if rect.collidepoint(mouse_pos) else BUTTON_COLOR

            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            pygame.draw.rect(self.screen, TEXT_COLOR, rect, 2, border_radius=5)

            text = self.font_small.render(file, True, TEXT_COLOR)
            text_rect = text.get_rect(midleft=(rect.x + 15, rect.centery))
            self.screen.blit(text, text_rect)

            # Icône
            if file != "Aucune sauvegarde trouvée":
                icon = self.font_small.render("📂", True, ACCENT_COLOR)
                self.screen.blit(icon, (rect.right - 40, rect.centery - 10))

        # Bouton retour
        self.btn_back.draw(self.screen)

        # Info
        info = self.font_tiny.render("Fichiers .pkl dans le dossier du projet", True, (120, 120, 140))
        info_rect = info.get_rect(center=(cx, self.h - 40))
        self.screen.blit(info, info_rect)

    def draw_options_screen(self):
        cx = self.w // 2
        left_align = cx - 200
        # Titre
        title = self.font_button.render("OPTIONS", True, ACCENT_COLOR)
        title_rect = title.get_rect(center=(cx, 50))
        self.screen.blit(title, title_rect)

        # Vitesse de jeu
        label1 = self.font_small.render("Vitesse de simulation", True, TEXT_COLOR)
        self.screen.blit(label1, (left_align, 175))

        # Auto-play
        label2 = self.font_small.render("Démarrer automatiquement", True, TEXT_COLOR)
        self.screen.blit(label2, (left_align + 50, 285))

        # Checkbox (Use self.chk_rect which is updated in recalc)
        pygame.draw.rect(self.screen, BUTTON_COLOR, self.chk_rect, border_radius=4)
        pygame.draw.rect(self.screen, TEXT_COLOR, self.chk_rect, 2, border_radius=4)

        if self.opt_auto_play:
            check_surf = self.font_button.render("✓", True, ACCENT_COLOR)
            check_rect = check_surf.get_rect(center=self.chk_rect.center)
            self.screen.blit(check_surf, check_rect)

        # Dropdown (Dessiné EN DERNIER pour passer au dessus)
        self.opt_speed.draw(self.screen)

        # Bouton retour
        self.btn_back.draw(self.screen)

    def launch_battle(self):
        """Lance la bataille avec les paramètres choisis"""
        ai_a_name = self.setup_ai_a.get_selected()
        ai_b_name = self.setup_ai_b.get_selected()
        scenario_name = self.setup_scenario.get_selected()

        print(f"\n🎮 Lancement de la bataille : {scenario_name}")
        print(f"   Équipe A : {ai_a_name}")
        print(f"   Équipe B : {ai_b_name}\n")

        # Créer le jeu
        scenario_func = AVAILABLE_SCENARIOS[scenario_name]
        game = scenario_func()

        # Remplacer les contrôleurs
        ai_a_class = AVAILABLE_AIS[ai_a_name]
        ai_b_class = AVAILABLE_AIS[ai_b_name]

        game.controllers = {
            "A": ai_a_class("A"),
            "B": ai_b_class("B"),
        }

        # NE PAS FERMER LE MENU (pygame.quit)
        # On lance la bataille dans la même fenêtre
        self.start_battle_window(game)
        
        # Au retour, on recalcule le layout au cas où la résolution ait changé dans la bataille (si redimensionné)
        self.recalc_layout()
        # On ne met PAS self.running = False, ainsi on revient au menu après la bataille

    def load_save(self, filename):
        """Charge une sauvegarde"""
        try:
            with open(filename, "rb") as f:
                game = pickle.load(f)

            print(f"\n📂 Chargement : {filename}")
            print(f"   Temps simulé : {game.time:.1f}s")
            print(f"   Unités en vie : {len(game.alive_units())}\n")

            # Lance dans la même fenêtre
            self.start_battle_window(game)
            self.recalc_layout()

        except Exception as e:
            print(f"❌ Erreur de chargement : {e}")

    def start_battle_window(self, game):
        """Lance la boucle de jeu de la bataille sur l'écran actuel"""
        # On réutilise self.screen
        w, h = self.screen.get_size()
        
        gui = GUI(game, w, h)
        
        # Force re-hide cursor (just in case)
        pygame.mouse.set_visible(False)
        
        auto_play = self.opt_auto_play
        battle_running = True
        clock = pygame.time.Clock()

        print("\n--- CONTRÔLES ---")
        print("[P]               : Lecture / Pause")
        print("[ESPACE]          : Pas à pas")
        print("[Molette]         : Zoomer / Dézoomer")
        print("[Clic]            : Déplacer la caméra")
        print("[M]               : Minimap")
        print("[F11/F12]         : Save/Load rapide")
        print("[ESC]             : Retour menu")
        print("-----------------\n")

        while battle_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Si on ferme la croix, on veut quitter tout le jeu
                    battle_running = False
                    self.running = False # Arrêter aussi le menu
                
                elif event.type == pygame.VIDEORESIZE:
                    # Update screen if resized
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.FULLSCREEN | pygame.RESIZABLE)
                    w, h = event.w, event.h
                    # Notifier la GUI du resize (elle a déjà une méthode handle_events pour ça ?)
                    # Views.py toggle resize manually inside handle_events usually.
                    # Start_battle_window reuses the same event loop style.
                
                gui.handle_events(event)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        auto_play = not auto_play
                    elif event.key == pygame.K_SPACE:
                        game.step(dt=0.1)
                    elif event.key == pygame.K_ESCAPE:
                        battle_running = False # Retour au menu

            if not game.is_finished() and auto_play:
                game.step(dt=0.1)

            # Update GUI dimensions just in case
            gui.screen_w, gui.screen_h = self.screen.get_size()
            
            gui.handle_input()
            gui.draw(self.screen)

            # Overlay de fin
            if game.is_finished():
                winner = game.get_winner()
                font = pygame.font.SysFont("Arial", 36, bold=True)

                if winner is None:
                    text = "MATCH NUL"
                    color = (255, 255, 255)
                else:
                    text = f"VICTOIRE ÉQUIPE {winner}"
                    color = (255, 215, 0)

                cx, cy = self.screen.get_size()
                surf = font.render(text, True, color)
                rect = surf.get_rect(center=(cx // 2, 100))

                bg = pygame.Surface((rect.width + 30, rect.height + 20))
                bg.set_alpha(200)
                bg.fill((0, 0, 0))
                self.screen.blit(bg, bg.get_rect(center=rect.center))
                self.screen.blit(surf, rect)

                # Instruction
                hint_font = pygame.font.SysFont("Arial", 18)
                hint = hint_font.render("Appuyez sur [ESC] pour retourner au menu", True, (200, 200, 200))
                hint_rect = hint.get_rect(center=(cx // 2, 150))
                self.screen.blit(hint, hint_rect)

            pygame.display.flip()
            clock.tick(60)

         # Fin de battle_window, on retourne au menu (qui est dans la boucle run)
        print("Retour au menu...")


def main():
    menu = MainMenu()
    menu.run()


if __name__ == "__main__":
    main()
