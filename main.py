import random
import sys
from dataclasses import dataclass

import pygame

# -----------------------------
# Tunable constants
# -----------------------------
WIDTH, HEIGHT = 800, 600
FPS = 60

PLAYER_SIZE = (60, 22)
PLAYER_MAX_SPEED = 360
PLAYER_ACCEL = 2200
PLAYER_FRICTION = 2600
PLAYER_START_Y = HEIGHT - 40
PLAYER_SHOT_COOLDOWN_MS = 220
PLAYER_LIVES = 3

ALIEN_ROWS = 5
ALIEN_COLS = 10
ALIEN_SIZE = (38, 24)
ALIEN_GAP = (16, 16)
ALIEN_START = (70, 80)
ALIEN_DROP_PX = 20
ALIEN_BASE_SPEED = 60
ALIEN_SPEED_PER_KILL = 2
ALIEN_WAVE_SPEED_BONUS = 6
ALIEN_SHOT_INTERVAL_BASE = (650, 1400)
ALIEN_SHOT_INTERVAL_MIN = (360, 700)

BULLET_SIZE = (6, 16)
PLAYER_BULLET_SPEED = -540
ALIEN_BULLET_SPEED = 260

BUNKER_COUNT = 4
BUNKER_WIDTH = 72
BUNKER_HEIGHT = 40
BUNKER_Y = HEIGHT - 140
BUNKER_CELL = 8
BUNKER_HP = 3

UFO_SIZE = (58, 24)
UFO_Y = 44
UFO_SPEED = 120
UFO_SPAWN_RANGE_MS = (7000, 12000)

WIN_WAVES = 3
HUD_TOP_MARGIN = 8
ANIM_TICK_MS = 400

BG_COLOR = (10, 12, 20)
INVADER_GREEN = (110, 255, 120)
PLAYER_HIT_FLASH = (255, 150, 150)
PLAYER_BULLET_COLOR = (255, 255, 120)
ALIEN_BULLET_COLOR = (255, 120, 120)
UFO_COLOR = (255, 80, 120)
TEXT_COLOR = (245, 245, 245)

ROW_SCORES = [30, 20, 20, 10, 10]


@dataclass
class Bullet:
    x: float
    y: float
    w: int
    h: int
    vy: float
    from_player: bool

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, dt: float) -> None:
        self.y += self.vy * dt


@dataclass
class Ship:
    x: float
    y: float
    w: int
    h: int

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)


@dataclass
class BunkerCell:
    rect: pygame.Rect
    hp: int = BUNKER_HP


@dataclass
class Alien:
    rect: pygame.Rect
    row: int


class SpaceInvaders:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Space Invaders - Pygame")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 24)

        self.player_sprite = self._make_player_sprite()
        self.alien_sprites = self._make_alien_sprites()
        self.player_bullet_sprite, self.alien_bullet_sprite = self._make_bullet_sprites()
        self.ufo_sprite = self._make_ufo_sprite()

        self.running = True
        self.state = "start"  # start | playing | win | lose

        self.player = Ship(
            x=WIDTH // 2 - PLAYER_SIZE[0] // 2,
            y=PLAYER_START_Y,
            w=PLAYER_SIZE[0],
            h=PLAYER_SIZE[1],
        )
        self.player_velocity_x = 0.0
        self.player_lives = PLAYER_LIVES
        self.player_hit_flash_until = 0

        self.player_bullet: Bullet | None = None
        self.alien_bullets: list[Bullet] = []
        self.last_player_shot_time = 0
        self.next_alien_shot_at = 0

        self.wave = 1
        self.score = 0
        self.aliens: list[Alien] = []
        self.alien_dir = 1
        self.bunkers: list[BunkerCell] = []

        self.ufo: pygame.Rect | None = None
        self.ufo_velocity_x = UFO_SPEED
        self.next_ufo_spawn_at = 0

        self._start_wave(reset_score=False)

    def _sprite_from_pattern(self, pattern: list[str], color: tuple[int, int, int], size: tuple[int, int]) -> pygame.Surface:
        rows = len(pattern)
        cols = len(pattern[0]) if rows else 1
        cell_w = max(1, size[0] // cols)
        cell_h = max(1, size[1] // rows)
        surface = pygame.Surface((cols * cell_w, rows * cell_h), pygame.SRCALPHA)
        for y, row in enumerate(pattern):
            for x, ch in enumerate(row):
                if ch not in {"0", " "}:
                    pygame.draw.rect(surface, color, (x * cell_w, y * cell_h, cell_w, cell_h))
        return pygame.transform.scale(surface, size)

    def _make_player_sprite(self) -> pygame.Surface:
        pattern = [
            "00000X00000",
            "0000XXX0000",
            "000XXXXX000",
            "00XXXXXXX00",
            "XXXXXXXXXXX",
            "XXXX000XXXX",
            "XXX00000XXX",
        ]
        return self._sprite_from_pattern(pattern, INVADER_GREEN, PLAYER_SIZE)

    def _make_alien_sprites(self) -> list[list[pygame.Surface]]:
        squid_a = [
            "0011001100",
            "0001111000",
            "0011111100",
            "0110110110",
            "1111111111",
            "1011111101",
            "0011001100",
            "0100000010",
        ]
        squid_b = [
            "0011001100",
            "0001111000",
            "0011111100",
            "0110110110",
            "1111111111",
            "0011111100",
            "0101001010",
            "1000000001",
        ]
        crab_a = [
            "0010000100",
            "0001001000",
            "0011111100",
            "0110110110",
            "1111111111",
            "1011111101",
            "1010000101",
            "0101001010",
        ]
        crab_b = [
            "0010000100",
            "1001001001",
            "1011111101",
            "1110110111",
            "1111111111",
            "0011111100",
            "0101001010",
            "1010000101",
        ]
        octo_a = [
            "0001111000",
            "0011111100",
            "0110110110",
            "1111111111",
            "1101111011",
            "1100000011",
            "0011001100",
            "0110011001",
        ]
        octo_b = [
            "0001111000",
            "0011111100",
            "0110110110",
            "1111111111",
            "1101111011",
            "0010000100",
            "0101001010",
            "1000000001",
        ]

        def s(p: list[str]) -> pygame.Surface:
            return self._sprite_from_pattern(p, INVADER_GREEN, ALIEN_SIZE)

        return [[s(squid_a), s(squid_b)], [s(crab_a), s(crab_b)], [s(octo_a), s(octo_b)]]

    def _make_bullet_sprites(self) -> tuple[pygame.Surface, pygame.Surface]:
        player = pygame.Surface(BULLET_SIZE, pygame.SRCALPHA)
        alien = pygame.Surface(BULLET_SIZE, pygame.SRCALPHA)
        pygame.draw.rect(player, PLAYER_BULLET_COLOR, (0, 0, BULLET_SIZE[0], BULLET_SIZE[1]), border_radius=2)
        pygame.draw.rect(player, (255, 255, 255), (2, 2, 2, BULLET_SIZE[1] - 4))
        pygame.draw.rect(alien, ALIEN_BULLET_COLOR, (0, 0, BULLET_SIZE[0], BULLET_SIZE[1]), border_radius=2)
        pygame.draw.rect(alien, (255, 180, 180), (2, 2, 2, BULLET_SIZE[1] - 4))
        return player, alien

    def _make_ufo_sprite(self) -> pygame.Surface:
        pattern = [
            "00011111111111000",
            "00111111111111100",
            "01101101101101110",
            "11111111111111111",
            "00111000000011100",
            "00000110011000000",
        ]
        return self._sprite_from_pattern(pattern, UFO_COLOR, UFO_SIZE)

    def _build_aliens(self) -> list[Alien]:
        aliens: list[Alien] = []
        for row in range(ALIEN_ROWS):
            for col in range(ALIEN_COLS):
                x = ALIEN_START[0] + col * (ALIEN_SIZE[0] + ALIEN_GAP[0])
                y = ALIEN_START[1] + row * (ALIEN_SIZE[1] + ALIEN_GAP[1])
                aliens.append(Alien(pygame.Rect(x, y, ALIEN_SIZE[0], ALIEN_SIZE[1]), row))
        return aliens

    def _build_bunkers(self) -> list[BunkerCell]:
        cells: list[BunkerCell] = []
        spacing = WIDTH // (BUNKER_COUNT + 1)
        cols = BUNKER_WIDTH // BUNKER_CELL
        rows = BUNKER_HEIGHT // BUNKER_CELL

        for idx in range(BUNKER_COUNT):
            left = spacing * (idx + 1) - BUNKER_WIDTH // 2
            for row in range(rows):
                for col in range(cols):
                    if row >= rows - 2 and cols // 3 <= col <= cols - cols // 3:
                        continue
                    rect = pygame.Rect(left + col * BUNKER_CELL, BUNKER_Y + row * BUNKER_CELL, BUNKER_CELL, BUNKER_CELL)
                    cells.append(BunkerCell(rect))
        return cells

    def _start_wave(self, reset_score: bool) -> None:
        if reset_score:
            self.score = 0
            self.wave = 1
        self.aliens = self._build_aliens()
        self.alien_dir = random.choice([-1, 1])
        self.player_bullet = None
        self.alien_bullets.clear()
        self.bunkers = self._build_bunkers()
        self.ufo = None
        self._schedule_next_ufo_spawn()
        self._schedule_next_alien_shot()

    def _schedule_next_alien_shot(self) -> None:
        min_delay, max_delay = ALIEN_SHOT_INTERVAL_BASE
        reduction = (self.wave - 1) * 70
        min_delay = max(ALIEN_SHOT_INTERVAL_MIN[0], min_delay - reduction)
        max_delay = max(ALIEN_SHOT_INTERVAL_MIN[1], max_delay - reduction)
        self.next_alien_shot_at = pygame.time.get_ticks() + random.randint(min_delay, max_delay)

    def _schedule_next_ufo_spawn(self) -> None:
        self.next_ufo_spawn_at = pygame.time.get_ticks() + random.randint(*UFO_SPAWN_RANGE_MS)

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            if self.state == "playing":
                self._update(dt)
            self._draw()
        pygame.quit()
        sys.exit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key in {pygame.K_RETURN, pygame.K_SPACE} and self.state == "start":
                    self.state = "playing"
                elif event.key == pygame.K_r and self.state in {"win", "lose"}:
                    self._restart()

    def _update(self, dt: float) -> None:
        self._update_player(dt)
        self._update_player_bullet(dt)
        self._update_alien_formation(dt)
        self._maybe_spawn_ufo()
        self._update_ufo(dt)
        self._maybe_fire_alien_bullet()
        self._update_alien_bullets(dt)
        self._handle_collisions()
        self._check_end_conditions()

    def _update_player(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        direction = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction += 1

        if direction != 0:
            self.player_velocity_x += direction * PLAYER_ACCEL * dt
        else:
            if self.player_velocity_x > 0:
                self.player_velocity_x = max(0, self.player_velocity_x - PLAYER_FRICTION * dt)
            elif self.player_velocity_x < 0:
                self.player_velocity_x = min(0, self.player_velocity_x + PLAYER_FRICTION * dt)

        self.player_velocity_x = max(-PLAYER_MAX_SPEED, min(PLAYER_MAX_SPEED, self.player_velocity_x))
        self.player.x += self.player_velocity_x * dt

        if self.player.x < 0:
            self.player.x = 0
            self.player_velocity_x = 0
        if self.player.x > WIDTH - self.player.w:
            self.player.x = WIDTH - self.player.w
            self.player_velocity_x = 0

        if keys[pygame.K_SPACE]:
            self._try_player_shoot()

    def _try_player_shoot(self) -> None:
        now = pygame.time.get_ticks()
        if self.player_bullet is not None:
            return
        if now - self.last_player_shot_time < PLAYER_SHOT_COOLDOWN_MS:
            return

        self.player_bullet = Bullet(
            x=self.player.x + self.player.w / 2 - BULLET_SIZE[0] / 2,
            y=self.player.y - BULLET_SIZE[1],
            w=BULLET_SIZE[0],
            h=BULLET_SIZE[1],
            vy=PLAYER_BULLET_SPEED,
            from_player=True,
        )
        self.last_player_shot_time = now

    def _update_player_bullet(self, dt: float) -> None:
        if self.player_bullet is None:
            return
        self.player_bullet.update(dt)
        if self.player_bullet.y + self.player_bullet.h < 0:
            self.player_bullet = None

    def _update_alien_formation(self, dt: float) -> None:
        if not self.aliens:
            return

        kills = ALIEN_ROWS * ALIEN_COLS - len(self.aliens)
        speed = ALIEN_BASE_SPEED + kills * ALIEN_SPEED_PER_KILL + (self.wave - 1) * ALIEN_WAVE_SPEED_BONUS
        dx = int(self.alien_dir * speed * dt)
        if dx == 0:
            dx = self.alien_dir

        for alien in self.aliens:
            alien.rect.x += dx

        if any(a.rect.right >= WIDTH - 12 or a.rect.left <= 12 for a in self.aliens):
            self.alien_dir *= -1
            for alien in self.aliens:
                alien.rect.y += ALIEN_DROP_PX

    def _select_alien_shooter(self) -> Alien | None:
        if not self.aliens:
            return None
        by_col: dict[int, Alien] = {}
        for alien in self.aliens:
            col = round((alien.rect.x - ALIEN_START[0]) / (ALIEN_SIZE[0] + ALIEN_GAP[0]))
            if col not in by_col or alien.rect.y > by_col[col].rect.y:
                by_col[col] = alien
        return random.choice(list(by_col.values())) if by_col else None

    def _maybe_spawn_ufo(self) -> None:
        now = pygame.time.get_ticks()
        if self.ufo is not None or now < self.next_ufo_spawn_at:
            return
        from_left = random.choice([True, False])
        x = -UFO_SIZE[0] if from_left else WIDTH
        self.ufo_velocity_x = UFO_SPEED if from_left else -UFO_SPEED
        self.ufo = pygame.Rect(x, UFO_Y, UFO_SIZE[0], UFO_SIZE[1])

    def _update_ufo(self, dt: float) -> None:
        if self.ufo is None:
            return
        self.ufo.x += int(self.ufo_velocity_x * dt)
        if self.ufo.right < 0 or self.ufo.left > WIDTH:
            self.ufo = None
            self._schedule_next_ufo_spawn()

    def _maybe_fire_alien_bullet(self) -> None:
        now = pygame.time.get_ticks()
        if not self.aliens or now < self.next_alien_shot_at:
            return

        shooter = self._select_alien_shooter()
        if shooter is None:
            return

        self.alien_bullets.append(
            Bullet(
                x=shooter.rect.centerx - BULLET_SIZE[0] / 2,
                y=shooter.rect.bottom,
                w=BULLET_SIZE[0],
                h=BULLET_SIZE[1],
                vy=ALIEN_BULLET_SPEED,
                from_player=False,
            )
        )
        self._schedule_next_alien_shot()

    def _update_alien_bullets(self, dt: float) -> None:
        for bullet in self.alien_bullets:
            bullet.update(dt)
        self.alien_bullets = [b for b in self.alien_bullets if b.y <= HEIGHT]

    def _damage_bunker(self, bullet_rect: pygame.Rect) -> bool:
        for cell in self.bunkers:
            if cell.hp > 0 and cell.rect.colliderect(bullet_rect):
                cell.hp -= 1
                return True
        return False

    def _handle_collisions(self) -> None:
        if self.player_bullet:
            bullet_rect = self.player_bullet.rect
            if self.ufo and bullet_rect.colliderect(self.ufo):
                self.score += 100
                self.ufo = None
                self.player_bullet = None
                self._schedule_next_ufo_spawn()
            elif self._damage_bunker(bullet_rect):
                self.player_bullet = None
            else:
                hit_index = next((i for i, alien in enumerate(self.aliens) if alien.rect.colliderect(bullet_rect)), None)
                if hit_index is not None:
                    row = self.aliens[hit_index].row
                    del self.aliens[hit_index]
                    self.player_bullet = None
                    self.score += ROW_SCORES[row] + (self.wave - 1) * 2

        player_rect = self.player.rect
        surviving_bullets: list[Bullet] = []
        for bullet in self.alien_bullets:
            bullet_rect = bullet.rect
            if self._damage_bunker(bullet_rect):
                continue
            if bullet_rect.colliderect(player_rect):
                self.player_lives -= 1
                self.player_hit_flash_until = pygame.time.get_ticks() + 120
            else:
                surviving_bullets.append(bullet)
        self.alien_bullets = surviving_bullets

        self.bunkers = [cell for cell in self.bunkers if cell.hp > 0]

    def _check_end_conditions(self) -> None:
        if self.player_lives <= 0:
            self.state = "lose"
            return

        if self.aliens:
            lowest_alien = max(self.aliens, key=lambda alien: alien.rect.bottom)
            if lowest_alien.rect.bottom >= self.player.y:
                self.state = "lose"
                return

        if not self.aliens:
            if self.wave >= WIN_WAVES:
                self.state = "win"
            else:
                self.wave += 1
                self._start_wave(reset_score=False)

    def _draw(self) -> None:
        self.screen.fill(BG_COLOR)

        for cell in self.bunkers:
            shade = 70 + cell.hp * 55
            pygame.draw.rect(self.screen, (70, min(255, shade), 95), cell.rect)

        if pygame.time.get_ticks() < self.player_hit_flash_until:
            flash = self.player_sprite.copy()
            flash.fill(PLAYER_HIT_FLASH, special_flags=pygame.BLEND_RGBA_MULT)
            self.screen.blit(flash, self.player.rect.topleft)
        else:
            self.screen.blit(self.player_sprite, self.player.rect.topleft)

        frame = (pygame.time.get_ticks() // ANIM_TICK_MS) % 2
        for alien in self.aliens:
            sprite_group = 0 if alien.row == 0 else (1 if alien.row <= 2 else 2)
            self.screen.blit(self.alien_sprites[sprite_group][frame], alien.rect.topleft)

        if self.ufo:
            self.screen.blit(self.ufo_sprite, self.ufo.topleft)

        if self.player_bullet:
            self.screen.blit(self.player_bullet_sprite, self.player_bullet.rect.topleft)

        for bullet in self.alien_bullets:
            self.screen.blit(self.alien_bullet_sprite, bullet.rect.topleft)

        self._draw_hud()

        if self.state == "start":
            self._draw_center_text("PRESS ENTER TO START")
        elif self.state == "win":
            self._draw_center_text("YOU WIN! Press R to play again")
        elif self.state == "lose":
            self._draw_center_text("GAME OVER! Press R to retry")

        pygame.display.flip()

    def _draw_hud(self) -> None:
        score_surface = self.font.render(f"Score: {self.score}", True, TEXT_COLOR)
        lives_surface = self.font.render(f"Lives: {self.player_lives}", True, TEXT_COLOR)
        wave_surface = self.font.render(f"Wave: {self.wave}/{WIN_WAVES}", True, TEXT_COLOR)
        self.screen.blit(score_surface, (16, HUD_TOP_MARGIN))
        self.screen.blit(lives_surface, (WIDTH - lives_surface.get_width() - 16, HUD_TOP_MARGIN))
        self.screen.blit(wave_surface, (WIDTH // 2 - wave_surface.get_width() // 2, HUD_TOP_MARGIN))

    def _draw_center_text(self, message: str) -> None:
        overlay = self.font.render(message, True, TEXT_COLOR)
        rect = overlay.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(overlay, rect)

    def _restart(self) -> None:
        self.player.x = WIDTH // 2 - PLAYER_SIZE[0] // 2
        self.player.y = PLAYER_START_Y
        self.player_velocity_x = 0
        self.player_lives = PLAYER_LIVES
        self.player_hit_flash_until = 0
        self.last_player_shot_time = 0
        self.player_bullet = None
        self.alien_bullets.clear()
        self.ufo = None
        self.state = "playing"
        self._start_wave(reset_score=True)


if __name__ == "__main__":
    SpaceInvaders().run()
