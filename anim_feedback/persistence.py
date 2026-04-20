from __future__ import annotations

import json
from pathlib import Path

from .kenney_character import KenneyCharacterChoice

_SAVE_PATH = Path(__file__).resolve().parent.parent / ".dont_crumble_save.json"


def _default_data() -> dict:
    return {
        "selected_character": {
            "family": "blue",
            "shape": "squircle",
            "face": "face_b.png",
        },
        "best_level_reached": 1,
        "best_clear_time_s": None,
    }


def load_progress() -> dict:
    if not _SAVE_PATH.is_file():
        return _default_data()
    try:
        with _SAVE_PATH.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError):
        return _default_data()

    data = _default_data()
    if isinstance(raw, dict):
        data.update(raw)
    return data


def save_progress(data: dict) -> None:
    payload = _default_data()
    payload.update(data)
    try:
        with _SAVE_PATH.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except OSError:
        # Persistence should never crash gameplay.
        return


def get_saved_character() -> KenneyCharacterChoice:
    data = load_progress()
    cfg = data.get("selected_character", {})
    if not isinstance(cfg, dict):
        return KenneyCharacterChoice()
    try:
        return KenneyCharacterChoice(
            family=str(cfg.get("family", "blue")),
            shape=str(cfg.get("shape", "squircle")),
            face=str(cfg.get("face", "face_b.png")),
        )
    except ValueError:
        return KenneyCharacterChoice()


def save_selected_character(choice: KenneyCharacterChoice) -> None:
    data = load_progress()
    data["selected_character"] = {
        "family": choice.family,
        "shape": choice.shape,
        "face": choice.face,
    }
    save_progress(data)


def get_best_level_reached() -> int:
    data = load_progress()
    value = data.get("best_level_reached", 1)
    if not isinstance(value, int):
        return 1
    return max(1, value)


def record_best_level_reached(level: int) -> int:
    best = max(get_best_level_reached(), int(level))
    data = load_progress()
    data["best_level_reached"] = best
    save_progress(data)
    return best


def get_best_clear_time_s() -> float | None:
    data = load_progress()
    value = data.get("best_clear_time_s")
    if isinstance(value, (int, float)) and value > 0:
        return float(value)
    return None


def record_best_clear_time_s(seconds: float) -> float:
    candidate = max(0.0, float(seconds))
    current = get_best_clear_time_s()
    best = candidate if current is None else min(current, candidate)
    data = load_progress()
    data["best_clear_time_s"] = best
    save_progress(data)
    return best
