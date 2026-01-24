#!/usr/bin/env python3
"""
menu_windowed.py - Version fenêtrée du menu (plus compatible)

Alternative au menu.py qui démarre en mode fenêtré au lieu du plein écran.
Utile pour le débogage ou si le mode plein écran pose problème.
"""

# Import everything from menu.py
from .menu import *

# Override the MainMenu class to use windowed mode
class MainMenuWindowed(MainMenu):
    def __init__(self):
        pygame.init()

        # Use windowed mode instead of fullscreen
        self.w, self.h = 1280, 720  # 720p resolution
        self.screen = pygame.display.set_mode((self.w, self.h), pygame.RESIZABLE)
        pygame.display.set_caption("MedievAIl Battle - Menu Principal (Windowed)")

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

        # Boutons du menu principal
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


def main():
    """Entry point for windowed menu"""
    menu = MainMenuWindowed()
    menu.run()


if __name__ == "__main__":
    main()
