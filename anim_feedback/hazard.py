import pygame

class Hazard(pygame.sprite.Sprite):
    def __init__(
        self,
        center: tuple[int, int],
        *,
        color: pygame.Color,
        size: int = 34,
        spin_speed_dps: float = 210.0,
    ) -> None:
        super().__init__()
        self.base = _make_hazard_surface(size, color)
        self.angle = 0.0
        self.spin_speed_dps = spin_speed_dps

        self.image = self.base
        self.rect = self.image.get_rect(center=center)

    def update(self, dt: float) -> None:
        self.angle = (self.angle + self.spin_speed_dps * dt) % 360.0
        center = self.rect.center
        self.image = pygame.transform.rotate(self.base, self.angle)
        self.rect = self.image.get_rect(center=center)

def _make_hazard_surface(size: int, color: pygame.Color) -> pygame.Surface:
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    pts = [
        (cx, 2),
        (size - 2, cy),
        (cx, size - 2),
        (2, cy),
    ]
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.polygon(surf, pygame.Color("#000000"), pts, 2)
    return surf


