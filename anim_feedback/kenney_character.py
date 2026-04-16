"""Player-facing Kenney Shape character configuration (color family + body shape + face)."""

from __future__ import annotations

from dataclasses import dataclass

FAMILIES: tuple[str, ...] = ("blue", "green", "yellow", "pink", "purple", "red")
SHAPES: tuple[str, ...] = ("circle", "squircle", "square", "rhombus")

# Full-face textures from spritesheet_default.xml (Kenney Shape Characters)
FACES: tuple[str, ...] = (
    "face_a.png",
    "face_b.png",
    "face_c.png",
    "face_d.png",
    "face_e.png",
    "face_f.png",
    "face_g.png",
    "face_h.png",
    "face_i.png",
    "face_j.png",
    "face_k.png",
    "face_l.png",
)


@dataclass(frozen=True)
class KenneyCharacterChoice:
    family: str = "blue"
    shape: str = "squircle"
    face: str = "face_b.png"

    def __post_init__(self) -> None:
        if self.family not in FAMILIES:
            raise ValueError(f"family must be one of {FAMILIES}")
        if self.shape not in SHAPES:
            raise ValueError(f"shape must be one of {SHAPES}")
        if self.face not in FACES:
            raise ValueError(f"face must be one of {FACES}")


DEFAULT_CHARACTER = KenneyCharacterChoice()

_selected: KenneyCharacterChoice = DEFAULT_CHARACTER


def set_selected_character(choice: KenneyCharacterChoice) -> None:
    global _selected
    _selected = choice


def get_selected_character() -> KenneyCharacterChoice:
    return _selected


def body_texture_key(choice: KenneyCharacterChoice) -> str:
    return f"{choice.family}_body_{choice.shape}.png"
