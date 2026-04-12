from __future__ import annotations

import pygame
import random

from .audio import Tone
from .coin import Coin
from .game_config import *
from .hazard import Hazard
from .levels import LEVELS
from .level_utils import *
from .palette import Palette
from .particle import Particle
from .player import Player
from .start_screen import *
from .tile_manager import TileManager


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


class Game:
    def __init__(self) -> None:
        self.palette = Palette()

        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.font = pygame.font.SysFont(None, 22)
        self.big_font = pygame.font.SysFont(None, 40)

        self.screen_rect = pygame.Rect(0, 0, SCREEN_W, SCREEN_H)
        self.playfield = pygame.Rect(
            PADDING,
            HUD_H + PADDING,
            WORLD_W - 2 * PADDING,
            SCREEN_H - HUD_H - 2 * PADDING,
        )

        self.debug = False
        self.state = "title"  # title | play | level_cleared | game_over | won | paused

        self.cue_flash = True
        self.cue_shake = True
        self.cue_hitstop = True
        self.cue_particles = True

        self.rng = random.Random(5)
        pygame.mixer.init()

        self.all_sprites: pygame.sprite.Group[pygame.sprite.Sprite] = pygame.sprite.Group()
        self.walls: pygame.sprite.Group[Wall] = pygame.sprite.Group()
        self.coins: pygame.sprite.Group[Coin] = pygame.sprite.Group()
        self.hazards: pygame.sprite.Group[Hazard] = pygame.sprite.Group()

        self.coin_pickup_tone: Tone = Tone(880, 0.05, 0.20)
        self.player_hit_tone: Tone = Tone(160, 0.16, 0.25)
        self.game_over_tone: Tone = Tone(1000, 0.20, 0.20)

        self.player = Player(self.playfield.center, color=self.palette.player)
        self.all_sprites.add(self.player)

        self.particles: list[Particle] = []

        self._shake_for = 0.0
        self._hitstop_for = 0.0

        self.level_data = []
        self.current_level = 1   # Change this value to test any level without having to start from Level 1

        self._reset_level(keep_state = True)

    # --- Diffculty parameters ---

    def _hazard_speed_mult(self) -> float:
        return 1.0 + (0.2 * self.current_level) if self.current_level >= 2 else 1.0

    def _tile_fade_mult(self) -> float:
        return 0.9 + (0.1 * self.current_level) if self.current_level >= 2 else 1.0

    def _tile_wave_mult(self) -> float:
        return 0.8 + (0.1 * self.current_level) if self.current_level >= 2 else 1.0

    def _player_at_right_exit(self) -> bool:
        return self.player.rect.right >= self.playfield.right - EXIT_RIGHT_MARGIN

    # --- Level building and management ---

    def _build_playfield_content(self) -> None:        
        
        def add_wall_rect(rect: pygame.Rect) -> None:
            wall = Wall(rect, self.palette.wall)
            self.walls.add(wall)
            self.all_sprites.add(wall)

        def add_finish_wall_rect(rect: pygame.Rect) -> None:
            finish_wall = Wall(rect, self.palette.finish_wall)
            self.walls.add(finish_wall)
            self.all_sprites.add(finish_wall)

        # --- Border walls ---
        t = 20

        # left: The x-coordinate of the top-left corner.
        # top: The y-coordinate of the top-left corner.
        # width: The horizontal dimension of the rectangle.
        # height: The vertical dimension of the rectangle.

        # Top wall
        add_wall_rect(pygame.Rect(self.playfield.left, self.playfield.top, self.playfield.width + 12, t))
        
        # Bottom Wall
        add_wall_rect(pygame.Rect(self.playfield.left, self.playfield.bottom - 8, self.playfield.width + 12, t))
        
        # Left Wall
        add_wall_rect(pygame.Rect(self.playfield.left, self.playfield.top, t, self.playfield.height))
        
        # Right Wall
        add_finish_wall_rect(pygame.Rect(self.playfield.right - t, self.playfield.top, 2 * t, self.playfield.height + t))

        # --- TILE LEVEL ---
        grid = LEVELS[self.current_level - 1]

        TILE_SIZE = 20   # the game breaks if this isn't here

        self.coin_totals = {}
        self.coin_counter = 0

        for row_idx, row in enumerate(grid):
            for col_idx, tile in enumerate(row):

                x = self.playfield.left + col_idx * TILE_SIZE
                y = self.playfield.top + row_idx * TILE_SIZE

                # --- WALL ---
                if tile == "W":
                    add_wall_rect(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))

                # --- HAZARD ---
                elif tile == "H":
                    hz = Hazard(
                        (x, y),
                        color = self.palette.hazard,
                        spin_speed_dps = 200 * self._hazard_speed_mult(),
                    )
                    self.hazards.add(hz)
                    self.all_sprites.add(hz)

                # --- COIN ---
                elif tile == "C":
                    self.coin_counter += 1
                    coin = Coin((x, y), color = self.palette.coin)
                    self.coins.add(coin)
                    self.all_sprites.add(coin)
                    self.coin_totals[self.current_level] = self.coin_counter

                # --- PLAYER SPAWN ---
                elif tile == "P":
                    self.player.pos.update(x, y)
                    self.player.rect.center = (x, y)
        
        self.coin_counter = 0

        # --- TileManager ---
        self.tile_manager = TileManager(
            self.playfield,
            panel_color = self.palette.panel,
            rng = self.rng,
            fade_speed_mult = self._tile_fade_mult(),
            wave_speed_mult = self._tile_wave_mult(),
        )

    def _reset_level(self, *, keep_state: bool = False) -> None:
        self.all_sprites.empty()
        self.walls.empty()
        self.coins.empty()
        self.hazards.empty()
        self.particles.clear()

        self.player = Player(
            (self.playfield.left + 100, self.playfield.centery),
            color = self.palette.player,
        )
        self.all_sprites.add(self.player)

        self._build_playfield_content()

        if not keep_state:
            self.state = "play"

    def _advance_to_next_level(self) -> None:
        self.state = "level_cleared"

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        if event.key == pygame.K_F1:
            self.debug = not self.debug
            return

        if event.key == pygame.K_1:
            self.cue_flash = not self.cue_flash
            return

        if event.key == pygame.K_2:
            self.cue_shake = not self.cue_shake
            return

        if event.key == pygame.K_3:
            self.cue_hitstop = not self.cue_hitstop
            return

        if event.key == pygame.K_4:
            self.cue_particles = not self.cue_particles
            return

        if event.key == pygame.K_p:
            if self.state == "play":
                self.state = "paused"
            elif self.state == "paused":
                self.state = "play"

        if self.state == "paused" and event.key == pygame.K_t:   # option to return to the title screen
            self.state = "return_to_title_screen"

        if self.state == "return_to_title_screen":
            if event.key == pygame.K_y:
                self.current_level = 1
                self._reset_level(keep_state = True)
                self.state = "title"
                run_start_screen()
            elif event.key == pygame.K_n:
                self.state = "paused"
        
        if self.state in {"title", "level_cleared", "game_over", "won"} and event.key == pygame.K_RETURN:
            
            if self.state == "level_cleared":
                self.state = "play"
                self._level_cleared()
            
            elif self.state == "won":
                self.current_level = 1
                self._reset_level(keep_state = True)
                self.state = "title"
                run_start_screen()
            
            elif self.state == "game_over":
                self.current_level = 1
                self._reset_level(keep_state = True)
                self.state = "title"
                run_start_screen()

            else:
                self.state = "play"
                self._reset_level(keep_state = True)

    def _level_cleared(self) -> None:
        self.current_level += 1
        
        self.all_sprites.empty()
        self.walls.empty()
        self.coins.empty()
        self.hazards.empty()
        self.particles.clear()
        
        self.player = Player((self.playfield.left + 100, self.playfield.centery), 
                            color = self.palette.player)
        
        self.player.hp = PLAYER_HEALTH   # reset HP on level advance (might change in favor of health pick-up items)
        self.player.score = 0            # reset score on level advance, as score is now a coin counter for each level individually

        self.all_sprites.add(self.player)
        
        self._build_playfield_content()

    def _read_move(self) -> pygame.Vector2:
        keys = pygame.key.get_pressed()

        x = 0
        y = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            y += 1

        v = pygame.Vector2(x, y)
        if v.length_squared() > 0:
            v = v.normalize()
        return v

    def _move_player_axis(self, axis: str, amount: float) -> None:
        if axis == "x":
            self.player.pos.x += amount
            self.player.rect.centerx = int(round(self.player.pos.x))
        else:
            self.player.pos.y += amount
            self.player.rect.centery = int(round(self.player.pos.y))

        hits = pygame.sprite.spritecollide(self.player, self.walls, dokill = False)
        if not hits:
            return

        for wall in hits:
            if axis == "x":
                if amount > 0:
                    self.player.rect.right = wall.rect.left
                elif amount < 0:
                    self.player.rect.left = wall.rect.right
                self.player.pos.x = self.player.rect.centerx
            else:
                if amount > 0:
                    self.player.rect.bottom = wall.rect.top
                elif amount < 0:
                    self.player.rect.top = wall.rect.bottom
                self.player.pos.y = self.player.rect.centery

    def _spawn_particles(self, center: tuple[int, int], *, color: pygame.Color, count: int) -> None:
        for _ in range(count):
            angle = self.rng.random() * 6.2831853
            speed = self.rng.uniform(80.0, 240.0)
            vel = pygame.Vector2(speed, 0).rotate_rad(angle)
            p = Particle(
                pos = pygame.Vector2(center),
                vel = vel,
                radius = self.rng.uniform(2.0, 5.0),
                color = color,
                life = 0.35,
                ttl = 0.35,
            )
            self.particles.append(p)

    def _cue_coin(self, coin_rect: pygame.Rect) -> None:
        if self.cue_shake:
            self._shake_for = max(self._shake_for, 0.10)

        if self.cue_particles:
            self._spawn_particles(coin_rect.center, color=self.palette.particle, count=18)

        if pygame.mixer.get_busy() == False:
            self.coin_pickup_tone.play()

    def _cue_hit(self, source_rect: pygame.Rect) -> None:
        if self.cue_flash:
            self.player.flash_for = FLASH_DURATION

        if self.cue_hitstop:
            self._hitstop_for = max(self._hitstop_for, 0.06)

        if self.cue_shake:
            self._shake_for = max(self._shake_for, 0.18)

        if self.cue_particles:
            self._spawn_particles(self.player.rect.center, color=self.palette.hazard, count=26)

        self.player_hit_tone.play()

    def _apply_damage(self, source_rect: pygame.Rect) -> None:
        if self.player.is_invincible:
            return

        self.player.hp -= 1
        self.player.invincible_for = INVINCIBLE_FOR

        push = pygame.Vector2(self.player.rect.center) - pygame.Vector2(source_rect.center)
        if push.length_squared() == 0:
            push = pygame.Vector2(1, 0)
        push = push.normalize() * 540.0
        self.player.vel.update(push)

        self._cue_hit(source_rect)

        if self.player.hp <= 0:
            self._cue_game_over()

    def _cue_game_over(self) -> None:
        self.state = "game_over"
        if self.cue_shake:
            self._shake_for = max(self._shake_for, 0.20)
        self.game_over_tone.play()

    def update(self, dt: float) -> None:
        if self._shake_for > 0:
            self._shake_for = max(0.0, self._shake_for - dt)

        if self._hitstop_for > 0:
            self._hitstop_for = max(0.0, self._hitstop_for - dt)
            return

        for p in list(self.particles):
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

        if self.state != "play":
            return

        move = self._read_move()
        self.player.vel.update(move * self.player.speed)

        speed2 = self.player.vel.length_squared()
        if self.player.is_invincible:
            self.player.set_state("hurt")
        elif self.player.collect_for > 0:
            pass
        elif speed2 < 1.0:
            self.player.set_state("idle")
        else:
            self.player.set_state("run")

        self._move_player_axis("x", self.player.vel.x * dt)
        self._move_player_axis("y", self.player.vel.y * dt)

        picked = pygame.sprite.spritecollide(self.player, self.coins, dokill = True)
        if picked:
            self.player.score += len(picked)
            self.player.trigger_collect()
            self._cue_coin(picked[0].rect)

        for hz in pygame.sprite.spritecollide(self.player, self.hazards, dokill = False):
            self._apply_damage(hz.rect)

        for tile in self.tile_manager.tiles:
            if tile.is_deadly and tile.rect.colliderect(self.player.rect):
                self._apply_damage(tile.rect)
                break

        self.tile_manager.update(dt)
        self.coins.update(dt)
        self.hazards.update(dt)
        self.player.update(dt)

        if len(self.coins) == 0 and self._player_at_right_exit():
            if self.current_level >= len(LEVELS):
                self.state = "won"
            else:
                self.state = "level_cleared"
                self._advance_to_next_level()

    def _camera_offset(self) -> tuple[int, int]:
        target = self.player.pos.x - SCREEN_W // 2
        scroll_x = max(0.0, min(float(WORLD_W - SCREEN_W), target))
        ox, oy = 0, 0
        if self.cue_shake and self._shake_for > 0:
            strength = _clamp(self._shake_for / 0.18, 0.0, 1.0)
            max_px = 10 * strength
            ox = int(self.rng.uniform(-max_px, max_px))
            oy = int(self.rng.uniform(-max_px, max_px))
        return (-int(scroll_x) + ox, oy)

    def draw(self) -> None:
        self.screen.fill(self.palette.bg)

        hud_rect = pygame.Rect(0, 0, SCREEN_W, HUD_H)
        pygame.draw.rect(self.screen, self.palette.panel, hud_rect)

        self._draw_text(
            f"Level: {self.current_level}  Coins: {self.player.score} / {self.coin_totals.get(self.current_level)}  HP: {self.player.hp}",
            (12, 16),
            self.palette.text
        )

        level_10_hud_string = f"Collect all the coins and reach the purple wall on the right edge to win the game!"
        main_hud_string = f"Collect all the coins and reach the purple wall on the right edge to escape Level {self.current_level}!"

        self._draw_text(
            (level_10_hud_string if self.current_level == 10 else main_hud_string),
            ((320, 16) if self.current_level == 10 else (310, 16)),
            self.palette.text
        )

        cam = self._camera_offset()

        pygame.draw.rect(self.screen, self.palette.panel, pygame.Rect(0, HUD_H, SCREEN_W, SCREEN_H - HUD_H))

        self.tile_manager.draw(self.screen, cam)

        for wall in self.walls:
            pygame.draw.rect(self.screen, wall.color, wall.rect.move(cam))

        for coin in self.coins:
            self.screen.blit(coin.image, coin.rect.move(cam))

        for hz in self.hazards:
            self.screen.blit(hz.image, hz.rect.move(cam))

        player_image = self.player.image
        if self.cue_flash and self.player.flash_for > 0:
            player_image = player_image.copy()
            player_image.fill((255, 255, 255, 120), special_flags = pygame.BLEND_RGBA_ADD)
        self.screen.blit(player_image, self.player.rect.move(cam))

        for p in self.particles:
            a = _clamp(p.life / p.ttl, 0.0, 1.0)
            radius = max(1, int(round(p.radius * (0.8 + 0.6 * a))))
            col = pygame.Color(p.color)
            col.a = int(255 * a)
            surf = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, col, (radius + 1, radius + 1), radius)
            self.screen.blit(surf, (p.pos.x - radius + cam[0], p.pos.y - radius + cam[1]))

        if self.debug:
            pygame.draw.rect(self.screen, pygame.Color("#d08770"), self.player.rect.move(cam), 2)
            for coin in self.coins:
                pygame.draw.rect(self.screen, pygame.Color("#ebcb8b"), coin.rect.move(cam), 2)
            for hz in self.hazards:
                pygame.draw.rect(self.screen, pygame.Color("#bf616a"), hz.rect.move(cam), 2)

        # --- Overlay text for various states ---

        if self.state == "title":
            self._draw_centered("Press Enter to Start.", 
                                y = self.playfield.centery - 40, 
                                color = self.palette.text)
            self._draw_centered("While playing, press P to pause,", 
                                y = self.playfield.centery, 
                                color = self.palette.text)
            self._draw_centered("view controls, or return to title screen.", 
                                y = self.playfield.centery + 40, 
                                color = self.palette.text)
        
        elif self.state == "level_cleared":
            self._draw_centered(f"You cleared Level {self.current_level}!", 
                                y = self.playfield.centery, 
                                color = self.palette.text)
            self._draw_centered(f"Press Enter to Continue to Level {self.current_level + 1}.", 
                                y = self.playfield.centery + 40, 
                                color = self.palette.text)
        
        elif self.state == "game_over":
            self._draw_centered("Game Over — Press Enter to return to title screen.", 
                                y = self.playfield.centery, 
                                color = self.palette.text)
        
        elif self.state == "won":
            self._draw_centered("You Escaped! — Press Enter to return to title screen.", 
                                y = self.playfield.centery, 
                                color = self.palette.text)
        
        elif self.state == "paused":
            self._draw_centered("Paused — Press P to resume or T to return to title screen.", 
                                y = self.playfield.centery, 
                                color = self.palette.text)
            self._draw_centered("While playing, use arrow keys or WASD to move.", 
                                y = self.playfield.centery + 40, 
                                color = self.palette.text)
        
        elif self.state == "return_to_title_screen":
            self._draw_centered("Are you sure? All current progress will be lost:", 
                                y = self.playfield.centery, 
                                color = self.palette.text)
            self._draw_centered("Y - Yes, N - No", 
                                y = self.playfield.centery + 40, 
                                color = self.palette.text)

    # Used for displaying HUD text
    def _draw_text(self, text: str, pos: tuple[int, int], color: pygame.Color) -> None:
        shadow = self.font.render(text, True, pygame.Color(0, 0, 0, 180))
        s = self.font.render(text, True, color)
        x, y = pos
        self.screen.blit(shadow, (x + 1, y + 1))
        self.screen.blit(s, (x, y))

    # Used for displaying large centered text on the screen for various game states
    def _draw_centered(self, text: str, *, y: int, color: pygame.Color) -> None:
        shadow = self.big_font.render(text, True, pygame.Color(0, 0, 0, 180))
        s = self.big_font.render(text, True, color)
        r_shadow = shadow.get_rect(center = (SCREEN_W // 2, y + 1))
        r = s.get_rect(center = (SCREEN_W // 2, y))
        bg_rect = r.inflate(20, 10)
        pygame.draw.rect(self.screen, pygame.Color(0, 0, 0), bg_rect)
        self.screen.blit(shadow, r_shadow)
        self.screen.blit(s, r)