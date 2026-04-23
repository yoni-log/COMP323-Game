"""Choose Kenney Shape character (color + shape + face) before gameplay."""

from __future__ import annotations

import sys

import pygame

from .game_config import FPS, SCREEN_H, SCREEN_W
from .kenney_character import (
    FACES,
    FAMILIES,
    SHAPES,
    KenneyCharacterChoice,
    body_texture_key,
    get_selected_character,
)
from .kenney_shape_atlas import KenneyShapeAtlas

from .start_screen import run_start_screen


def _preview_surface(atlas: KenneyShapeAtlas | None, choice: KenneyCharacterChoice) -> pygame.Surface:
    if atlas is None:
        surf = pygame.Surface((88, 88), pygame.SRCALPHA)
        surf.fill((40, 30, 55, 220))
        pygame.draw.rect(surf, (180, 150, 120), surf.get_rect(), 2, border_radius=8)
        return surf
    key = body_texture_key(choice)
    if not atlas.has_texture(key):
        key = f"{choice.family}_body_squircle.png"
    img = atlas.composite_safe(key, choice.face)
    return pygame.transform.smoothscale(img, (88, 88))


def run_character_select() -> KenneyCharacterChoice:
    """
    Blocks until the player confirms with Enter.
    On window close or Escape, exits the process (same as the splash screen).
    """
    pygame.display.set_caption("Don't Crumble")

    # Fresh display surface avoids stale driver state after the splash screen loop.
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

    clock = pygame.time.Clock()
    atlas = KenneyShapeAtlas.try_load()

    current = get_selected_character()
    fi = FAMILIES.index(current.family)
    si = SHAPES.index(current.shape)
    face_i = FACES.index(current.face) if current.face in FACES else 1

    title_font = pygame.font.SysFont(None, 42)
    body_font = pygame.font.SysFont(None, 28)
    hint_font = pygame.font.SysFont(None, 22)
    tiny_font = pygame.font.SysFont(None, 20)

    bg_top = pygame.Color("#0f0a1e")
    bg_bot = pygame.Color("#28140a")
    text = pygame.Color("#f3eadc")
    muted = pygame.Color("#c6b29a")
    accent = pygame.Color("#ffdc64")
    panel = pygame.Color("#2a1812")
    panel_soft = pygame.Color("#1c1218")

    active_row = 0

    def choice_from_indices() -> KenneyCharacterChoice:
        return KenneyCharacterChoice(
            family=FAMILIES[fi],
            shape=SHAPES[si],
            face=FACES[face_i],
        )

    def _change_active_row(direction: int) -> None:
        nonlocal active_row
        active_row = (active_row + direction) % 3

    def _adjust_current_value(direction: int) -> None:
        nonlocal fi, si, face_i
        if active_row == 0:
            fi = (fi + direction) % len(FAMILIES)
        elif active_row == 1:
            si = (si + direction) % len(SHAPES)
        else:
            face_i = (face_i + direction) % len(FACES)

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type != pygame.KEYDOWN:
                continue
            if event.key in (pygame.K_ESCAPE,):
                pygame.quit()
                sys.exit(0)
            if event.key == pygame.K_t:
                run_start_screen()
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                pygame.event.clear()
                return choice_from_indices()
            if event.key in (pygame.K_UP, pygame.K_w):
                _change_active_row(-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                _change_active_row(1)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                _adjust_current_value(-1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                _adjust_current_value(1)
            elif event.key in (pygame.K_q, pygame.K_LEFTBRACKET):
                face_i = (face_i - 1) % len(FACES)
            elif event.key in (pygame.K_e, pygame.K_RIGHTBRACKET):
                face_i = (face_i + 1) % len(FACES)

        ch = choice_from_indices()
        for y in range(SCREEN_H):
            t = y / max(1, SCREEN_H - 1)
            c = bg_top.lerp(bg_bot, t)
            pygame.draw.line(screen, c, (0, y), (SCREEN_W, y))

        title = title_font.render("Choose Your Character", True, text)
        screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 50)))
        subtitle = tiny_font.render("Pick a style before you start", True, muted)
        screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_W // 2, 76)))

        if atlas is None:
            msg = hint_font.render("Kenney sprites not found — classic drawn player will be used.", True, muted)
            screen.blit(msg, msg.get_rect(center=(SCREEN_W // 2, 102)))

        left_panel = pygame.Rect(80, 110, 360, 320)
        right_panel = pygame.Rect(470, 110, 350, 320)
        pygame.draw.rect(screen, panel_soft, left_panel, border_radius = 12)
        pygame.draw.rect(screen, accent, left_panel, 2, border_radius = 12)
        pygame.draw.rect(screen, panel_soft, right_panel, border_radius = 12)
        pygame.draw.rect(screen, accent, right_panel, 2, border_radius = 12)

        header_left = hint_font.render("SELECTION", True, accent)
        screen.blit(header_left, (left_panel.left + 18, left_panel.top + 14))
        header_right = hint_font.render("PREVIEW", True, accent)
        screen.blit(header_right, (right_panel.left + 18, right_panel.top + 14))

        face_label = FACES[face_i].replace(".png", "").replace("_", " ").upper()
        rows = [
            ("COLOR", FAMILIES[fi].upper()),
            ("SHAPE", SHAPES[si].upper()),
            ("FACE", face_label),
        ]
        y = left_panel.top + 52
        for idx, (label, value) in enumerate(rows):
            row_rect = pygame.Rect(left_panel.left + 16, y, left_panel.width - 32, 76)
            selected = idx == active_row
            if selected:
                pygame.draw.rect(screen, pygame.Color(255, 220, 100, 36), row_rect, border_radius = 8)
                pygame.draw.rect(screen, accent, row_rect, 1, border_radius = 8)
            else:
                pygame.draw.rect(screen, pygame.Color(0, 0, 0, 55), row_rect, border_radius = 8)

            label_s = tiny_font.render(label, True, muted if not selected else accent)
            value_s = body_font.render(value, True, text)
            screen.blit(label_s, (row_rect.left + 12, row_rect.top + 10))
            screen.blit(value_s, (row_rect.left + 12, row_rect.top + 36))
            y += 90

        preview = _preview_surface(atlas, ch)
        preview = pygame.transform.smoothscale(preview, (140, 140))
        pr = preview.get_rect(center=(right_panel.centerx, right_panel.top + 140))
        pad = pygame.Rect(pr).inflate(26, 26)
        pygame.draw.rect(screen, panel, pad, border_radius = 12)
        pygame.draw.rect(screen, accent, pad, 2, border_radius = 12)
        screen.blit(preview, pr)

        code_line = tiny_font.render(
            f"{FAMILIES[fi].upper()} / {SHAPES[si].upper()} / {face_label}",
            True,
            muted,
        )
        screen.blit(code_line, code_line.get_rect(center = (right_panel.centerx, right_panel.top + 246)))

        quick_hint = tiny_font.render("Q/E or [ ] to cycle face quickly", True, muted)
        screen.blit(quick_hint, quick_hint.get_rect(center = (right_panel.centerx, right_panel.top + 276)))

        hints = [
            "Up/Down: Choose Field   Left/Right: Change Value",
            "Enter: Start Game   T: Return to Title   Esc: Quit",
        ]
        y0 = SCREEN_H - 72
        for i, line in enumerate(hints):
            s = hint_font.render(line, True, muted)
            screen.blit(s, s.get_rect(center=(SCREEN_W // 2, y0 + i * 28)))

        pygame.display.flip()