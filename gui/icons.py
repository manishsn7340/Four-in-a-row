"""Small icons and agent avatars drawn with pygame shapes, so no emoji font is needed."""

from __future__ import annotations

import math

import pygame

WHITE = (220, 235, 255)


def _canvas(size: int) -> pygame.Surface:
    return pygame.Surface((size, size), pygame.SRCALPHA)


def make_bulb_icon(color: tuple = WHITE, size: int = 18) -> pygame.Surface:
    s, cx = _canvas(size), size // 2
    pygame.draw.circle(s, color, (cx, int(size * 0.35)), int(size * 0.28))
    neck = int(size * 0.32)
    pygame.draw.rect(s, color, (cx - neck // 2, int(size * 0.52), neck, int(size * 0.22)))
    pygame.draw.line(s, color, (cx - neck // 2, int(size * 0.85)), (cx + neck // 2, int(size * 0.85)))
    return s


def make_sound_icon(color: tuple = WHITE, size: int = 18, muted: bool = False) -> pygame.Surface:
    s, cy = _canvas(size), size // 2
    pygame.draw.rect(s, color, (2, cy - 3, 4, 6))
    pygame.draw.polygon(s, color, [(6, cy - 3), (11, cy - 7), (11, cy + 7), (6, cy + 3)])
    if muted:
        pygame.draw.line(s, color, (13, cy - 5), (size - 2, cy + 5), 2)
        pygame.draw.line(s, color, (13, cy + 5), (size - 2, cy - 5), 2)
    else:
        pygame.draw.arc(s, color, (8, cy - 5, 8, 10), -1.1, 1.1)
        pygame.draw.arc(s, color, (8, cy - 8, 13, 16), -1.0, 1.0)
    return s


def make_chart_icon(color: tuple = WHITE, size: int = 18) -> pygame.Surface:
    s = _canvas(size)
    for x, h in ((2, 5), (7, 9), (12, 14)):
        pygame.draw.rect(s, color, (x, size - 2 - h, 3, h), border_radius=1)
    return s


def make_demo_icon(color: tuple = WHITE, size: int = 18) -> pygame.Surface:
    s, cy = _canvas(size), size // 2
    pygame.draw.polygon(s, color, [(4, cy - 6), (size - 4, cy), (4, cy + 6)])
    return s


def make_puzzle_icon(color: tuple = WHITE, size: int = 18) -> pygame.Surface:
    s, m = _canvas(size), max(2, size // 6)
    pygame.draw.rect(s, color, (m, m, size - 2 * m, size - 2 * m), border_radius=3)
    pygame.draw.circle(s, color, (size // 2, m), m)
    pygame.draw.circle(s, color, (size - m, size // 2), m)
    return s


def _polygon(cx: int, cy: int, radii: list[float], start: float) -> list[tuple[int, int]]:
    """Points evenly spaced round (cx, cy), cycling through `radii`."""
    n = len(radii)
    return [(int(cx + r * math.cos(start + i * math.tau / n)),
             int(cy + r * math.sin(start + i * math.tau / n))) for i, r in enumerate(radii)]


def draw_agent_avatar(surf: pygame.Surface, name: str, cx: int, cy: int, size: int = 52) -> None:
    """Each AI personality gets a shape: Rookie a smiley, Tactician a diamond,
    Grandmaster a hexagon, Gambler a star."""
    layer = _canvas(size + 8)
    c, r = (size + 8) // 2, size // 2
    name = name.lower()
    if "rookie" in name or "random" in name:
        color = (160, 220, 120)
        pygame.draw.circle(layer, (*color, 55), (c, c), r)
        pygame.draw.circle(layer, color, (c, c), r, 2)
        for dx in (-size // 6, size // 6):
            pygame.draw.circle(layer, color, (c + dx, c - size // 8), 2)
        pygame.draw.lines(layer, color, False, [(c - size // 5, c + size // 8), (c, c + size // 4),
                                                (c + size // 5, c + size // 8)], 2)
        surf.blit(layer, layer.get_rect(center=(cx, cy)))
        return
    if "tactician" in name or "alpha" in name:
        color, points = (100, 180, 255), _polygon(c, c, [r] * 4, -math.pi / 2)
    elif "grand" in name:
        color, points = (255, 160, 60), _polygon(c, c, [r] * 6, math.pi / 6)
        pygame.draw.polygon(layer, (*color, 120), _polygon(c, c, [r // 2] * 6, math.pi / 6))
    else:
        color, points = (200, 100, 255), _polygon(c, c, [r, r // 2] * 8, -math.pi / 2)
    pygame.draw.polygon(layer, (*color, 55), points)
    pygame.draw.polygon(layer, color, points, 2)
    surf.blit(layer, layer.get_rect(center=(cx, cy)))
