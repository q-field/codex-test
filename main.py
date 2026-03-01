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
PLAYER_SPEED = 360
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
ALIEN_SPEED_PER_KILL = 4
ALIEN_SHOT_INTERVAL_RANGE_MS = (500, 1200)

BULLET_SIZE = (6, 16)
PLAYER_BULLET_SPEED = -540
ALIEN_BULLET_SPEED = 260

HUD_TOP_MARGIN = 8

BG_COLOR = (10, 12, 20)
PLAYER_COLOR = (120, 255, 150)
PLAYER_HIT_FLASH = (255, 150, 150)
ALIEN_COLOR = (120, 200, 255)
PLAYER_BULLET_COLOR = (255, 255, 120)
ALIEN_BULLET_COLOR = (255, 120, 120)
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


class SpaceInvaders:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Space Invaders - Pygame")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 24)

        self.running = True
        self.state = "start"  # start | playing | win | lose

        self.player = Ship(
            x=WIDTH // 2 - PLAYER_SIZE[0] // 2,
            y=PLAYER_START_Y,
            w=PLAYER_SIZE[0],
            h=PLAYER_SIZE[1],
        )
        self.player_lives = PLAYER_LIVES
        self.player_hit_flash_until = 0

        self.player_bullet: Bullet | None = None
        self.alien_bullets: list[Bullet] = []
        self.last_player_shot_time = 0
        self.next_alien_shot_at = 0

        self.aliens = self._build_aliens()
        self.alien_dir = 1
        self.score = 0

    def _build_aliens(self) -> list[pygame.Rect]:
        aliens: list[pygame.Rect] = []
        for row in range(ALIEN_ROWS):
            for col in range(ALIEN_COLS):
                x = ALIEN_START[0] + col * (ALIEN_SIZE[0] + ALIEN_GAP[0])
                y = ALIEN_START[1] + row * (ALIEN_SIZE[1] + ALIEN_GAP[1])
                aliens.append(pygame.Rect(x, y, ALIEN_SIZE[0], ALIEN_SIZE[1]))
        return aliens

    def _schedule_next_alien_shot(self) -> None:
        delay = random.randint(*ALIEN_SHOT_INTERVAL_RANGE_MS)
        self.next_alien_shot_at = pygame.time.get_ticks() + delay

    def run(self) -> None:
        self._schedule_next_alien_shot()
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
        move_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x -= PLAYER_SPEED * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x += PLAYER_SPEED * dt

        self.player.x = max(0, min(WIDTH - self.player.w, self.player.x + move_x))

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

        speed = ALIEN_BASE_SPEED + (ALIEN_ROWS * ALIEN_COLS - len(self.aliens)) * ALIEN_SPEED_PER_KILL
        dx = int(self.alien_dir * speed * dt)
        if dx == 0:
            dx = self.alien_dir

        for alien in self.aliens:
            alien.x += dx

        if any(alien.right >= WIDTH - 12 or alien.left <= 12 for alien in self.aliens):
            self.alien_dir *= -1
            for alien in self.aliens:
                alien.y += ALIEN_DROP_PX

    def _maybe_fire_alien_bullet(self) -> None:
        now = pygame.time.get_ticks()
        if not self.aliens or now < self.next_alien_shot_at:
            return

        shooter = random.choice(self.aliens)
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

    def _handle_collisions(self) -> None:
        if self.player_bullet:
            hit_index = next(
                (i for i, alien in enumerate(self.aliens) if alien.colliderect(self.player_bullet.rect)),
                None,
            )
            if hit_index is not None:
                del self.aliens[hit_index]
                self.player_bullet = None
                self.score += 10

        player_rect = self.player.rect
        surviving_bullets: list[Bullet] = []
        for bullet in self.alien_bullets:
            if bullet.rect.colliderect(player_rect):
                self.player_lives -= 1
                self.player_hit_flash_until = pygame.time.get_ticks() + 120
            else:
                surviving_bullets.append(bullet)
        self.alien_bullets = surviving_bullets

    def _check_end_conditions(self) -> None:
        if not self.aliens:
            self.state = "win"
            return

        if self.player_lives <= 0:
            self.state = "lose"
            return

        lowest_alien = max(self.aliens, key=lambda alien: alien.bottom)
        if lowest_alien.bottom >= self.player.y:
            self.state = "lose"

    def _draw(self) -> None:
        self.screen.fill(BG_COLOR)

        player_color = PLAYER_HIT_FLASH if pygame.time.get_ticks() < self.player_hit_flash_until else PLAYER_COLOR
        pygame.draw.rect(self.screen, player_color, self.player.rect)

        for alien in self.aliens:
            pygame.draw.rect(self.screen, ALIEN_COLOR, alien)

        if self.player_bullet:
            pygame.draw.rect(self.screen, PLAYER_BULLET_COLOR, self.player_bullet.rect)

        for bullet in self.alien_bullets:
            pygame.draw.rect(self.screen, ALIEN_BULLET_COLOR, bullet.rect)

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
        self.screen.blit(score_surface, (16, HUD_TOP_MARGIN))
        self.screen.blit(lives_surface, (WIDTH - lives_surface.get_width() - 16, HUD_TOP_MARGIN))

    def _draw_center_text(self, message: str) -> None:
        overlay = self.font.render(message, True, TEXT_COLOR)
        rect = overlay.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(overlay, rect)

    def _restart(self) -> None:
        self.player.x = WIDTH // 2 - PLAYER_SIZE[0] // 2
        self.player.y = PLAYER_START_Y
        self.player_lives = PLAYER_LIVES
        self.player_bullet = None
        self.alien_bullets.clear()
        self.last_player_shot_time = 0
        self.player_hit_flash_until = 0

        self.aliens = self._build_aliens()
        self.alien_dir = random.choice([-1, 1])
        self.score = 0
        self.state = "playing"
        self._schedule_next_alien_shot()


if __name__ == "__main__":
    SpaceInvaders().run()
