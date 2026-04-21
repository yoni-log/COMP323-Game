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

    def update(self, dt: float, *args) -> None:
        self.angle = (self.angle + self.spin_speed_dps * dt) % 360.0
        center = self.rect.center
        self.image = pygame.transform.rotate(self.base, self.angle)
        self.rect = self.image.get_rect(center=center)


class MovingHazard(Hazard):
    def __init__(
        self,
        center: tuple[int, int],
        *,
        color: pygame.Color,
        size: int = 34,
        spin_speed_dps: float = 210.0,
        speed: float = 140.0,
    ) -> None:
        super().__init__(center, color=color, size=size, spin_speed_dps=spin_speed_dps)
        # Give moving hazards a unique silhouette so players can identify them instantly.
        self.base = _make_moving_hazard_surface(size, color)
        self.image = self.base
        self.rect = self.image.get_rect(center=center)
        self.pos = pygame.Vector2(self.rect.center)
        self.vel = pygame.Vector2(speed, 0)

    def _collides_walls(self, walls: pygame.sprite.Group) -> bool:
        return any(self.rect.colliderect(w.rect) for w in walls)

    def update(
        self,
        dt: float,
        walls: pygame.sprite.Group | None = None,
        playfield: pygame.Rect | None = None,
    ) -> None:
        if walls is None or playfield is None:
            super().update(dt)
            return

        self.pos.x += self.vel.x * dt
        self.rect.centerx = int(round(self.pos.x))
        if self._collides_walls(walls) or not playfield.contains(self.rect):
            self.vel.x *= -1.0
            self.pos.x += self.vel.x * dt
            self.rect.centerx = int(round(self.pos.x))

        self.pos.y += self.vel.y * dt
        self.rect.centery = int(round(self.pos.y))
        if self._collides_walls(walls) or not playfield.contains(self.rect):
            self.vel.y *= -1.0
            self.pos.y += self.vel.y * dt
            self.rect.centery = int(round(self.pos.y))

        # Add occasional vertical sway to avoid perfectly straight paths.
        if abs(self.vel.y) < 1.0:
            self.vel.y = 60.0 if (int(self.pos.x) // 40) % 2 == 0 else -60.0

        super().update(dt)

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


def _make_moving_hazard_surface(size: int, color: pygame.Color) -> pygame.Surface:
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    r_outer = size // 2 - 2
    r_inner = max(4, r_outer - 8)

    # Distinct shape: six-point star (instead of the original diamond).
    pts: list[tuple[int, int]] = []
    for i in range(12):
        ang = i * (3.14159265 / 6.0)
        r = r_outer if i % 2 == 0 else r_inner
        x = int(round(cx + r * pygame.math.Vector2(1, 0).rotate_rad(ang).x))
        y = int(round(cy + r * pygame.math.Vector2(1, 0).rotate_rad(ang).y))
        pts.append((x, y))

    pygame.draw.polygon(surf, color, pts)
    pygame.draw.polygon(surf, pygame.Color("#101015"), pts, 2)

    # Center marker increases readability during motion.
    pygame.draw.circle(surf, pygame.Color("#f3e7cf"), (cx, cy), max(2, size // 7))
    pygame.draw.circle(surf, pygame.Color("#101015"), (cx, cy), max(2, size // 7), 1)
    return surf