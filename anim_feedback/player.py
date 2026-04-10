import pygame

from .animation import Animation
from .game_config import *

class Player(pygame.sprite.Sprite):
    def __init__(self, center: tuple[int, int], *, color: pygame.Color) -> None:
        super().__init__()

        self.anims = _make_player_anims(color)
        self.state = "idle"
        self.prev_state = "idle"

        self.image = self.anims[self.state].image
        self.rect = self.image.get_rect(center=center)

        self.pos = pygame.Vector2(self.rect.center)
        self.vel = pygame.Vector2(0, 0)
        self.speed = PLAYER_SPEED

        self.hp = PLAYER_HEALTH
        self.invincible_for = 0.0

        self.score = 0

        self.collect_for = 0.0
        self.flash_for = 0.0

    @property
    def is_invincible(self) -> bool:
        return self.invincible_for > 0

    def set_state(self, new_state: str) -> None:
        if new_state == self.state:
            return
        self.prev_state = self.state
        self.state = new_state
        self.anims[self.state].reset()

    def trigger_collect(self) -> None:
        self.collect_for = COLLECT_DURATION
        self.set_state("collect")

    def update(self, dt: float) -> None:
        self.anims[self.state].update(dt)
        center = self.rect.center
        self.image = self.anims[self.state].image
        self.rect = self.image.get_rect(center=center)

        if self.collect_for > 0:
            self.collect_for = max(0.0, self.collect_for - dt)
        elif self.invincible_for > 0:
            self.invincible_for = max(0.0, self.invincible_for - dt)
        elif self.flash_for > 0:
            self.flash_for = max(0.0, self.flash_for - dt)

def _make_player_anims(color: pygame.Color) -> dict[str, Animation]:
    idle = [_draw_player_frame(color, leg_phase=0, eye_open=True)]

    run_frames = [
        _draw_player_frame(color, leg_phase=0, eye_open=True),
        _draw_player_frame(color, leg_phase=1, eye_open=True),
        _draw_player_frame(color, leg_phase=2, eye_open=True),
        _draw_player_frame(color, leg_phase=3, eye_open=True),
    ]

    hurt_frames = [
        _draw_player_frame(pygame.Color("#d08770"), leg_phase=0, eye_open=False),
        _draw_player_frame(pygame.Color("#bf616a"), leg_phase=2, eye_open=False),
    ]


    collect = [
        _draw_player_frame(pygame.Color("#e8c173"), leg_phase=0, eye_open=False),
        _draw_player_frame(pygame.Color("#dada29"), leg_phase=1, eye_open=True),
        _draw_player_frame(pygame.Color("#e8c173"), leg_phase=2, eye_open=False),
        _draw_player_frame(pygame.Color("#dada29"), leg_phase=3, eye_open=True),
    ]

    return {
        "idle": Animation(idle, fps=1.0),
        "run": Animation(run_frames, fps=10.0),
        "hurt": Animation(hurt_frames, fps=8.0),
        "collect": Animation(collect, fps=4.0)
    }


def _draw_player_frame(color: pygame.Color, *, leg_phase: int, eye_open: bool) -> pygame.Surface:
    w, h = 44, 44
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    dark = pygame.Color("#1b2229")

    # Torso
    torso = pygame.Rect(0, 0, 16, 20)
    torso.center = (w // 2, h // 2 + 2)
    pygame.draw.rect(surf, color, torso, border_radius=4)
    pygame.draw.rect(surf, dark, torso, 2, border_radius=4)

    # Head
    head_center = (w // 2, torso.top - 8)
    pygame.draw.circle(surf, color, head_center, 7)
    pygame.draw.circle(surf, dark, head_center, 7, 2)

    # Face / eyes (kept simple so it reads as a little person)
    eye_col = dark
    if eye_open:
        pygame.draw.circle(surf, eye_col, (head_center[0] - 2, head_center[1] - 1), 1)
        pygame.draw.circle(surf, eye_col, (head_center[0] + 2, head_center[1] - 1), 1)
    else:
        pygame.draw.line(surf, eye_col, (head_center[0] - 3, head_center[1] - 1), (head_center[0] - 1, head_center[1] - 1), 2)
        pygame.draw.line(surf, eye_col, (head_center[0] + 1, head_center[1] - 1), (head_center[0] + 3, head_center[1] - 1), 2)

    # Legs – two simple blocks that shift slightly with the run cycle
    leg_phase = leg_phase % 4
    base_leg_y = torso.bottom + 1
    step = 3
    left_dx = -3 if leg_phase in {0, 3} else -1
    right_dx = 1 if leg_phase in {0, 1} else 3

    left_leg = pygame.Rect(0, 0, 5, 10)
    right_leg = pygame.Rect(0, 0, 5, 10)
    left_leg.midtop = (w // 2 - step, base_leg_y + left_dx // 2)
    right_leg.midtop = (w // 2 + step, base_leg_y + right_dx // 2)
    pygame.draw.rect(surf, dark, left_leg)
    pygame.draw.rect(surf, dark, right_leg)

    # Arms – simple rectangles angled slightly out
    arm_y = torso.top + 8
    arm_len = 9

    pygame.draw.line(
        surf,
        dark,
        (torso.left - 2, arm_y),
        (torso.left - 2 - arm_len, arm_y + 3),
        3,
    )
    pygame.draw.line(
        surf,
        dark,
        (torso.right + 2, arm_y),
        (torso.right + 2 + arm_len, arm_y + 3),
        3,
    )

    return surf