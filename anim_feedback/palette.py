import pygame
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Palette:
    bg: pygame.Color = field(default_factory = lambda: pygame.Color("#0f0a1e"))
    panel: pygame.Color = field(default_factory = lambda: pygame.Color("#28140a"))
    
    # High-contrast, readable UI colors for in-game text
    text: pygame.Color = field(default_factory = lambda: pygame.Color("#fdf9f0"))
    subtle: pygame.Color = field(default_factory = lambda: pygame.Color("#d0c8b8"))

    # Softer overlay / menu text (matches warm panel tones, easier on the eyes)
    menu_text: pygame.Color = field(default_factory = lambda: pygame.Color("#e8d9ca"))
    menu_muted: pygame.Color = field(default_factory = lambda: pygame.Color("#bea891"))
    menu_shadow: pygame.Color = field(default_factory = lambda: pygame.Color("#1a0f14"))
    menu_panel: pygame.Color = field(default_factory = lambda: pygame.Color("#2d1a14"))
    menu_panel_border: pygame.Color = field(default_factory = lambda: pygame.Color("#5a3824"))

    player: pygame.Color = field(default_factory = lambda: pygame.Color("#5faad0"))
    coin: pygame.Color = field(default_factory = lambda: pygame.Color("#cd7f32"))
    dash_power_up: pygame.Color = field(default_factory = lambda: pygame.Color("#5faad0"))
    hazard: pygame.Color = field(default_factory = lambda: pygame.Color("#c83c14"))
    heart: pygame.Color = field(default_factory = lambda: pygame.Color("#e74c3c"))
    particle: pygame.Color = field(default_factory = lambda: pygame.Color("#5faad0"))
    wall: pygame.Color = field(default_factory = lambda: pygame.Color("#654321"))
    finish_wall: pygame.Color = field(default_factory = lambda: pygame.Color("#ffffff"))