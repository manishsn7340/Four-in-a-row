"""Short animations: a falling disc, a pulse on the winning four, and confetti."""

from __future__ import annotations

import math
import random

import pygame

import gui.theme as T
from gui.board_view import board_pixel, draw_disc


def _bounce_out(t: float) -> float:
    """Standard 'bounce' easing curve for t in [0, 1]."""
    for edge, offset, base in ((1 / 2.75, 0, 0), (2 / 2.75, 1.5, 0.75),
                               (2.5 / 2.75, 2.25, 0.9375), (1.01, 2.625, 0.984375)):
        if t < edge:
            t -= offset / 2.75
            return 7.5625 * t * t + base
    return 1.0


class DiscDrop:
    DURATION = 0.28

    def __init__(self, col: int, row: int, color: tuple) -> None:
        self.col, self.row, self.color = col, row, color
        self.x, self.end_y = board_pixel(row, col)
        self.start_y = T.BOARD_TOP - T.CELL_SIZE
        self.elapsed = 0.0
        self.done = False

    def update(self, dt: float) -> None:
        self.elapsed += dt
        self.done = self.elapsed >= self.DURATION

    def draw(self, surf: pygame.Surface) -> None:
        t = min(self.elapsed / self.DURATION, 1.0)
        y = self.start_y + (self.end_y - self.start_y) * _bounce_out(t)
        draw_disc(surf, (self.x, int(y)), self.color)


class WinPulse:
    """A line through the four winning discs and rings that gently pulse."""
    PERIOD = 0.65

    def __init__(self, win_cells: list[tuple[int, int]]) -> None:
        self.centers = [board_pixel(r, c) for r, c in sorted(win_cells)]
        self.elapsed = 0.0

    def update(self, dt: float) -> None:
        self.elapsed += dt

    def draw(self, surf: pygame.Surface) -> None:
        t = (math.sin(self.elapsed * math.tau / self.PERIOD) + 1) / 2
        layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        pygame.draw.line(layer, (*T.WIN_GLOW, int(120 + 80 * t)), self.centers[0], self.centers[-1], 8)
        radius = int(T.DISC_RADIUS + 4 + 12 * t)
        for center in self.centers:
            pygame.draw.circle(layer, (*T.WIN_GLOW, int(90 + 165 * t)), center, radius, width=6)
        surf.blit(layer, (0, 0))


CONFETTI_COLORS = [(255, 80, 80), (255, 220, 50), (50, 230, 180), (100, 140, 255),
                   (255, 140, 40), (210, 100, 255), (255, 255, 255), (80, 250, 160)]


class ConfettiBurst:
    """Particles fly out of each winning cell, fall under gravity and fade."""
    _rng = random.Random(42)

    def __init__(self, win_cells: list[tuple[int, int]]) -> None:
        self.particles = []  # [x, y, vx, vy, color, size, life]
        for r, c in win_cells:
            x, y = board_pixel(r, c)
            for _ in range(24):
                angle, speed = self._rng.uniform(0, math.tau), self._rng.uniform(70, 300)
                self.particles.append([x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                                       self._rng.choice(CONFETTI_COLORS), self._rng.randint(3, 7), 1.0])
        self.done = False

    def update(self, dt: float) -> None:
        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 320 * dt
            p[6] -= 1.1 * dt
        self.done = all(p[6] <= 0 for p in self.particles)

    def draw(self, surf: pygame.Surface) -> None:
        layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        for x, y, _, _, color, size, life in self.particles:
            if life > 0:
                pygame.draw.circle(layer, (*color, int(255 * life)), (int(x), int(y)), size)
        surf.blit(layer, (0, 0))
