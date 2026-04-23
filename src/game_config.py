# Dimensions
SCREEN_W, SCREEN_H = 900, 600
WORLD_W = 2880
HUD_H = 56
PADDING = 12
FPS = 60

# Player values
PLAYER_HEALTH = 3
PLAYER_SPEED = 320
INVINCIBLE_FOR = 3.0
COLLECT_DURATION = 0.5
FLASH_DURATION = 0.18        # controls player hit animation
DASH_DURATION = 1.5          # controls how long player dashes when using a dash power-up

# Tile spawning
TILE_SIZE = 64
FADE_DURATION = 1.25         # seconds from crumble start to fully black
DEADLY_AT = 0.5              # fade progress at which tile starts hurting the player

# Increases each time the player levels up
L2_HAZARD_SPEED_MULT = 0.2   # controls how fast hazards spin
L2_TILE_FADE_MULT = 0.1      # controls how quickly the tiles disappear
L2_TILE_WAVE_MULT = 0.1      # controls when tiles start disappearing

# Inner right wall is 16px; player must reach this zone to count as "exit"
EXIT_RIGHT_MARGIN = 22