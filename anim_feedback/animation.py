import pygame
from dataclasses import dataclass, field

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

        sparkle = pygame.Color("#ffffff")
        sparkle.a = 180
        pygame.draw.circle(surf, sparkle, (cx - r // 3, cy - r // 3), max(1, r // 5))

        frames.append(surf)

    return frames