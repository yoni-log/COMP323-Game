import pygame
from .animation import Animation, _make_coin_frames

class Coin(pygame.sprite.Sprite):
    def __init__(
        self,
        center: tuple[int, int],
        *,
        color: pygame.Color,
    ) -> None:
        super().__init__()
        self.anim = Animation(_make_coin_frames(color), fps=10.0)
        self.image = self.anim.image
        self.rect = self.image.get_rect(center=center)

    def update(self, dt: float) -> None:
        self.anim.update(dt)
        center = self.rect.center
        self.image = self.anim.image
        self.rect = self.image.get_rect(center=center)
