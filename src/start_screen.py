import math
import pygame
import random
import sys
from .persistence import get_settings, save_settings

# --- Constants ---
WIDTH, HEIGHT = 900, 600
FPS = 60

# Colors
BG_TOP = (15, 10, 30)
BG_BOTTOM = (40, 20, 10)
TILE_COLORS = [
    (180, 100, 40),
    (160, 80, 30),
    (200, 120, 50),
    (140, 70, 25),
]
CRACK_COLOR = (80, 40, 10)
GAME_YELLOW = (255, 220, 100)  # Matches in-game safe tile yellow.
TITLE_COLOR = GAME_YELLOW
TITLE_SHADOW = (120, 60, 10)
PROMPT_COLOR = (255, 255, 255)
DIM_COLOR = (180, 180, 180)
HIGHLIGHT = GAME_YELLOW

# Lazily created when run_start_screen() runs (never at import time — avoids SDL/macOS crashes)
_screen: pygame.Surface | None = None
_clock: pygame.time.Clock | None = None
font_title: pygame.font.Font | None = None
font_sub: pygame.font.Font | None = None
font_prompt: pygame.font.Font | None = None
font_ctrl: pygame.font.Font | None = None

def _ensure_start_screen_ready() -> None:
    """Create window, clock, and fonts once. Importing this module must not touch video/audio."""
    global _screen, _clock, font_title, font_sub, font_prompt, font_ctrl
    if _screen is not None:
        return
    if not pygame.get_init():
        pygame.init()
    _screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Don't Crumble")
    _clock = pygame.time.Clock()
    font_title = pygame.font.SysFont("impact", 96, bold=False)
    font_sub = pygame.font.SysFont("impact", 28)
    font_prompt = pygame.font.SysFont("couriernew", 22, bold=True)
    font_ctrl = pygame.font.SysFont("couriernew", 18)

# --- Falling Tile Particles ---
class FallingTile:
    def __init__(self, x=None):
        self.reset(x)

    def reset(self, x=None):
        self.w = random.randint(48, 90)
        self.h = random.randint(18, 30)
        self.x = x if x is not None else random.randint(0, WIDTH)
        self.y = random.randint(-HEIGHT, -self.h)
        self.vy = random.uniform(1.5, 4.5)
        self.vx = random.uniform(-0.6, 0.6)
        self.rot = random.uniform(-15, 15)
        self.rot_speed = random.uniform(-1.5, 1.5)
        self.color = random.choice(TILE_COLORS)
        self.alpha = random.randint(160, 230)
        self.cracks = self._gen_cracks()

    def _gen_cracks(self):
        cracks = []
        for _ in range(random.randint(1, 3)):
            sx = random.randint(4, self.w - 4)
            sy = random.randint(4, self.h - 4)
            ex = sx + random.randint(-20, 20)
            ey = sy + random.randint(-10, 10)
            cracks.append((sx, sy, ex, ey))
        return cracks

    def update(self):
        self.y += self.vy
        self.x += self.vx
        self.rot += self.rot_speed
        if self.y > HEIGHT + 60:
            self.reset()

    def draw(self, surface):
        tile_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        pygame.draw.rect(tile_surf, (*self.color, self.alpha), (0, 0, self.w, self.h), border_radius=3)
        pygame.draw.rect(tile_surf, (*CRACK_COLOR, self.alpha), (0, 0, self.w, self.h), 2, border_radius=3)
        for (sx, sy, ex, ey) in self.cracks:
            pygame.draw.line(tile_surf, (*CRACK_COLOR, self.alpha), (sx, sy), (ex, ey), 1)
        rotated = pygame.transform.rotate(tile_surf, self.rot)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)

# --- Background gradient ---
def draw_gradient(surface):
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))

# --- Ground crack line at bottom ---
def draw_ground_cracks(surface, tick):
    base_y = HEIGHT - 60
    crack_points = []
    x = 0
    while x < WIDTH:
        jitter = int(math.sin(x * 0.05 + tick * 0.03) * 6) + random.randint(-2, 2)
        crack_points.append((x, base_y + jitter))
        x += random.randint(8, 20)
    crack_points.append((WIDTH, base_y))
    if len(crack_points) > 1:
        pygame.draw.lines(surface, (100, 55, 15), False, crack_points, 2)
    fill_poly = crack_points + [(WIDTH, HEIGHT), (0, HEIGHT)]
    pygame.draw.polygon(surface, (55, 28, 8), fill_poly)
    tile_w, tile_h = 90, 25
    for col in range(0, WIDTH // tile_w + 1):
        for row in range(0, 3):
            tx = col * tile_w + (row % 2) * (tile_w // 2)
            ty = base_y + row * tile_h + 10
            rect = pygame.Rect(tx, ty, tile_w - 3, tile_h - 3)
            pygame.draw.rect(surface, (80, 42, 12), rect, border_radius=2)
            pygame.draw.rect(surface, (55, 28, 8), rect, 1, border_radius=2)

# --- Title with shake effect ---
def draw_title(surface, tick):
    assert font_title is not None and font_sub is not None
    shake_x = int(math.sin(tick * 0.18) * 2)
    shake_y = int(math.cos(tick * 0.22) * 1.5)
    title_text = "DON'T CRUMBLE"
    shadow = font_title.render(title_text, True, TITLE_SHADOW)
    surface.blit(shadow, (WIDTH // 2 - shadow.get_width() // 2 + shake_x + 5, 130 + shake_y + 6))
    title = font_title.render(title_text, True, TITLE_COLOR)
    surface.blit(title, (WIDTH // 2 - title.get_width() // 2 + shake_x, 130 + shake_y))
    sub = font_sub.render("A SURVIVAL PLATFORMER", True, (200, 140, 60))
    surface.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 238))

# --- Blinking prompt ---
def draw_prompt(surface, tick):
    assert font_prompt is not None
    if (tick // 35) % 2 == 0:
        prompt = font_prompt.render("PRESS  ENTER  TO  START", True, PROMPT_COLOR)
        surface.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 290))

# --- Controls panel ---
CONTROLS = [
    ("MOVE", "WASD or Arrow Keys"), 
    ("DASH", "SHIFT"), 
    ("PAUSE", "P"), 
    ("RESTART LEVEL", "R"), 
    ("RETURN TO TITLE", "T"), 
    ("CREDITS", "C"), 
    ("QUIT", "ESC")
]

def draw_controls(surface):
    assert font_ctrl is not None
    panel_w, panel_h = 360, 210
    panel_x = WIDTH // 2 - panel_w // 2
    panel_y = 340
    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (0, 0, 0, 120), (0, 0, panel_w, panel_h), border_radius=8)
    pygame.draw.rect(panel_surf, (*GAME_YELLOW, 180), (0, 0, panel_w, panel_h), 2, border_radius=8)
    surface.blit(panel_surf, (panel_x, panel_y))
    header = font_ctrl.render("C O N T R O L S", True, HIGHLIGHT)
    surface.blit(header, (panel_x + panel_w // 2 - header.get_width() // 2, panel_y + 10))
    pygame.draw.line(
        surface,
        GAME_YELLOW,
        (panel_x + 20, panel_y + 32),
        (panel_x + panel_w - 20, panel_y + 32),
        1,
    )
    for i, (action, keys) in enumerate(CONTROLS):
        y = panel_y + 44 + i * 22
        action_surf = font_ctrl.render(action, True, DIM_COLOR)
        keys_surf = font_ctrl.render(keys, True, PROMPT_COLOR)
        surface.blit(action_surf, (panel_x + 24, y))
        surface.blit(keys_surf, (panel_x + panel_w - keys_surf.get_width() - 24, y))


def settings_button_rect() -> pygame.Rect:
    size = 36
    margin = 14
    return pygame.Rect(WIDTH - size - margin, margin, size, size)


def draw_settings_button(surface: pygame.Surface) -> None:
    btn = settings_button_rect()
    mouse_over = btn.collidepoint(pygame.mouse.get_pos())
    gear_col = PROMPT_COLOR if mouse_over else DIM_COLOR
    ring_col = HIGHLIGHT if mouse_over else (*GAME_YELLOW, 100)
    fill_col = (255, 255, 255, 50) if mouse_over else (255, 255, 255, 32)
    pygame.draw.circle(surface, fill_col, btn.center, btn.width // 2)
    pygame.draw.circle(surface, ring_col, btn.center, btn.width // 2, 2)

    cx, cy = btn.center
    outer_r = 12
    inner_r = 6
    for i in range(8):
        angle = i * 45
        v = pygame.Vector2(0, -1).rotate(angle)
        p1 = (cx + int(v.x * inner_r), cy + int(v.y * inner_r))
        p2 = (cx + int(v.x * outer_r), cy + int(v.y * outer_r))
        pygame.draw.line(surface, gear_col, p1, p2, 2)
    pygame.draw.circle(surface, gear_col, btn.center, 5, 2)


def draw_settings_popup(surface: pygame.Surface, settings: dict, selected_idx: int) -> None:
    assert font_sub is not None and font_ctrl is not None
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((8, 8, 16, 165))
    surface.blit(overlay, (0, 0))

    rows = [
        f"Music Volume: {int(round(float(settings['music_volume']) * 100))}%",
        f"SFX Volume: {int(round(float(settings['sfx_volume']) * 100))}%",
        f"Screen Shake: {'On' if settings['screen_shake'] else 'Off'}",
        f"Pulse Effects: {'On' if settings['pulse_effects'] else 'Off'}",
    ]
    panel = pygame.Rect(0, 0, 560, 330)
    panel.center = (WIDTH // 2, HEIGHT // 2 + 10)
    panel_surf = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (0, 0, 0, 165), (0, 0, panel.width, panel.height), border_radius=12)
    pygame.draw.rect(panel_surf, (*GAME_YELLOW, 220), (0, 0, panel.width, panel.height), 2, border_radius=12)
    surface.blit(panel_surf, panel.topleft)

    title = font_sub.render("SETTINGS", True, HIGHLIGHT)
    surface.blit(title, title.get_rect(center=(panel.centerx, panel.top + 34)))
    pygame.draw.line(surface, GAME_YELLOW, (panel.left + 28, panel.top + 58), (panel.right - 28, panel.top + 58), 1)

    y = panel.top + 86
    for i, row in enumerate(rows):
        row_rect = pygame.Rect(panel.left + 26, y - 3, panel.width - 52, 38)
        selected = i == selected_idx
        if selected:
            pygame.draw.rect(surface, (255, 220, 100, 34), row_rect, border_radius=6)
            pygame.draw.rect(surface, GAME_YELLOW, row_rect, 1, border_radius=6)
        col = (45, 34, 24) if selected else DIM_COLOR
        text = font_ctrl.render(row, True, col)
        surface.blit(text, (row_rect.left + 12, y + 7))
        y += 50

    footer_1 = font_ctrl.render("Up/Down select  |  Left/Right adjust", True, DIM_COLOR)
    footer_2 = font_ctrl.render("Enter / Esc / O: Back", True, DIM_COLOR)
    surface.blit(footer_1, footer_1.get_rect(center=(panel.centerx, panel.bottom - 38)))
    surface.blit(footer_2, footer_2.get_rect(center=(panel.centerx, panel.bottom - 18)))


# --- Main loop ---
def run_start_screen() -> None:
    _ensure_start_screen_ready()
    assert _screen is not None and _clock is not None

    tiles = [FallingTile() for _ in range(22)]
    tick = 0
    settings = get_settings()
    show_settings = False
    settings_index = 0
    setting_keys = ("music_volume", "sfx_volume", "screen_shake", "pulse_effects")
    while True:
        _clock.tick(FPS)
        tick += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if settings_button_rect().collidepoint(event.pos):
                    show_settings = not show_settings
                    if show_settings:
                        settings_index = 0
                    continue
            if event.type == pygame.KEYDOWN:
                if show_settings:
                    if event.key == pygame.K_UP:
                        settings_index = (settings_index - 1) % len(setting_keys)
                        continue
                    if event.key == pygame.K_DOWN:
                        settings_index = (settings_index + 1) % len(setting_keys)
                        continue
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        key = setting_keys[settings_index]
                        step = 0.05 if event.key == pygame.K_RIGHT else -0.05
                        if key in {"music_volume", "sfx_volume"}:
                            settings[key] = max(0.0, min(1.0, float(settings[key]) + step))
                        else:
                            settings[key] = not bool(settings[key])
                        save_settings(settings)
                        continue
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE, pygame.K_o):
                        save_settings(settings)
                        show_settings = False
                        continue
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return
                if event.key == pygame.K_o:
                    show_settings = not show_settings
                    if show_settings:
                        settings_index = 0
                    continue
                if event.key == pygame.K_ESCAPE:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
        draw_gradient(_screen)
        for tile in tiles:
            tile.update()
            tile.draw(_screen)
        draw_ground_cracks(_screen, tick)
        draw_title(_screen, tick)
        draw_prompt(_screen, tick)
        draw_controls(_screen)
        draw_settings_button(_screen)
        if show_settings:
            draw_settings_popup(_screen, settings, settings_index)
        pygame.display.flip()