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
    pygame.display.set_caption("Don't Crumble — Choose your character")

    # Fresh display surface avoids stale driver state after the splash screen loop.
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

    clock = pygame.time.Clock()
    atlas = KenneyShapeAtlas.try_load()

    current = get_selected_character()
    fi = FAMILIES.index(current.family)
    si = SHAPES.index(current.shape)
    face_i = FACES.index(current.face) if current.face in FACES else 1

    title_font = pygame.font.SysFont(None, 36)
    body_font = pygame.font.SysFont(None, 26)
    hint_font = pygame.font.SysFont(None, 22)

    bg_top = pygame.Color("#0f0a1e")
    bg_bot = pygame.Color("#28140a")
    text = pygame.Color("#e8d9ca")
    muted = pygame.Color("#bea891")
    accent = pygame.Color("#c9a227")
    panel = pygame.Color("#2d1a14")

    def choice_from_indices() -> KenneyCharacterChoice:
        return KenneyCharacterChoice(
            family=FAMILIES[fi],
            shape=SHAPES[si],
            face=FACES[face_i],
        )

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
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                pygame.event.clear()
                return choice_from_indices()
            if event.key in (pygame.K_LEFT, pygame.K_a):
                fi = (fi - 1) % len(FAMILIES)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                fi = (fi + 1) % len(FAMILIES)
            elif event.key in (pygame.K_UP, pygame.K_w):
                si = (si - 1) % len(SHAPES)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                si = (si + 1) % len(SHAPES)
            elif event.key in (pygame.K_q, pygame.K_LEFTBRACKET):
                face_i = (face_i - 1) % len(FACES)
            elif event.key in (pygame.K_e, pygame.K_RIGHTBRACKET):
                face_i = (face_i + 1) % len(FACES)

        ch = choice_from_indices()
        for y in range(SCREEN_H):
            t = y / max(1, SCREEN_H - 1)
            c = bg_top.lerp(bg_bot, t)
            pygame.draw.line(screen, c, (0, y), (SCREEN_W, y))

        title = title_font.render("Choose your character", True, text)
        screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 56)))

        if atlas is None:
            msg = hint_font.render("Kenney sprites not found — classic drawn player will be used.", True, muted)
            screen.blit(msg, msg.get_rect(center=(SCREEN_W // 2, 100)))
        else:
            fam = body_font.render(f"Color: {FAMILIES[fi].upper()}  (← / →)", True, text)
            shp = body_font.render(f"Shape: {SHAPES[si].upper()}  (↑ / ↓)", True, text)
            face_label = FACES[face_i].replace(".png", "").replace("_", " ").upper()
            fc = body_font.render(f"Face: {face_label}  (Q / E or [ / ])", True, text)
            screen.blit(fam, fam.get_rect(center=(SCREEN_W // 2, 100)))
            screen.blit(shp, shp.get_rect(center=(SCREEN_W // 2, 132)))
            screen.blit(fc, fc.get_rect(center=(SCREEN_W // 2, 164)))

        preview = _preview_surface(atlas, ch)
        pr = preview.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 10))
        pad = pygame.Rect(pr).inflate(24, 24)
        pygame.draw.rect(screen, panel, pad, border_radius=12)
        pygame.draw.rect(screen, accent, pad, 2, border_radius=12)
        screen.blit(preview, pr)

        hints = [
            "Enter — Start Game",
            "Escape — Quit",
        ]
        y0 = SCREEN_H - 88
        for i, line in enumerate(hints):
            s = hint_font.render(line, True, muted)
            screen.blit(s, s.get_rect(center=(SCREEN_W // 2, y0 + i * 28)))

        pygame.display.flip()