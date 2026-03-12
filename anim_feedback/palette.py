import pygame
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Palette:
    bg: pygame.Color = field(default_factory=lambda: pygame.Color("#0f0a1e"))
    panel: pygame.Color = field(default_factory=lambda: pygame.Color("#28140a"))
    # High-contrast, readable UI colors for in-game text
    text: pygame.Color = field(default_factory=lambda: pygame.Color("#fdf9f0"))
    subtle: pygame.Color = field(default_factory=lambda: pygame.Color("#d0c8b8"))

    # Neutral, generic player color
    player: pygame.Color = field(default_factory=lambda: pygame.Color("#5faad0"))
    coin: pygame.Color = field(default_factory=lambda: pygame.Color("#ffc83c"))
    hazard: pygame.Color = field(default_factory=lambda: pygame.Color("#c83c14"))
    particle: pygame.Color = field(default_factory=lambda: pygame.Color("#ffdc64"))
    wall: pygame.Color = field(default_factory=lambda: pygame.Color("#502a0c"))