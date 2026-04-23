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