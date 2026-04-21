import pygame
from dataclasses import dataclass, field

@dataclass
class Particle:
    pos: pygame.Vector2
    vel: pygame.Vector2
    radius: float
    color: pygame.Color
    life: float
    ttl: float

    def update(self, dt: float) -> None:
        self.life = max(0.0, self.life - dt)
        self.pos += self.vel * dt

    @property
    def alive(self) -> bool:
        return self.life > 0