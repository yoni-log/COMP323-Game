# This file is for testing the difficulty parameters of the game, 
# to see how they scale across levels and to help with tuning them.

print("hazard_speed_mult")   # controls how fast hazards spin
for i in range(2, 11):
    print(f'Level {i}: {round((1.0 + (0.2 * i)), 1)}')

print()
print()

print("_tile_fade_mult")   # controls how quickly the tiles disappear
for i in range(2, 11):
    print(f'Level {i}: {round((1.0 + (0.1 * i)), 1)}')

print()
print()

print("_tile_wave_mult")   # controls when tiles start disappearing
for i in range(2, 11):
    print(f'Level {i}: {round((1.0 + (0.1 * i)), 1)}')