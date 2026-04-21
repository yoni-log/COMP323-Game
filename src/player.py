import pygame

from .animation import Animation
from .game_config import *
from .kenney_character import KenneyCharacterChoice, get_selected_character
from .kenney_shape_atlas import KenneyShapeAtlas

_kenney_atlas: KenneyShapeAtlas | None = None
_kenney_load_attempted = False


def _get_kenney_atlas() -> KenneyShapeAtlas | None:
    global _kenney_atlas, _kenney_load_attempted
    if _kenney_load_attempted:
        return _kenney_atlas
    _kenney_load_attempted = True
    _kenney_atlas = KenneyShapeAtlas.try_load()
    return _kenney_atlas


class Player(pygame.sprite.Sprite):
    def __init__(
        self,
        center: tuple[int, int],
        *,
        color: pygame.Color,
        character: KenneyCharacterChoice | None = None,
    ) -> None:
        super().__init__()

        self._character = character if character is not None else get_selected_character()

        atlas = _get_kenney_atlas()
        if atlas is not None:
            self.anims = _make_kenney_player_anims(atlas, self._character)
        else:
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


def _make_kenney_player_anims(atlas: KenneyShapeAtlas, choice: KenneyCharacterChoice) -> dict[str, Animation]:
    def _body_or_fallback(family: str, shape: str) -> str:
        key = f"{family}_body_{shape}.png"
        if atlas.has_texture(key):
            return key
        return f"{family}_body_squircle.png"

    body_main = _body_or_fallback(choice.family, choice.shape)
    main_face = choice.face

    idle = [atlas.composite_safe(body_main, main_face)]
    # Single-frame run avoids duplicate composites; movement reads from velocity, not bobbing faces.
    run_frames = [atlas.composite_safe(body_main, main_face) for _ in range(4)]

    hurt_body = _body_or_fallback("red", choice.shape)
    hurt_frames = [
        atlas.composite_safe(hurt_body, "face_h.png"),
        atlas.composite_safe(hurt_body, "face_g.png"),
    ]
    cheer_family = "green" if choice.family == "yellow" else "yellow"
    cheer_body = _body_or_fallback(cheer_family, choice.shape)
    collect_frames = [
        atlas.composite_safe(cheer_body, "face_c.png"),
        atlas.composite_safe(cheer_body, "face_k.png"),
        atlas.composite_safe(cheer_body, "face_c.png"),
        atlas.composite_safe(cheer_body, "face_l.png"),
    ]
    return {
        "idle": Animation(idle, fps=1.0),
        "run": Animation(run_frames, fps=10.0),
        "hurt": Animation(hurt_frames, fps=8.0),
        "collect": Animation(collect_frames, fps=4.0),
    }


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