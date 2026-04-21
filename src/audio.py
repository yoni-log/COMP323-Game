from __future__ import annotations

import array
import pygame

class SilentTone:
    """Used when pygame.mixer cannot start (common after display/audio device changes on macOS)."""

    def play(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        return None

    def set_volume(self, volume: float) -> None:
        return None

# Only square wave tones are supported
class Tone(pygame.mixer.Sound):
    def __init__(self, frequency: int, duration: float, volume: float):
        self.frequency = frequency
        self.duration = duration
        self.volume = volume

        sample_rate = 44100  # Max quality
        n_samples = int(round(duration * sample_rate))

        audio_buffer = []
        for i in range(n_samples):
            cycle = (i * frequency / sample_rate) % 1.0
            # Square wave generation logic
            if cycle < 0.5:
                value = int(32767 * volume)
            else:
                value = int(-32767 * volume)
            audio_buffer.append([value, value])

        samples = array.array("h", [sample for pair in audio_buffer for sample in pair])
        pygame.mixer.Sound.__init__(self, buffer=samples)
        self.set_volume(volume)

def init_mixer_safe() -> bool:
    """Initialize the mixer if possible; return whether audio is available."""
    if pygame.mixer.get_init() is not None:
        return True
    try:
        pygame.mixer.init()
    except pygame.error:
        return False
    return pygame.mixer.get_init() is not None

def make_tone(frequency: int, duration: float, volume: float) -> Tone | SilentTone:
    """Build a square-wave tone, or a silent stand-in if the mixer is unavailable."""
    if pygame.mixer.get_init() is None:
        try:
            pygame.mixer.init()
        except pygame.error:
            return SilentTone()
    try:
        return Tone(frequency, duration, volume)
    except pygame.error:
        return SilentTone()