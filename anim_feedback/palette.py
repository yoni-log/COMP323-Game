import pygame
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Palette:
    bg: pygame.Color = field(default_factory=lambda: pygame.Color("#0f0a1e"))
    panel: pygame.Color = field(default_factory=lambda: pygame.Color("#28140a"))
    text: pygame.Color = field(default_factory=lambda: pygame.Color("#ffdc64"))
    subtle: pygame.Color = field(default_factory=lambda: pygame.Color("#b4b4b4"))

    player: pygame.Color = field(default_factory=lambda: pygame.Color("#c87832"))
    coin: pygame.Color = field(default_factory=lambda: pygame.Color("#ffc83c"))
    hazard: pygame.Color = field(default_factory=lambda: pygame.Color("#c83c14"))
    particle: pygame.Color = field(default_factory=lambda: pygame.Color("#ffdc64"))
    wall: pygame.Color = field(default_factory=lambda: pygame.Color("#502a0c"))