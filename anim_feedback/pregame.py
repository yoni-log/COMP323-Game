"""Intro flow: splash start screen, then character selection."""

from __future__ import annotations

from .character_select import run_character_select
from .kenney_character import set_selected_character
from .start_screen import run_start_screen


def run_pregame_sequence() -> None:
    run_start_screen()
    set_selected_character(run_character_select())
