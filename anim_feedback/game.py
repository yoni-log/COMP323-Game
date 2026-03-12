from __future__ import annotations

from dataclasses import dataclass, field
import random
import array

import pygame

from .animation import Animation
from .palette import Palette
from .particle import Particle
from .coin import *
from .map import *
from .tile_manager import TileManager

def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))

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

class Hazard(pygame.sprite.Sprite):
    def __init__(
        self,
        center: tuple[int, int],
        *,
        color: pygame.Color,
        size: int = 34,
        spin_speed_dps: float = 210.0,
    ) -> None:
        super().__init__()
        self.base = _make_hazard_surface(size, color)
        self.angle = 0.0
        self.spin_speed_dps = spin_speed_dps

        self.image = self.base
        self.rect = self.image.get_rect(center=center)

    def update(self, dt: float) -> None:
        self.angle = (self.angle + self.spin_speed_dps * dt) % 360.0
        center = self.rect.center
        self.image = pygame.transform.rotate(self.base, self.angle)
        self.rect = self.image.get_rect(center=center)


class Player(pygame.sprite.Sprite):
    COLLECT_DURATION = 0.5

    def __init__(
        self,
        center: tuple[int, int],
        *,
        color: pygame.Color,
    ) -> None:
        super().__init__()

        self.anims = _make_player_anims(color)
        self.state = "idle"
        self.prev_state = "idle"

        self.image = self.anims[self.state].image
        self.rect = self.image.get_rect(center=center)

        self.pos = pygame.Vector2(self.rect.center)
        self.vel = pygame.Vector2(0, 0)
        self.speed = 320.0

        self.hp = 3
        self.invincible_for = 0.0

        self.score = 0

        self.flash_for = 0.0

        self.collect_for = 0.0

    @property
    def is_invincible(self) -> bool:
        return self.invincible_for > 0

    def set_state(self, new_state: str) -> None:
        if new_state == self.state:
            return
        self.prev_state = self.state
        self.state = new_state
        self.anims[self.state].reset()

    def trigger_collect(self) -> None:
        self.collect_for = self.COLLECT_DURATION
        self.set_state("collect")

    def update(self, dt: float) -> None:
        self.anims[self.state].update(dt)
        center = self.rect.center
        self.image = self.anims[self.state].image
        self.rect = self.image.get_rect(center=center)

        if self.collect_for > 0:
            self.collect_for = max(0.0, self.collect_for - dt)
        elif self.invincible_for > 0:
            self.invincible_for = max(0.0, self.invincible_for - dt)
        elif self.flash_for > 0:
            self.flash_for = max(0.0, self.flash_for - dt)


class Game:
    fps = 60

    # Match the start screen resolution so there is no size jump
    SCREEN_W, SCREEN_H = 900, 600
    WORLD_W = 2880
    HUD_H = 56
    PADDING = 12

    def __init__(self) -> None:
        self.palette = Palette()

        self.screen = pygame.display.set_mode((self.SCREEN_W, self.SCREEN_H))
        self.font = pygame.font.SysFont(None, 22)
        self.big_font = pygame.font.SysFont(None, 40)

        self.screen_rect = pygame.Rect(0, 0, self.SCREEN_W, self.SCREEN_H)
        self.playfield = pygame.Rect(
            self.PADDING,
            self.HUD_H + self.PADDING,
            self.WORLD_W - 2 * self.PADDING,
            self.SCREEN_H - self.HUD_H - 2 * self.PADDING,
        )

        self.debug = False
        self.state = "title"  # title | play | game_over | paused

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

        self._reset_level(keep_state=True)

    def _reset_level(self, *, keep_state: bool = False) -> None:
        self.all_sprites.empty()
        self.walls.empty()
        self.coins.empty()
        self.hazards.empty()
        self.particles.clear()

        self.player = Player(
            (self.playfield.left + 200, self.playfield.centery),
            color=self.palette.player,
        )
        self.all_sprites.add(self.player)

        def add_wall(r: pygame.Rect) -> None:
            wall = Wall(r, self.palette.wall)
            self.walls.add(wall)
            self.all_sprites.add(wall)

        t = 16
        add_wall(pygame.Rect(self.playfield.left, self.playfield.top, self.playfield.width, t))
        add_wall(pygame.Rect(self.playfield.left, self.playfield.bottom - t, self.playfield.width, t))
        add_wall(pygame.Rect(self.playfield.left, self.playfield.top, t, self.playfield.height))
        add_wall(pygame.Rect(self.playfield.right - t, self.playfield.top, t, self.playfield.height))

        lx = self.playfield.left
        lt = self.playfield.top
        add_wall(pygame.Rect(lx + 180,  lt + 110, 18, 240))
        add_wall(pygame.Rect(lx + 420,  lt + 40,  18, 240))
        add_wall(pygame.Rect(lx + 560,  lt + 240, 260, 18))
        add_wall(pygame.Rect(lx + 800,  lt + 80,  18, 200))
        add_wall(pygame.Rect(lx + 1000, lt + 160, 220, 18))
        add_wall(pygame.Rect(lx + 1300, lt + 100, 18, 280))
        add_wall(pygame.Rect(lx + 1600, lt + 60,  260, 18))
        add_wall(pygame.Rect(lx + 1900, lt + 180, 18, 200))
        add_wall(pygame.Rect(lx + 2100, lt + 240, 220, 18))
        add_wall(pygame.Rect(lx + 2450, lt + 80,  18, 260))

        cy = self.playfield.centery
        for hx, hy, spd in [
            (lx + 380,  cy - 80,  210.0),
            (lx + 750,  cy + 120, 260.0),
            (lx + 1150, cy - 100, 210.0),
            (lx + 1550, cy + 80,  260.0),
            (lx + 1950, cy - 60,  210.0),
            (lx + 2350, cy + 100, 260.0),
        ]:
            hz = Hazard((hx, hy), color=self.palette.hazard, spin_speed_dps=spd)
            self.hazards.add(hz)
            self.all_sprites.add(hz)

        for _ in range(18):
            for __ in range(120):
                x = self.rng.randint(self.playfield.left + 50, self.playfield.right - 50)
                y = self.rng.randint(self.playfield.top + 50, self.playfield.bottom - 50)
                candidate = Coin((x, y), color=self.palette.coin)

                if pygame.sprite.spritecollideany(candidate, self.walls):
                    continue
                if pygame.sprite.spritecollideany(candidate, self.coins):
                    continue
                if candidate.rect.colliderect(self.player.rect):
                    continue

                self.coins.add(candidate)
                self.all_sprites.add(candidate)
                break

        self.tile_manager = TileManager(
            self.playfield,
            panel_color=self.palette.panel,
            rng=self.rng,
        )

        if not keep_state:
            self.state = "play"

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        if event.key == pygame.K_F1:
            self.debug = not self.debug
            return

        if event.key == pygame.K_r:
            self._reset_level(keep_state=(self.state == "title"))
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
        
        if event.key == pygame.K_p:   # Toggles between paused and play states
            if self.state == "play":
                self.state = "paused"
            elif self.state == "paused":
                self.state = "play"

        if self.state in {"title", "game_over"} and event.key == pygame.K_RETURN:
            self._reset_level(keep_state=True)
            self.state = "play"

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

        hits = pygame.sprite.spritecollide(self.player, self.walls, dokill=False)
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
                pos=pygame.Vector2(center),
                vel=vel,
                radius=self.rng.uniform(2.0, 5.0),
                color=color,
                life=0.35,
                ttl=0.35,
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
            self.player.flash_for = 0.18

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
        self.player.invincible_for = 0.85

        push = pygame.Vector2(self.player.rect.center) - pygame.Vector2(source_rect.center)
        if push.length_squared() == 0:
            push = pygame.Vector2(1, 0)
        push = push.normalize() * 540.0
        self.player.vel.update(push)

        self._cue_hit(source_rect)

        if self.player.hp <= 0:
            self.state = "game_over"

    def _cue_game_over(self) -> None:
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

        picked = pygame.sprite.spritecollide(self.player, self.coins, dokill=True)
        if picked:
            self.player.score += len(picked)
            self.player.trigger_collect()
            self._cue_coin(picked[0].rect)

        for hz in pygame.sprite.spritecollide(self.player, self.hazards, dokill=False):
            self._apply_damage(hz.rect)

        for tile in self.tile_manager.tiles:
            if tile.is_deadly and tile.rect.colliderect(self.player.rect):
                self._apply_damage(tile.rect)
                break

        self.tile_manager.update(dt)
        self.coins.update(dt)
        self.hazards.update(dt)
        self.player.update(dt)

        if len(self.coins) == 0:
            self._cue_game_over()
            self._reset_level(keep_state=True)
            self.state = "play"

    def _camera_offset(self) -> tuple[int, int]:
        target = self.player.pos.x - self.SCREEN_W // 2
        scroll_x = max(0.0, min(float(self.WORLD_W - self.SCREEN_W), target))
        ox, oy = 0, 0
        if self.cue_shake and self._shake_for > 0:
            strength = _clamp(self._shake_for / 0.18, 0.0, 1.0)
            max_px = 10 * strength
            ox = int(self.rng.uniform(-max_px, max_px))
            oy = int(self.rng.uniform(-max_px, max_px))
        return (-int(scroll_x) + ox, oy)

    def draw(self) -> None:
        self.screen.fill(self.palette.bg)

        hud_rect = pygame.Rect(0, 0, self.SCREEN_W, self.HUD_H)
        pygame.draw.rect(self.screen, self.palette.panel, hud_rect)

        # Clean HUD: just show the core game info
        self._draw_text(f"HP {self.player.hp}   Score {self.player.score}", (12, 16), self.palette.text)

        cam = self._camera_offset()

        pygame.draw.rect(self.screen, self.palette.panel,
                         pygame.Rect(0, self.HUD_H, self.SCREEN_W, self.SCREEN_H - self.HUD_H))

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

        if self.state == "title":
            self._draw_centered("Press Enter to Start", y=self.playfield.centery, color=self.palette.text)
        elif self.state == "game_over":
            self._draw_centered("Game Over — Press Enter", y=self.playfield.centery, color=self.palette.text)
        elif self.state == "paused": 
            self._draw_centered("Paused — Press P to resume.", y=self.playfield.centery, color=self.palette.text)

    def _draw_text(self, text: str, pos: tuple[int, int], color: pygame.Color) -> None:
        s = self.font.render(text, True, color)
        self.screen.blit(s, pos)

    def _draw_centered(self, text: str, *, y: int, color: pygame.Color) -> None:
        s = self.big_font.render(text, True, color)
        r = s.get_rect(center=(self.SCREEN_W // 2, y))
        self.screen.blit(s, r)


def _make_hazard_surface(size: int, color: pygame.Color) -> pygame.Surface:
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    pts = [
        (cx, 2),
        (size - 2, cy),
        (cx, size - 2),
        (2, cy),
    ]
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.polygon(surf, pygame.Color("#000000"), pts, 2)
    return surf


def _make_player_anims(color: pygame.Color) -> dict[str, Animation]:
    idle = [_draw_player_frame(color, leg_phase=0, eye_open=True)]

    run_frames = [
        _draw_player_frame(color, leg_phase=0, eye_open=True),
        _draw_player_frame(color, leg_phase=1, eye_open=True),
        _draw_player_frame(color, leg_phase=2, eye_open=True),
        _draw_player_frame(color, leg_phase=3, eye_open=True),
    ]

    hurt_frames = [
        _draw_player_frame(pygame.Color("#d08770"), leg_phase=0, eye_open=False),
        _draw_player_frame(pygame.Color("#bf616a"), leg_phase=2, eye_open=False),
    ]


    collect = [
        _draw_player_frame(pygame.Color("#e8c173"), leg_phase=0, eye_open=False),
        _draw_player_frame(pygame.Color("#dada29"), leg_phase=1, eye_open=True),
        _draw_player_frame(pygame.Color("#e8c173"), leg_phase=2, eye_open=False),
        _draw_player_frame(pygame.Color("#dada29"), leg_phase=3, eye_open=True),
    ]

    return {
        "idle": Animation(idle, fps=1.0),
        "run": Animation(run_frames, fps=10.0),
        "hurt": Animation(hurt_frames, fps=8.0),
        "collect": Animation(collect, fps=4.0)
    }


def _draw_player_frame(color: pygame.Color, *, leg_phase: int, eye_open: bool) -> pygame.Surface:
    w, h = 44, 44
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    # Body
    body = pygame.Rect(0, 0, 24, 26)
    body.center = (w // 2, h // 2 + 4)
    pygame.draw.rect(surf, color, body, border_radius=8)
    pygame.draw.rect(surf, pygame.Color("#000000"), body, 2, border_radius=8)

    # Head
    head_center = (w // 2, h // 2 - 10)
    pygame.draw.circle(surf, color, head_center, 10)
    pygame.draw.circle(surf, pygame.Color("#000000"), head_center, 10, 2)

    # Eyes
    eye = pygame.Color("#2e3440")
    if eye_open:
        pygame.draw.circle(surf, eye, (head_center[0] - 3, head_center[1] - 1), 2)
        pygame.draw.circle(surf, eye, (head_center[0] + 3, head_center[1] - 1), 2)
    else:
        pygame.draw.line(surf, eye, (head_center[0] - 5, head_center[1] - 1), (head_center[0] - 1, head_center[1] - 1), 2)
        pygame.draw.line(surf, eye, (head_center[0] + 1, head_center[1] - 1), (head_center[0] + 5, head_center[1] - 1), 2)

    # Legs (simple alternating phase)
    leg_y = body.bottom + 2
    dx = 6
    phase = leg_phase % 4
    left_off = (-dx, 4) if phase in {0, 3} else (-dx, 1)
    right_off = (dx, 4) if phase in {1, 2} else (dx, 1)

    pygame.draw.line(surf, pygame.Color("#2e3440"), (w // 2 - 6, leg_y), (w // 2 - 6 + left_off[0] // 3, leg_y + left_off[1]), 4)
    pygame.draw.line(surf, pygame.Color("#2e3440"), (w // 2 + 6, leg_y), (w // 2 + 6 + right_off[0] // 3, leg_y + right_off[1]), 4)

    # Arms
    arm_y = body.top + 10
    pygame.draw.line(surf, pygame.Color("#2e3440"), (body.left + 3, arm_y), (body.left - 6, arm_y + 3), 4)
    pygame.draw.line(surf, pygame.Color("#2e3440"), (body.right - 3, arm_y), (body.right + 6, arm_y + 3), 4)

    return surf
