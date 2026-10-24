"""Disc drop, win-pulse animations, particle burst, and background starfield."""

from __future__ import annotations

import math
import random

import pygame

import gui.theme as T


# ── Easing ────────────────────────────────────────────────────────────────────

def _bounce_out(t: float) -> float:
    """Ease-out bounce with natural damping."""
    if t < 1 / 2.75:
        return 7.5625 * t * t
    elif t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375


def _cell_center(row: int, col: int) -> tuple[int, int]:
    x = T.BOARD_LEFT + col * T.CELL_SIZE + T.CELL_SIZE // 2
    y = T.BOARD_TOP + (T.BOARD_ROWS - 1 - row) * T.CELL_SIZE + T.CELL_SIZE // 2
    return x, y


def _darken(color: tuple[int, int, int], factor: float = 0.50) -> tuple[int, int, int]:
    return tuple(int(c * factor) for c in color)  # type: ignore[return-value]


# ── Starfield ─────────────────────────────────────────────────────────────────

_STAR_PALETTE = [
    (180, 215, 255),  # icy blue
    (245, 210, 255),  # lavender
    (255, 240, 200),  # warm starlight
    (140, 255, 230),  # aqua teal
    (255, 190, 200),  # peach rose
]


def draw_disc(
    surf: pygame.Surface,
    center: tuple[int, int],
    color: tuple[int, int, int],
    radius: int = T.DISC_RADIUS,
) -> None:
    """Draw one flat-shaded disc: rim, face, soft highlight and a colour-blind marker."""
    cx, cy = center
    pygame.draw.circle(surf, _darken(color, 0.72), (cx, cy), radius)
    pygame.draw.circle(surf, color, (cx, cy), radius - 3)
    pygame.draw.circle(surf, _darken(color, 0.86), (cx, cy), radius - 11, width=2)
    hl = tuple(min(255, c + 38) for c in color)
    pygame.draw.circle(surf, hl, (cx - radius // 3, cy - radius // 3), radius // 6)
    # Marker so players stay distinguishable without colour: dot (P1) / ring (P2)
    marker = _darken(color, 0.62)
    if color == T.P1_DISC:
        pygame.draw.circle(surf, marker, (cx, cy), 7)
    else:
        pygame.draw.circle(surf, marker, (cx, cy), 12, width=3)


class Starfield:
    """A parallax star field with multi-tint twinkle stars drifting smoothly."""
    _rng = random.Random(7)

    def __init__(self, n: int = 150) -> None:
        self.stars = [
            [
                self._rng.randint(0, T.WIN_W),     # x
                self._rng.randint(0, T.WIN_H),     # y
                self._rng.uniform(0.4, 2.2),       # speed
                self._rng.randint(1, 3),           # size
                self._rng.uniform(0.0, math.tau),  # twinkle phase
                self._rng.choice(_STAR_PALETTE),   # tint
            ]
            for _ in range(n)
        ]

    def update(self, dt: float) -> None:
        for s in self.stars:
            s[1] += s[2] * dt * 18
            s[4] += dt * 3.0  # advance twinkle phase
            if s[1] > T.WIN_H:
                s[1] = 0
                s[0] = self._rng.randint(0, T.WIN_W)

    def draw(self, surf: pygame.Surface) -> None:
        for x, y, _, sz, phase, tint in self.stars:
            twinkle = 0.6 + 0.4 * math.sin(phase)
            col = tuple(int(c * twinkle) for c in tint)
            pygame.draw.circle(surf, col, (int(x), int(y)), sz)


# ── DiscDrop ──────────────────────────────────────────────────────────────────

class DiscDrop:
    """Animate a disc falling from above the board with realistic bounce ease."""
    DURATION = 0.28

    def __init__(self, col: int, row: int, color: tuple[int, int, int]) -> None:
        self.col = col
        self.row = row
        self.color = color
        cx, end_y = _cell_center(row, col)
        self.x = cx
        self.start_y = T.BOARD_TOP - T.CELL_SIZE
        self.end_y = end_y
        self.current_y = float(self.start_y)
        self.elapsed = 0.0
        self.done = False

    def update(self, dt: float) -> None:
        if self.done:
            return
        self.elapsed += dt
        t = min(self.elapsed / self.DURATION, 1.0)
        self.current_y = self.start_y + (self.end_y - self.start_y) * _bounce_out(t)
        if t >= 1.0:
            self.done = True

    def draw(self, surf: pygame.Surface) -> None:
        draw_disc(surf, (self.x, int(self.current_y)), self.color)


class WinPulse:
    """Pulsing teal glow rings and a radiant laser line connecting the 4 winning cells."""
    PERIOD = 0.65

    def __init__(self, win_cells: list[tuple[int, int]]) -> None:
        # Sort cells so line traverses in order
        sorted_cells = sorted(win_cells)
        self.centers = [_cell_center(r, c) for r, c in sorted_cells]
        self.elapsed = 0.0

    def update(self, dt: float) -> None:
        self.elapsed += dt

    def draw(self, surf: pygame.Surface) -> None:
        t = (math.sin(self.elapsed * 2 * math.pi / self.PERIOD) + 1) / 2
        radius = int(T.DISC_RADIUS + 4 + t * 16)
        alpha = int(90 + t * 165)

        # 1. Radiant connector laser line across winning discs
        if len(self.centers) >= 2:
            p_start = self.centers[0]
            p_end = self.centers[-1]
            # Outer thick glow
            line_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            pygame.draw.line(line_surf, (*T.WIN_GLOW, int(80 + t * 90)),
                             p_start, p_end, 14)
            pygame.draw.line(line_surf, (*T.WIN_GLOW, int(150 + t * 80)),
                             p_start, p_end, 6)
            # Inner bright white/cyan core
            pygame.draw.line(line_surf, (240, 255, 255, 220), p_start, p_end, 2)
            surf.blit(line_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # 2. Glowing pulse rings on winning discs
        for cx, cy in self.centers:
            glow = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*T.WIN_GLOW, alpha),
                               (radius + 4, radius + 4), radius, width=7)
            surf.blit(glow, (cx - radius - 4, cy - radius - 4))


# ── Confetti burst ────────────────────────────────────────────────────────────

_CONFETTI_COLORS = [
    (255, 80,  80),   (255, 220, 50), (50, 230, 180),
    (100, 140, 255),  (255, 140, 40), (210, 100, 255),
    (255, 255, 255),  (80, 250, 160),
]


class ConfettiBurst:
    """Delightful particle burst from each winning cell."""
    _rng = random.Random(42)

    def __init__(self, win_cells: list[tuple[int, int]]) -> None:
        self.particles: list[list] = []
        for r, c in win_cells:
            cx, cy = _cell_center(r, c)
            for _ in range(24):
                angle = self._rng.uniform(0, math.tau)
                speed = self._rng.uniform(70, 300)
                color = self._rng.choice(_CONFETTI_COLORS)
                size = self._rng.randint(3, 7)
                self.particles.append([
                    float(cx), float(cy),
                    math.cos(angle) * speed, math.sin(angle) * speed,
                    color, size, 1.0,  # x, y, vx, vy, color, size, alpha
                ])
        self.done = False

    def update(self, dt: float) -> None:
        alive = False
        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 320 * dt  # gravity
            p[6] -= dt * 1.1  # gradual fade
            if p[6] > 0:
                alive = True
        self.done = not alive

    def draw(self, surf: pygame.Surface) -> None:
        for x, y, _, __, color, size, alpha in self.particles:
            if alpha <= 0:
                continue
            a = int(max(0, min(255, alpha * 255)))
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, a), (size, size), size)
            surf.blit(s, (int(x) - size, int(y) - size))
