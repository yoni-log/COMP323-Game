import math
import pygame

class Animation:
    def __init__(self, frames: list[pygame.Surface], *, fps: float) -> None:
        if not frames:
            raise ValueError("Animation needs at least 1 frame")
        self.frames = frames
        self.frame_dt = 1.0 / fps
        self.t = 0.0
        self.i = 0

    def reset(self) -> None:
        self.t = 0.0
        self.i = 0

    def update(self, dt: float) -> None:
        self.t += dt
        while self.t >= self.frame_dt:
            self.t -= self.frame_dt
            self.i = (self.i + 1) % len(self.frames)

    @property
    def image(self) -> pygame.Surface:
        return self.frames[self.i]
    
def _make_coin_frames(color: pygame.Color) -> list[pygame.Surface]:
    frames: list[pygame.Surface] = []

    for i in range(6):
        pulse = 1.0 + 0.08 * (1.0 if i % 2 == 0 else -1.0)
        w = int(round(26 * pulse))
        h = int(round(26 * pulse))

        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        r = min(cx, cy) - 2

        pygame.draw.circle(surf, color, (cx, cy), r)
        pygame.draw.circle(surf, pygame.Color("#000000"), (cx, cy), r, 2)
        # Coin marker: vertical notch for quick recognition.
        pygame.draw.rect(surf, pygame.Color("#2a1b0a"), pygame.Rect(cx - 2, cy - r // 2, 4, r), border_radius=2)

        sparkle = pygame.Color("#ffffff")
        sparkle.a = 180
        pygame.draw.circle(surf, sparkle, (cx - r // 3, cy - r // 3), max(1, r // 5))

        frames.append(surf)

    return frames

def _make_dash_power_up_frames(color: pygame.Color) -> list[pygame.Surface]:
    frames: list[pygame.Surface] = []

    for i in range(6):
        pulse = 1.0 + 0.08 * (1.0 if i % 2 == 0 else -1.0)
        w = int(round(26 * pulse))
        h = int(round(26 * pulse))

        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        r = min(cx, cy) - 2

        # Triangle points (equilateral triangle pointing up)
        points = [
            (cx, cy - r),
            (cx + r, cy + r),
            (cx - r, cy + r)
        ]
        pygame.draw.polygon(surf, color, points)
        pygame.draw.polygon(surf, pygame.Color("#000000"), points, 2)
        # Dash marker: lightning-styled slash.
        bolt = [
            (cx - 2, cy - r + 4),
            (cx + 2, cy - r + 4),
            (cx - 1, cy + 1),
            (cx + 3, cy + 1),
            (cx - 3, cy + r - 3),
            (cx - 1, cy + 2),
            (cx - 4, cy + 2),
        ]
        pygame.draw.polygon(surf, pygame.Color("#ffffff"), bolt)

        sparkle = pygame.Color("#ffffff")
        sparkle.a = 180
        pygame.draw.circle(surf, sparkle, (cx - r // 3, cy - r // 3), max(1, r // 5))

        frames.append(surf)

    return frames

def _make_heart_frames(color:pygame.Color) -> list[pygame.Surface]:
    frames: list[pygame.Surface] = []

    for i in range(6):
        pulse = 1.0 + 0.08 * (1.0 if i % 2 == 0 else -1.0)
        w = int(round(26 * pulse))
        h = int(round(26 * pulse))

        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        r = min(cx, cy) - 2

        points = []
        for i in range(0, 361):
            angle = math.radians(i)

            x = 16 * math.sin(angle) ** 3
            y = 13 * math.cos(angle) - 5 * math.cos(2 * angle) - 2 * math.cos(3 * angle) - math.cos(4 * angle)
            
            points.append((cx + int(x * r / 16), cy - int(y * r / 13)))

        pygame.draw.polygon(surf, color, points)
        pygame.draw.polygon(surf, pygame.Color("#000000"), points, 2)
        # Health marker: white plus sign.
        plus_w = max(1, r // 4)
        pygame.draw.rect(surf, pygame.Color("#ffffff"), pygame.Rect(cx - plus_w // 2, cy - r // 2, plus_w, r))
        pygame.draw.rect(surf, pygame.Color("#ffffff"), pygame.Rect(cx - r // 2, cy - plus_w // 2, r, plus_w))

        sparkle = pygame.Color("#ffffff")
        sparkle.a = 180
        pygame.draw.circle(surf, sparkle, (cx - r // 3, cy - r // 3), max(1, r // 5))

        frames.append(surf)

    return frames