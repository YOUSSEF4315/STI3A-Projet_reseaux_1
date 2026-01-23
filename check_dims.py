import pygame
import os

pygame.init()
pygame.display.set_mode((100, 100)) # Needed for convert() sometimes, though not strictly for load

paths = [
    "assets/units/Knight/walk/Knight_walk.webp",
    "assets/units/Knight/idle/Knight_idle.webp",
    "assets/units/Knight/attack/Knight_attack.webp",
    "assets/units/Pikeman/walk/Pikeman_walk.webp",
    "assets/units/crossbowman/walk/crossbowman_walk.webp"
]

for p in paths:
    if os.path.exists(p):
        try:
            img = pygame.image.load(p)
            print(f"{p}: {img.get_width()}x{img.get_height()}")
        except Exception as e:
            print(f"{p}: Error {e}")
    else:
        print(f"{p}: Not found")
