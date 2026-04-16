import pygame

from .game_config import *

class Wall(pygame.sprite.Sprite):
    def __init__(self, rect: pygame.Rect, color: pygame.Color) -> None:
        super().__init__()
        self.rect = rect.copy()
        self.color = color

TILE_SIZE = 20

# dictionary for the characters in the level design files
TILES = {
    ".": "empty", 
    "C": "coin", 
    "D": "dash", 
    "H": "hazard", 
    "E": "heart", 
    "P": "player_spawn", 
    "W": "wall"
}

# Original level system, not using anymore
'''
LEVELS = [
    # Level 1
    {
        "walls": [
            (180, 110, 18, 240), 
            (420, 40, 18, 240), 
            (560, 240, 260, 18), 
            (900, 80, 18, 200), 
            (1000, 160, 220, 18), 
            (1300, 100, 18, 280), 
            (1600, 60, 260, 18), 
            (1900, 180, 18, 200), 
            (2100, 240, 220, 18), 
            (2450, 80, 18, 260)
        ],
        "hazards": [
            (380, -80, 210.0), 
            (750, 120, 260.0), 
            (1150, 100, 210.0), 
            (1550, 80, 260.0), 
            (1950, -60, 210.0), 
            (2350, 100, 260.0)
        ],
        "coins": TARGET_SCORE
    }
]
'''