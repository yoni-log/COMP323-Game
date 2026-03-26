import array
import pygame

# Only square wave tones are supported
class Tone(pygame.mixer.Sound):
    def __init__(self, frequency: int, duration: float, volume: float):
        self.frequency = frequency
        self.duration = duration
        self.volume = volume

        sample_rate = 44100 # Max quality
        max_amplitude = pow(2, 16) # Max volume for 16-bit signed audio
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

        samples = array.array('h', [sample for pair in audio_buffer for sample in pair])
        pygame.mixer.Sound.__init__(self, buffer=samples)
        self.set_volume(volume)