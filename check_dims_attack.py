import pygame
import os
pygame.init()
paths = [
    "assets/units/crossbowman/attack/crossbowman_attack.webp"
]
for p in paths:
    if os.path.exists(p):
        try:
            img = pygame.image.load(p)
            print(f"{p}: {img.get_width()}x{img.get_height()}")
        except:
            print(f"{p}: Fallback error")
    else:
        print(f"{p}: Not found")
