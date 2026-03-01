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

WIN_WAVES = 3
HUD_TOP_MARGIN = 8

BG_COLOR = (10, 12, 20)
PLAYER_COLOR = (120, 255, 150)
PLAYER_HIT_FLASH = (255, 150, 150)
ALIEN_COLOR = (120, 200, 255)
PLAYER_BULLET_COLOR = (255, 255, 120)
ALIEN_BULLET_COLOR = (255, 120, 120)
BUNKER_COLOR = (150, 255, 180)
TEXT_COLOR = (245, 245, 245)


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


class SpaceInvaders:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Space Invaders - Pygame")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 24)

        self.player_sprite = self._make_player_sprite()
        self.alien_sprite = self._make_alien_sprite()
        self.player_bullet_sprite, self.alien_bullet_sprite = self._make_bullet_sprites()

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
        self.aliens: list[pygame.Rect] = []
        self.alien_dir = 1
        self.bunkers: list[BunkerCell] = []
        self._start_wave(reset_score=False)

    def _make_player_sprite(self) -> pygame.Surface:
        surface = pygame.Surface(PLAYER_SIZE, pygame.SRCALPHA)
        w, h = PLAYER_SIZE
        points = [(w // 2, 0), (w - 4, h - 2), (4, h - 2)]
        pygame.draw.polygon(surface, PLAYER_COLOR, points)
        pygame.draw.rect(surface, (40, 90, 55), (w // 2 - 5, h // 2, 10, h // 2 - 2))
        return surface

    def _make_alien_sprite(self) -> pygame.Surface:
        surface = pygame.Surface(ALIEN_SIZE, pygame.SRCALPHA)
        w, h = ALIEN_SIZE
        pygame.draw.rect(surface, ALIEN_COLOR, (6, 6, w - 12, h - 10), border_radius=4)
        pygame.draw.circle(surface, (20, 30, 50), (w // 3, h // 2), 3)
        pygame.draw.circle(surface, (20, 30, 50), (2 * w // 3, h // 2), 3)
        pygame.draw.rect(surface, (90, 150, 200), (10, h - 6, 6, 4))
        pygame.draw.rect(surface, (90, 150, 200), (w - 16, h - 6, 6, 4))
        return surface

    def _make_bullet_sprites(self) -> tuple[pygame.Surface, pygame.Surface]:
        player = pygame.Surface(BULLET_SIZE, pygame.SRCALPHA)
        alien = pygame.Surface(BULLET_SIZE, pygame.SRCALPHA)
        pygame.draw.rect(player, PLAYER_BULLET_COLOR, (0, 0, BULLET_SIZE[0], BULLET_SIZE[1]), border_radius=2)
        pygame.draw.rect(player, (255, 255, 255), (2, 2, 2, BULLET_SIZE[1] - 4))
        pygame.draw.rect(alien, ALIEN_BULLET_COLOR, (0, 0, BULLET_SIZE[0], BULLET_SIZE[1]), border_radius=2)
        pygame.draw.rect(alien, (255, 180, 180), (2, 2, 2, BULLET_SIZE[1] - 4))
        return player, alien

    def _build_aliens(self) -> list[pygame.Rect]:
        aliens: list[pygame.Rect] = []
        for row in range(ALIEN_ROWS):
            for col in range(ALIEN_COLS):
                x = ALIEN_START[0] + col * (ALIEN_SIZE[0] + ALIEN_GAP[0])
                y = ALIEN_START[1] + row * (ALIEN_SIZE[1] + ALIEN_GAP[1])
                aliens.append(pygame.Rect(x, y, ALIEN_SIZE[0], ALIEN_SIZE[1]))
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
                    # carve a tiny arch in lower middle
                    if row >= rows - 2 and cols // 3 <= col <= cols - cols // 3:
                        continue
                    rect = pygame.Rect(
                        left + col * BUNKER_CELL,
                        BUNKER_Y + row * BUNKER_CELL,
                        BUNKER_CELL,
                        BUNKER_CELL,
                    )
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
        self._schedule_next_alien_shot()

    def _schedule_next_alien_shot(self) -> None:
        min_delay, max_delay = ALIEN_SHOT_INTERVAL_BASE
        reduction = (self.wave - 1) * 70
        min_delay = max(ALIEN_SHOT_INTERVAL_MIN[0], min_delay - reduction)
        max_delay = max(ALIEN_SHOT_INTERVAL_MIN[1], max_delay - reduction)
        delay = random.randint(min_delay, max_delay)
        self.next_alien_shot_at = pygame.time.get_ticks() + delay

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
            alien.x += dx

        if any(alien.right >= WIDTH - 12 or alien.left <= 12 for alien in self.aliens):
            self.alien_dir *= -1
            for alien in self.aliens:
                alien.y += ALIEN_DROP_PX

    def _select_alien_shooter(self) -> pygame.Rect | None:
        if not self.aliens:
            return None
        by_col: dict[int, pygame.Rect] = {}
        for alien in self.aliens:
            col = round((alien.x - ALIEN_START[0]) / (ALIEN_SIZE[0] + ALIEN_GAP[0]))
            if col not in by_col or alien.y > by_col[col].y:
                by_col[col] = alien
        return random.choice(list(by_col.values())) if by_col else None

    def _maybe_fire_alien_bullet(self) -> None:
        now = pygame.time.get_ticks()
        if not self.aliens or now < self.next_alien_shot_at:
            return

        shooter = self._select_alien_shooter()
        if shooter is None:
            return

        self.alien_bullets.append(
            Bullet(
                x=shooter.centerx - BULLET_SIZE[0] / 2,
                y=shooter.bottom,
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
            if self._damage_bunker(bullet_rect):
                self.player_bullet = None
            else:
                hit_index = next((i for i, alien in enumerate(self.aliens) if alien.colliderect(bullet_rect)), None)
                if hit_index is not None:
                    del self.aliens[hit_index]
                    self.player_bullet = None
                    self.score += 10 + (self.wave - 1) * 2

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
            lowest_alien = max(self.aliens, key=lambda alien: alien.bottom)
            if lowest_alien.bottom >= self.player.y:
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
            color = (min(255, BUNKER_COLOR[0]), min(255, shade), min(255, BUNKER_COLOR[2]))
            pygame.draw.rect(self.screen, color, cell.rect)

        player_color = PLAYER_HIT_FLASH if pygame.time.get_ticks() < self.player_hit_flash_until else None
        if player_color:
            flash = self.player_sprite.copy()
            flash.fill(player_color, special_flags=pygame.BLEND_RGBA_MULT)
            self.screen.blit(flash, self.player.rect.topleft)
        else:
            self.screen.blit(self.player_sprite, self.player.rect.topleft)

        for alien in self.aliens:
            self.screen.blit(self.alien_sprite, alien.topleft)

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
        self.state = "playing"
        self._start_wave(reset_score=True)


if __name__ == "__main__":
    SpaceInvaders().run()
