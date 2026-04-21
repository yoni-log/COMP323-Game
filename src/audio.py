from __future__ import annotations

import array
import pygame
import os

snd_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sounds")

class AudioBank:
    def __init__(self) -> None:
        self.enabled = False
        self.music_muted = False
        self.sfx_muted = False

        self.music_volume = 0.16
        self.sfx_volume = 0.32

        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._loop_channel: pygame.mixer.Channel | None = None

        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency = 22050, size = -16, channels = 2)

            pygame.mixer.set_num_channels(8)
            self._loop_channel = pygame.mixer.Channel(0)
            self.enabled = True
            self._build_sounds()
            self._apply_volumes()
        except pygame.error:
            self.enabled = False

    def _build_sounds(self) -> None:
        self._sounds = {
            "coin_pickup": self._make_tone(880, 0.05, 0.20), 
            "dash_power_up_pickup": self._make_tone(1250, 0.06, 0.22), 
            "heart_pickup": self._make_tone(720, 0.09, 0.24), 
            "player_hit": self._make_tone(150, 0.18, 0.28), 
            "level_cleared": self._make_tone(980, 0.12, 0.24), 
            "level_cleared_2": self._make_tone(1320, 0.10, 0.22), 
            "game_over": self._make_tone(1000, 0.20, 0.20), 
        }
        self._music_tracks = {
            "title_screen_loop": os.path.join(snd_dir, "title_screen_loop.wav"), 
            "title_state_loop": os.path.join(snd_dir, "title_state_loop.mp3"), 
            "gameplay_loop": os.path.join(snd_dir, "gameplay_loop.mp3"), 
            "game_over_loop": os.path.join(snd_dir, "game_over_loop.ogg"), 
            "pause_music_loop": os.path.join(snd_dir, "pause_music_loop.ogg"),
            "level_cleared_won_loop": os.path.join(snd_dir, "level_cleared_won_loop.mp3")
        }
        self._current_music: str | None = None

    @staticmethod
    def _make_tone(frequency: int, duration: float, volume: float) -> Tone | SilentTone:
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

    def _apply_volumes(self) -> None:
        if not self.enabled:
            return

        if self._loop_channel is not None:
            self._loop_channel.set_volume(0.0 if self.music_muted else self.music_volume)

        if self._current_music == "gameplay_loop":
            volume = 0.0 if self.music_muted else self.music_volume * 0.25
        elif self._current_music == "level_cleared_won_loop":
            volume = 0.0 if self.music_muted else self.music_volume * 0.5
        else:
            volume = 0.0 if self.music_muted else self.music_volume
        pygame.mixer.music.set_volume(volume)

        for name, sound in self._sounds.items():
            if name.endswith("_loop"):
                volume = 0.0 if self.music_muted else self.music_volume
            else:
                volume = 0.0 if self.sfx_muted else self.sfx_volume
            
            sound.set_volume(volume)

    def toggle_music_mute(self) -> None:
        self.music_muted = not self.music_muted
        self._apply_volumes()

    def toggle_sfx_mute(self) -> None:
        self.sfx_muted = not self.sfx_muted
        self._apply_volumes()

    def play(self, name: str) -> None:
        if not self.enabled:
            return

        if self.sfx_muted:
            return

        sound = self._sounds.get(name)
        if sound is not None:
            sound.play()

    def play_loop(self, name: str) -> None:
        if not self.enabled or self._loop_channel is None:
            return

        if self.music_muted:
            return

        sound = self._sounds.get(name)
        if sound is None:
            return

        if self._loop_channel.get_sound() is sound:
            return

        self._loop_channel.stop()
        self._loop_channel.play(sound, loops=-1)
        self._apply_volumes()

    def _play_music(self, track_key: str) -> None:
        if not self.enabled:
            return
        if self._current_music == track_key:
            return
        path = self._music_tracks.get(track_key)
        if path is None:
            return
        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.load(path)
            if track_key == "gameplay_loop":
                volume = 0.0 if self.music_muted else self.music_volume * 0.25
            elif track_key == "level_cleared_won_loop":
                volume = 0.0 if self.music_muted else self.music_volume * 0.5
            else:
                volume = 0.0 if self.music_muted else self.music_volume
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1)
            self._current_music = track_key
        except pygame.error:
            self._current_music = None

    def play_title_screen_music(self) -> None:
        self._play_music("title_screen_loop")
    
    def play_title_state_music(self) -> None:
        self._play_music("title_state_loop")
    
    def play_gameplay_music(self) -> None:
        self._play_music("gameplay_loop")
    
    def play_game_over_music(self) -> None:
        self._play_music("game_over_loop")

    def play_pause_music(self) -> None:
        self._play_music("pause_music_loop")

    def play_level_cleared_won_music(self) -> None:
        self._play_music("level_cleared_won_loop")

    def stop_music(self) -> None:
        pygame.mixer.music.stop()
        self._current_music = None

    def shutdown(self) -> None:
        if self.enabled:
            self.stop_loop()

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