"""Load Kenney Shape Characters spritesheet (CC0) for pygame."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pygame

_SPRITE_OUT: Final[tuple[int, int]] = (44, 44)


def _spritesheet_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "kenney_shape_characters" / "Spritesheet"


@dataclass(frozen=True)
class KenneyShapeAtlas:
    """Cuts frames from spritesheet_default using the bundled TextureAtlas XML."""

    _sheet: pygame.Surface
    _frames: dict[str, pygame.Rect]

    @classmethod
    def try_load(cls) -> KenneyShapeAtlas | None:
        base = _spritesheet_dir()
        png = base / "spritesheet_default.png"
        xml = base / "spritesheet_default.xml"
        if not png.is_file() or not xml.is_file():
            return None
        try:
            sheet = pygame.image.load(str(png)).convert_alpha()
        except pygame.error:
            return None

        tree = ET.parse(xml)
        root = tree.getroot()
        frames: dict[str, pygame.Rect] = {}
        for el in root.findall("SubTexture"):
            name = el.get("name")
            if not name:
                continue
            x = int(el.get("x", "0"))
            y = int(el.get("y", "0"))
            w = int(el.get("width", "0"))
            h = int(el.get("height", "0"))
            if w <= 0 or h <= 0:
                continue
            frames[name] = pygame.Rect(x, y, w, h)

        if not frames:
            return None
        return cls(_sheet=sheet, _frames=frames)

    def has_texture(self, texture_name: str) -> bool:
        return texture_name in self._frames

    def cut(self, texture_name: str) -> pygame.Surface:
        rect = self._frames[texture_name]
        return self._sheet.subsurface(rect).copy()

    def composite(self, body_texture: str, face_texture: str) -> pygame.Surface:
        """Body (80×80) with face centered on the upper area, scaled to game sprite size."""
        body = self.cut(body_texture)
        face = self.cut(face_texture)
        out = body.copy()
        bw, bh = body.get_size()
        fw, fh = face.get_size()
        fx = (bw - fw) // 2
        fy = max(8, int(bh * 0.12))
        out.blit(face, (fx, fy))
        return pygame.transform.smoothscale(out, _SPRITE_OUT)

    def composite_safe(self, body_texture: str, face_texture: str) -> pygame.Surface:
        """Like composite, but never raises if a texture name is missing from the atlas."""
        body_key = body_texture if self.has_texture(body_texture) else "blue_body_squircle.png"
        face_key = face_texture if self.has_texture(face_texture) else "face_b.png"
        return self.composite(body_key, face_key)
