"""Intro flow: splash start screen, then character selection."""

from __future__ import annotations

import pygame

from .audio import AudioBank
from .character_select import run_character_select
from .kenney_character import set_selected_character
from .persistence import get_saved_character, save_selected_character
from .start_screen import run_start_screen

def run_pregame_sequence() -> None:
    audio = AudioBank()
    if not pygame.mixer.music.get_busy():
        audio.play_title_screen_music()
    
    # Restore last-used character before showing selector.
    set_selected_character(get_saved_character())
    run_start_screen(audio)
    choice = run_character_select()
    set_selected_character(choice)
    save_selected_character(choice)