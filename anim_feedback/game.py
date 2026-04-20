from __future__ import annotations

import pygame
import random

from .audio import *
from .items import Coin, Dash_Power_Up, Heart
from .game_config import *
from .hazard import Hazard, MovingHazard
from .levels import LEVELS
from .level_utils import *
from .palette import Palette
from .particle import Particle
from .player import Player
from .persistence import (
    get_best_clear_time_s,
    get_best_level_reached,
    record_best_clear_time_s,
    record_best_level_reached,
)
from .pregame import run_pregame_sequence
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
        self.state = "title"  # title | play | level_cleared | paused | return_to_title_screen | won | game_over

        self.cue_flash = True
        self.cue_shake = True
        self.cue_hitstop = True
        self.cue_particles = True

        self.rng = random.Random(5)
        # Mixer often fails on macOS (CoreAudio) after window/display changes; game must still run.
        init_mixer_safe()

        self.all_sprites: pygame.sprite.Group[pygame.sprite.Sprite] = pygame.sprite.Group()
        self.walls: pygame.sprite.Group[Wall] = pygame.sprite.Group()
        self.coins: pygame.sprite.Group[Coin] = pygame.sprite.Group()
        self.hazards: pygame.sprite.Group[Hazard] = pygame.sprite.Group()
        self.dash_power_ups: pygame.sprite.Group[Dash_Power_Up] = pygame.sprite.Group()
        self.hearts: pygame.sprite.Group[Heart] = pygame.sprite.Group()
        self.coin_pickup_tone = make_tone(880, 0.05, 0.20)
        self.dash_power_up_pickup_tone = make_tone(1250, 0.06, 0.22)
        self.heart_pickup_tone = make_tone(720, 0.09, 0.24)
        self.player_hit_tone = make_tone(150, 0.18, 0.28)
        self.level_cleared_tone = make_tone(980, 0.12, 0.24)
        self.level_cleared_tone_2 = make_tone(1320, 0.10, 0.22)
        self.game_over_tone = make_tone(1000, 0.20, 0.20)

        self.player = Player(self.playfield.center, color = self.palette.player)
        self.all_sprites.add(self.player)

        self.particles: list[Particle] = []

        self._shake_for = 0.0
        self._hitstop_for = 0.0
        self._damage_pulse_for = 0.0
        self._clear_pulse_for = 0.0

        self.level_data = []
        self.current_level = 1   # Change this value to test any level without having to start from Level 1
        self.run_elapsed_s = 0.0
        self.best_level_reached = get_best_level_reached()
        self.best_clear_time_s = get_best_clear_time_s()

        self.dashes = 0
        self.dash_for = 0.0

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
                    if self.current_level >= 3 and (row_idx + col_idx) % 3 == 0:
                        hz = MovingHazard(
                            (x, y),
                            color=self.palette.hazard,
                            spin_speed_dps=190 * self._hazard_speed_mult(),
                            speed=min(260.0, 120.0 + 18.0 * self.current_level),
                        )
                    else:
                        hz = Hazard(
                            (x, y),
                            color=self.palette.hazard,
                            spin_speed_dps=200 * self._hazard_speed_mult(),
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

                # --- DASH POWER-UP ---
                elif tile == "D":
                    dash_power_up = Dash_Power_Up((x, y), color = self.palette.dash_power_up)
                    self.dash_power_ups.add(dash_power_up)
                    self.all_sprites.add(dash_power_up)
                
                # --- HEART ---
                elif tile == "E":
                    heart = Heart((x, y), color = self.palette.heart)
                    self.hearts.add(heart)
                    self.all_sprites.add(heart)

                # --- PLAYER SPAWN ---
                elif tile == "P":
                    self.player.pos.update(x, y)
                    self.player.rect.center = (x, y)
        
        self.coin_counter = 0
        if self.current_level not in self.coin_totals:
            self.coin_totals[self.current_level] = 0

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
        self.dash_power_ups.empty()
        self.hazards.empty()
        self.hearts.empty()
        self.particles.clear()

        self.player = Player(
            (self.playfield.left + 100, self.playfield.centery),
            color = self.palette.player,
        )
        self.all_sprites.add(self.player)

        self._build_playfield_content()

        if not keep_state:
            self.state = "play"

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        # Quit the game using the escape key from any state
        if event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        # Handle debug toggles with the F1 key and 1-4 keys
        if event.key == pygame.K_F1:
            self.debug = not self.debug
            return

        if self.debug:
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

        # Handle switching between "play" and "paused" states with the P key
        if event.key == pygame.K_p:
            if self.state == "play":
                self.state = "paused"
            elif self.state == "paused":
                self.state = "play"

        # Handle "paused" state input for returning to the title screen
        if self.state == "paused" and event.key == pygame.K_t: 
            self.state = "return_to_title_screen"
        if self.state == "paused" and event.key == pygame.K_r:
            self._reset_level(keep_state = True)
            self.state = "play"
            return

        # Handle "return_to_title_screen" state input
        if self.state == "return_to_title_screen": 
            if event.key == pygame.K_y:
                self.current_level = 1
                self.dashes = 0
                self.state = "title"
                run_pregame_sequence()
                self._reset_level(keep_state = True)
            elif event.key == pygame.K_n:
                self.state = "paused"
        
        # State transitions that require pressing the Enter key
        if self.state in {"title", "level_cleared", "game_over", "won"} and event.key == pygame.K_RETURN:
            
            if self.state == "level_cleared":
                self.state = "play"
                self._level_cleared()
            
            elif self.state == "won":
                self.current_level = 1
                self.dashes = 0
                self.state = "title"
                run_pregame_sequence()
                self._reset_level(keep_state = True)

            elif self.state == "game_over":
                self.current_level = 1
                self.dashes = 0
                self.state = "title"
                run_pregame_sequence()
                self._reset_level(keep_state = True)

            else:
                self.state = "play"
                self._reset_level(keep_state = True)
                self.run_elapsed_s = 0.0

        if self.dashes > 0 and self.state == "play" and (event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT):
            self._dash_power_up_use(self.player.rect, dt = 0.0)

    def _advance_to_next_level(self) -> None:
        self.pending_hp = self.player.hp
        self.pending_dashes = self.dashes
        self.state = "level_cleared"
        self._cue_level_cleared()

    def _level_cleared(self) -> None:
        self.current_level += 1
        self.best_level_reached = record_best_level_reached(self.current_level)
        
        self.all_sprites.empty()
        self.walls.empty()
        self.coins.empty()
        self.dash_power_ups.empty()
        self.hazards.empty()
        self.particles.clear()
        
        self.player = Player((self.playfield.left + 100, self.playfield.centery), 
                            color = self.palette.player)
        
        self.player.hp = self.pending_hp    # current health carries between levels due to health pick-ups
        self.player.score = 0               # reset score on level advance, as score is now a coin counter for each level individually
        self.dashes = self.pending_dashes   # dashes carry between levels

        self.all_sprites.add(self.player)
        self._build_playfield_content()

    def _cue_level_cleared(self) -> None:
        if self.cue_shake:
            self._shake_for = max(self._shake_for, 0.14)
        self._clear_pulse_for = max(self._clear_pulse_for, 0.20)
        self.level_cleared_tone.play()
        self.level_cleared_tone_2.play()

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

    # Cues animations and sounds for coin and dash power-up pickups
    def _cue_item(self, item_rect: pygame.Rect, pickup_tone: object) -> None:
        if self.cue_shake:
            self._shake_for = max(self._shake_for, 0.10)

        if self.cue_particles:
            self._spawn_particles(item_rect.center, color = self.palette.particle, count = 18)

        if pygame.mixer.get_init() is None or pygame.mixer.get_busy() == False:
            pickup_tone.play()

    # Handles actual use of the dash power-up item, as well as animations and sounds
    def _dash_power_up_use(self, dash_power_up_rect: pygame.Rect, dt: float) -> None:
        self.dashes -= 1
        self.dash_for = DASH_DURATION
        self.player.speed *= 1.5

        self._cue_item(dash_power_up_rect, self.dash_power_up_pickup_tone)

    def _cue_hit(self, source_rect: pygame.Rect) -> None:
        if self.cue_flash:
            self.player.flash_for = FLASH_DURATION
            self._damage_pulse_for = max(self._damage_pulse_for, 0.14)

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
        if self._damage_pulse_for > 0:
            self._damage_pulse_for = max(0.0, self._damage_pulse_for - dt)
        if self._clear_pulse_for > 0:
            self._clear_pulse_for = max(0.0, self._clear_pulse_for - dt)

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
        self.run_elapsed_s += dt

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
            self._cue_item(picked[0].rect, self.coin_pickup_tone)

        for picked in pygame.sprite.spritecollide(self.player, self.dash_power_ups, dokill = True):
            self.dashes += 1
            self.player.trigger_collect()
            self._cue_item(picked.rect, self.dash_power_up_pickup_tone)

        for picked in pygame.sprite.spritecollide(self.player, self.hearts, dokill = True):
            self.player.hp += 1
            self.player.trigger_collect()
            self._cue_item(picked.rect, self.heart_pickup_tone)

        for hz in pygame.sprite.spritecollide(self.player, self.hazards, dokill = False):
            self._apply_damage(hz.rect)

        for tile in self.tile_manager.tiles:
            if tile.is_deadly and tile.rect.colliderect(self.player.rect):
                self._apply_damage(tile.rect)
                break

        self.coins.update(dt)
        self.dash_power_ups.update(dt)
        self.hearts.update(dt)
        self.hazards.update(dt, self.walls, self.playfield)
        self.player.update(dt)
        self.tile_manager.update(dt)

        # Check for level completion
        if len(self.coins) == 0 and self._player_at_right_exit():
            if self.current_level >= len(LEVELS):
                self.state = "won"
                self.best_level_reached = record_best_level_reached(self.current_level)
                self.best_clear_time_s = record_best_clear_time_s(self.run_elapsed_s)
                self._cue_level_cleared()
            else:
                self._advance_to_next_level()
        
        # Handle dash duration and speed reset
        if self.dash_for > 0:
            self.dash_for = max(0.0, self.dash_for - dt)
        else:
            self.player.speed = PLAYER_SPEED

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

        # Defining HUD Element Strings
        level_string = f"Level: {self.current_level}  "
        coins_string = f"Coins: {self.player.score} / {self.coin_totals.get(self.current_level, 0)}  "
        dashes_string = f"Dashes: {self.dashes}  "
        hp_string = f"HP: {self.player.hp}  "
        best_level_string = f"Best Lv: {self.best_level_reached}  "
        best_time_string = f"Best Time: {self._fmt_time(self.best_clear_time_s) if self.best_clear_time_s else '--:--'}"

        # Drawing HUD Element Strings
        self._draw_text(
            (level_string + coins_string + dashes_string + hp_string), 
            (12, 16),
            self.palette.text
        )
        self._draw_text((best_level_string + best_time_string), (12, 36), self.palette.subtle)

        self._draw_text(
            ("Dashing!" if self.dash_for > 0 else ""), 
            (12, 54), 
            self.palette.text
        )

        # Message on the right of the HUD is different for Level 10
        level_10_hud_string = f"Collect all coins and reach the white wall on the right edge to win the game!"
        main_hud_string = f"Collect all coins and reach the white wall on the right edge to escape Level {self.current_level}!"

        self._draw_text(
            (level_10_hud_string if self.current_level == 10 else main_hud_string),
            ((352, 16) if self.current_level == 10 else (342, 16)),
            self.palette.text
        )

        cam = self._camera_offset()

        pygame.draw.rect(self.screen, self.palette.panel, pygame.Rect(0, HUD_H, SCREEN_W, SCREEN_H - HUD_H))

        self.tile_manager.draw(self.screen, cam)

        for wall in self.walls:
            pygame.draw.rect(self.screen, wall.color, wall.rect.move(cam))

        for coin in self.coins:
            self.screen.blit(coin.image, coin.rect.move(cam))

        for dash_power_up in self.dash_power_ups:
            self.screen.blit(dash_power_up.image, dash_power_up.rect.move(cam))

        for hz in self.hazards:
            self.screen.blit(hz.image, hz.rect.move(cam))

        for heart in self.hearts:
            self.screen.blit(heart.image, heart.rect.move(cam))

        player_image = self.player.image
        if self.cue_flash and self.player.flash_for > 0:
            player_image = player_image.copy()
            if player_image.get_flags() & pygame.SRCALPHA:
                player_image.fill((255, 255, 255, 120), special_flags=pygame.BLEND_RGBA_ADD)
            else:
                player_image = player_image.convert_alpha()
                player_image.fill((255, 255, 255, 120), special_flags=pygame.BLEND_RGBA_ADD)
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
            self._draw_centered(
                "Press Enter to Start.",
                y = self.playfield.centery - 40,
                color = self.palette.menu_text,
            )
            self._draw_centered(
                "While playing, press P to pause,",
                y = self.playfield.centery,
                color = self.palette.menu_muted,
            )
            self._draw_centered(
                "view controls, or return to title screen.",
                y = self.playfield.centery + 40,
                color = self.palette.menu_muted,
            )

        elif self.state == "level_cleared":
            self._draw_centered(
                f"You cleared Level {self.current_level}!",
                y = self.playfield.centery,
                color = self.palette.menu_text,
            )
            self._draw_centered(
                f"Press Enter to Continue to Level {self.current_level + 1}.",
                y = self.playfield.centery + 40,
                color = self.palette.menu_muted,
            )

        elif self.state == "game_over":
            self._draw_centered(
                "Game Over — Press Enter to return to title screen.",
                y = self.playfield.centery,
                color = self.palette.menu_text,
            )

        elif self.state == "won":
            self._draw_centered(
                "You Escaped! — Press Enter to return to title screen.",
                y = self.playfield.centery,
                color = self.palette.menu_text,
            )

        elif self.state == "paused":
            self._draw_centered(
                "Paused — Press P to resume or T to return to title screen.",
                y = self.playfield.centery - 60,
                color = self.palette.menu_text,
            )
            self._draw_centered(
                "Controls:",
                y = self.playfield.centery - 20,
                color = self.palette.menu_muted,
            )
            self._draw_centered(
                "Move: Arrow keys or WASD",
                y = self.playfield.centery + 20,
                color = self.palette.menu_muted,
            )
            self._draw_centered(
                "Dash: Left or Right Shift",
                y = self.playfield.centery + 60,
                color = self.palette.menu_muted,
            )
            self._draw_centered(
                "Restart Level: R",
                y = self.playfield.centery + 100,
                color = self.palette.menu_muted,
            )

        elif self.state == "return_to_title_screen":
            self._draw_centered(
                "Are you sure? All current progress will be lost:",
                y = self.playfield.centery,
                color = self.palette.menu_text,
            )
            self._draw_centered(
                "Y - Yes, N - No",
                y = self.playfield.centery + 40,
                color = self.palette.menu_muted,
            )

        # Small pulse feedback for damage / level clear.
        if self._damage_pulse_for > 0:
            a = int(75 * _clamp(self._damage_pulse_for / 0.14, 0.0, 1.0))
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((200, 30, 30, a))
            self.screen.blit(overlay, (0, 0))
        if self._clear_pulse_for > 0:
            a = int(65 * _clamp(self._clear_pulse_for / 0.20, 0.0, 1.0))
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((240, 215, 120, a))
            self.screen.blit(overlay, (0, 0))

    # Used for displaying HUD text
    def _draw_text(self, text: str, pos: tuple[int, int], color: pygame.Color) -> None:
        shadow = self.font.render(text, True, self.palette.menu_shadow)
        s = self.font.render(text, True, color)
        x, y = pos
        self.screen.blit(shadow, (x + 1, y + 1))
        self.screen.blit(s, (x, y))

    # Used for displaying large centered text on the screen for various game states
    def _draw_centered(self, text: str, *, y: int, color: pygame.Color) -> None:
        shadow = self.big_font.render(text, True, self.palette.menu_shadow)
        s = self.big_font.render(text, True, color)
        r_shadow = shadow.get_rect(center = (SCREEN_W // 2, y + 1))
        r = s.get_rect(center = (SCREEN_W // 2, y))
        bg_rect = r.inflate(24, 14)
        pygame.draw.rect(self.screen, self.palette.menu_panel, bg_rect, border_radius = 6)
        pygame.draw.rect(self.screen, self.palette.menu_panel_border, bg_rect, 1, border_radius = 6)
        self.screen.blit(shadow, r_shadow)
        self.screen.blit(s, r)

    def _fmt_time(self, seconds: float) -> str:
        total = max(0, int(round(seconds)))
        m, s = divmod(total, 60)
        return f"{m:02d}:{s:02d}"