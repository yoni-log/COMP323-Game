import pygame
import random
import math
import sys


pygame.init()


# --- Constants ---
WIDTH, HEIGHT = 900, 600
FPS = 60


# Colors
BG_TOP       = (15, 10, 30)
BG_BOTTOM    = (40, 20, 10)
TILE_COLORS  = [
   (180, 100, 40),
   (160, 80,  30),
   (200, 120, 50),
   (140, 70,  25),
]
CRACK_COLOR  = (80, 40, 10)
TITLE_COLOR  = (255, 220, 100)
TITLE_SHADOW = (120, 60, 10)
PROMPT_COLOR = (255, 255, 255)
DIM_COLOR    = (180, 180, 180)
HIGHLIGHT    = (255, 200, 60)


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Don't Crumble")
clock = pygame.time.Clock()


# --- Fonts ---
font_title  = pygame.font.SysFont("impact", 96, bold=False)
font_sub    = pygame.font.SysFont("impact", 28)
font_prompt = pygame.font.SysFont("couriernew", 22, bold=True)
font_ctrl   = pygame.font.SysFont("couriernew", 18)


# --- Falling Tile Particles ---
class FallingTile:
   def __init__(self, x=None):
       self.reset(x)


   def reset(self, x=None):
       self.w = random.randint(48, 90)
       self.h = random.randint(18, 30)
       self.x = x if x is not None else random.randint(0, WIDTH)
       self.y = random.randint(-HEIGHT, -self.h)
       self.vy = random.uniform(1.5, 4.5)
       self.vx = random.uniform(-0.6, 0.6)
       self.rot = random.uniform(-15, 15)
       self.rot_speed = random.uniform(-1.5, 1.5)
       self.color = random.choice(TILE_COLORS)
       self.alpha = random.randint(160, 230)
       self.cracks = self._gen_cracks()


   def _gen_cracks(self):
       cracks = []
       for _ in range(random.randint(1, 3)):
           sx = random.randint(4, self.w - 4)
           sy = random.randint(4, self.h - 4)
           ex = sx + random.randint(-20, 20)
           ey = sy + random.randint(-10, 10)
           cracks.append((sx, sy, ex, ey))
       return cracks


   def update(self):
       self.y  += self.vy
       self.x  += self.vx
       self.rot += self.rot_speed
       if self.y > HEIGHT + 60:
           self.reset()


   def draw(self, surface):
       tile_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
       pygame.draw.rect(tile_surf, (*self.color, self.alpha), (0, 0, self.w, self.h), border_radius=3)
       pygame.draw.rect(tile_surf, (*CRACK_COLOR, self.alpha), (0, 0, self.w, self.h), 2, border_radius=3)
       for (sx, sy, ex, ey) in self.cracks:
           pygame.draw.line(tile_surf, (*CRACK_COLOR, self.alpha), (sx, sy), (ex, ey), 1)
       rotated = pygame.transform.rotate(tile_surf, self.rot)
       rect = rotated.get_rect(center=(int(self.x), int(self.y)))
       surface.blit(rotated, rect)




# --- Background gradient ---
def draw_gradient(surface):
   for y in range(HEIGHT):
       t = y / HEIGHT
       r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
       g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
       b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
       pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))




# --- Ground crack line at bottom ---
def draw_ground_cracks(surface, tick):
   base_y = HEIGHT - 60
   crack_points = []
   x = 0
   while x < WIDTH:
       jitter = int(math.sin(x * 0.05 + tick * 0.03) * 6) + random.randint(-2, 2)
       crack_points.append((x, base_y + jitter))
       x += random.randint(8, 20)
   crack_points.append((WIDTH, base_y))
   if len(crack_points) > 1:
       pygame.draw.lines(surface, (100, 55, 15), False, crack_points, 2)
   fill_poly = crack_points + [(WIDTH, HEIGHT), (0, HEIGHT)]
   pygame.draw.polygon(surface, (55, 28, 8), fill_poly)
   tile_w, tile_h = 90, 25
   for col in range(0, WIDTH // tile_w + 1):
       for row in range(0, 3):
           tx = col * tile_w + (row % 2) * (tile_w // 2)
           ty = base_y + row * tile_h + 10
           rect = pygame.Rect(tx, ty, tile_w - 3, tile_h - 3)
           pygame.draw.rect(surface, (80, 42, 12), rect, border_radius=2)
           pygame.draw.rect(surface, (55, 28, 8), rect, 1, border_radius=2)




# --- Title with shake effect ---
def draw_title(surface, tick):
   shake_x = int(math.sin(tick * 0.18) * 2)
   shake_y = int(math.cos(tick * 0.22) * 1.5)
   title_text = "DON'T CRUMBLE"
   shadow = font_title.render(title_text, True, TITLE_SHADOW)
   surface.blit(shadow, (WIDTH // 2 - shadow.get_width() // 2 + shake_x + 5,
                         130 + shake_y + 6))
   title = font_title.render(title_text, True, TITLE_COLOR)
   surface.blit(title, (WIDTH // 2 - title.get_width() // 2 + shake_x,
                        130 + shake_y))
   sub = font_sub.render("A SURVIVAL PLATFORMER", True, (200, 140, 60))
   surface.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 238))




# --- Blinking prompt ---
def draw_prompt(surface, tick):
   if (tick // 35) % 2 == 0:
       prompt = font_prompt.render("PRESS  ENTER  TO  START", True, PROMPT_COLOR)
       surface.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 310))




# --- Controls panel ---
CONTROLS = [("MOVE",  "WASD or Arrow Keys"),]

# Not implemented yet
# ("JUMP",  "SPACE  /  W"),
# ("DASH",  "SHIFT")

def draw_controls(surface):
   panel_w, panel_h = 360, 110
   panel_x = WIDTH // 2 - panel_w // 2
   panel_y = 380
   panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
   pygame.draw.rect(panel_surf, (0, 0, 0, 120), (0, 0, panel_w, panel_h), border_radius=8)
   pygame.draw.rect(panel_surf, (180, 120, 40, 160), (0, 0, panel_w, panel_h), 2, border_radius=8)
   surface.blit(panel_surf, (panel_x, panel_y))
   header = font_ctrl.render("C O N T R O L S", True, HIGHLIGHT)
   surface.blit(header, (panel_x + panel_w // 2 - header.get_width() // 2, panel_y + 10))
   pygame.draw.line(surface, (180, 120, 40), (panel_x + 20, panel_y + 32),
                    (panel_x + panel_w - 20, panel_y + 32), 1)
   for i, (action, keys) in enumerate(CONTROLS):
       y = panel_y + 44 + i * 22
       action_surf = font_ctrl.render(action, True, DIM_COLOR)
       keys_surf   = font_ctrl.render(keys,   True, PROMPT_COLOR)
       surface.blit(action_surf, (panel_x + 24, y))
       surface.blit(keys_surf,   (panel_x + panel_w - keys_surf.get_width() - 24, y))




# --- Main loop ---
def run_start_screen():
   tiles = [FallingTile() for _ in range(22)]
   tick = 0
   while True:
       clock.tick(FPS)
       tick += 1
       for event in pygame.event.get():
           if event.type == pygame.QUIT:
               pygame.quit()
               sys.exit()
           if event.type == pygame.KEYDOWN:
               if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                   return  # Hand off to main game
       draw_gradient(screen)
       for tile in tiles:
           tile.update()
           tile.draw(screen)
       draw_ground_cracks(screen, tick)
       draw_title(screen, tick)
       draw_prompt(screen, tick)
       draw_controls(screen)
       pygame.display.flip()


