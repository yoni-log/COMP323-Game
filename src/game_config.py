# Dimensions
SCREEN_W, SCREEN_H = 900, 600
WORLD_W = 2880
HUD_H = 56
PADDING = 12
FPS = 60

# Player values
PLAYER_HEALTH = 100
PLAYER_SPEED = 320
INVINCIBLE_FOR = 3.0
COLLECT_DURATION = 0.5
FLASH_DURATION = 0.18     # controls player hit animation
DASH_DURATION = 1.5

# Tile spawning
TILE_SIZE = 64
FADE_DURATION = 1.25      # seconds from crumble start to fully black
DEADLY_AT = 0.5           # fade progress at which tile starts hurting the player

# Target score and tile spawning variables should change 
# to increase the game's difficulty as the player levels up

# From level 2 onward: faster hazards and crumbling floor
L2_HAZARD_SPEED_MULT = 1.55
L2_TILE_FADE_MULT = 1.05
L2_TILE_WAVE_MULT = 1.2
# Inner right wall is 16px; player must reach this zone to count as "exit"
EXIT_RIGHT_MARGIN = 22