import pygame
import os

def load_and_slice(path, rows, cols, final_size):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    
    try:
        sheet = pygame.image.load(path)
        sheet_w, sheet_h = sheet.get_size()
        frame_w = sheet_w // cols
        frame_h = sheet_h // rows
        
        print(f"Sheet: {sheet_w}x{sheet_h}. Frame: {frame_w}x{frame_h}")
        
        # Slice first frame (Row 0, Col 0)
        rect = pygame.Rect(0, 0, frame_w, frame_h)
        sub = sheet.subsurface(rect)
        scaled = pygame.transform.scale(sub, final_size)
        
        pygame.image.save(scaled, "test_frame_0_0.png")
        print("Saved test_frame_0_0.png")
        
        # Slice middle frame (Row 4, Col 7)
        rect2 = pygame.Rect(7*frame_w, 4*frame_h, frame_w, frame_h)
        sub2 = sheet.subsurface(rect2)
        scaled2 = pygame.transform.scale(sub2, final_size)
        pygame.image.save(scaled2, "test_frame_4_7.png")
        print("Saved test_frame_4_7.png")
        
    except Exception as e:
        print(f"Error: {e}")

pygame.init()
pygame.display.set_mode((100,100))
load_and_slice("assets/units/Knight/walk/Knight_walk.webp", 8, 15, (100, 100))
