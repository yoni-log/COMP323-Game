import random
import pygame
from dataclasses import dataclass

TILE_SIZE = 64
FADE_DURATION = 1.25  # seconds from crumble start to fully black
DEADLY_AT = 0.5       # fade progress at which tile starts hurting the player


@dataclass
class FloorTile:
    rect: pygame.Rect
    crumble_at: float   # elapsed seconds when this tile starts fading
    fade: float = 0.0   # 0.0 = normal panel color, 1.0 = fully black

    @property
    def is_deadly(self) -> bool:
        return self.fade >= DEADLY_AT


class TileManager:
    def __init__(
        self,
        playfield: pygame.Rect,
        *,
        panel_color: pygame.Color,
        rng: random.Random,
    ) -> None:
        self.panel_color = panel_color
        self.tiles: list[FloorTile] = []
        self._elapsed = 0.0

        span = max(1, playfield.width - TILE_SIZE)
        for ty in range(playfield.top, playfield.bottom, TILE_SIZE):
            for tx in range(playfield.left, playfield.right, TILE_SIZE):
                x_norm = (tx - playfield.left) / span
                # Left tiles crumble at ~6 s, right tiles at ~100 s
                crumble_at = 3.0 + x_norm * 47.0 + rng.uniform(-1.0, 1.0)
                self.tiles.append(FloorTile(
                    rect=pygame.Rect(tx, ty, TILE_SIZE, TILE_SIZE),
                    crumble_at=crumble_at,
                ))

    def update(self, dt: float) -> None:
        self._elapsed += dt
        for tile in self.tiles:
            if self._elapsed >= tile.crumble_at:
                tile.fade = min(1.0, tile.fade + dt / FADE_DURATION)

    def draw(self, surface: pygame.Surface, cam: tuple[int, int]) -> None:
        # Bright base color for tiles so they contrast clearly with the darker border
        base = pygame.Color("#ffdc64")
        sw = surface.get_width()
        for tile in self.tiles:
            screen_rect = tile.rect.move(cam)
            # skip tiles fully outside the viewport
            if screen_rect.right < 0 or screen_rect.left > sw:
                continue
            f = tile.fade
            # Fade from bright yellow to black as the tile crumbles
            r = int(base.r * (1.0 - f))
            g = int(base.g * (1.0 - f))
            b = int(base.b * (1.0 - f))
            pygame.draw.rect(surface, (r, g, b), screen_rect)
            # Use the panel color as a consistent darker border for clear separation
            border = (self.panel_color.r, self.panel_color.g, self.panel_color.b)
            pygame.draw.rect(surface, border, screen_rect, 1)
