"""gui/icons.py — Crisp procedural vector icons and agent avatars for Pygame.

Draws resolution-independent vector icons directly to Pygame surfaces.
Guaranteed to render smoothly without relying on OS emoji fonts or causing tofu boxes.
"""

from __future__ import annotations

import math
import pygame


def make_human_icon(color: tuple[int, int, int] = (255, 120, 120), size: int = 18) -> pygame.Surface:
    """Draw a smooth human head & shoulders silhouette."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = size // 2
    # Head
    pygame.draw.circle(surf, color, (cx, int(size * 0.28)), int(size * 0.22))
    # Shoulders
    body_rect = pygame.Rect(
        int(cx - size * 0.42),
        int(size * 0.55),
        int(size * 0.84),
        int(size * 0.45),
    )
    pygame.draw.ellipse(surf, color, body_rect)
    return surf


def make_robot_icon(color: tuple[int, int, int] = (255, 220, 80), size: int = 18) -> pygame.Surface:
    """Draw a retro robot head with antenna, visor, and glowing eyes."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = size // 2
    # Antenna
    pygame.draw.line(surf, color, (cx, 1), (cx, int(size * 0.25)), 1)
    pygame.draw.circle(surf, color, (cx, 1), 2)
    # Head block
    head_w = int(size * 0.75)
    head_h = int(size * 0.58)
    head_rect = pygame.Rect(cx - head_w // 2, int(size * 0.30), head_w, head_h)
    pygame.draw.rect(surf, color, head_rect, border_radius=3)
    # Eye sockets / visor
    eye_y = int(size * 0.50)
    eye_offset = int(size * 0.20)
    dark_bg = (12, 18, 45)
    pygame.draw.circle(surf, dark_bg, (cx - eye_offset, eye_y), 2)
    pygame.draw.circle(surf, dark_bg, (cx + eye_offset, eye_y), 2)
    return surf


def make_bulb_icon(color: tuple[int, int, int] = (50, 240, 180), size: int = 18) -> pygame.Surface:
    """Draw a glowing lightbulb idea icon."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = size // 2
    # Bulb globe
    pygame.draw.circle(surf, color, (cx, int(size * 0.35)), int(size * 0.28))
    # Bulb neck
    neck_w = int(size * 0.32)
    neck_h = int(size * 0.22)
    neck_rect = pygame.Rect(cx - neck_w // 2, int(size * 0.52), neck_w, neck_h)
    pygame.draw.rect(surf, color, neck_rect)
    # Screw base contacts
    base_col = (200, 220, 255)
    pygame.draw.line(surf, base_col, (cx - neck_w // 2, int(size * 0.80)), (cx + neck_w // 2, int(size * 0.80)), 1)
    pygame.draw.line(surf, base_col, (cx - 2, int(size * 0.90)), (cx + 2, int(size * 0.90)), 1)
    return surf


def make_sound_icon(color: tuple[int, int, int] = (50, 240, 180), size: int = 18, muted: bool = False) -> pygame.Surface:
    """Draw a speaker cone with sound waves or a mute cross."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cy = size // 2
    # Speaker box
    pygame.draw.rect(surf, color, (2, cy - 3, 4, 6))
    # Speaker cone
    pygame.draw.polygon(surf, color, [(6, cy - 3), (11, cy - 7), (11, cy + 7), (6, cy + 3)])

    if muted:
        # Red/coral slash
        pygame.draw.line(surf, (255, 80, 80), (13, cy - 5), (size - 2, cy + 5), 2)
        pygame.draw.line(surf, (255, 80, 80), (13, cy + 5), (size - 2, cy - 5), 2)
    else:
        # Sound arcs
        arc_rect1 = pygame.Rect(8, cy - 5, 8, 10)
        pygame.draw.arc(surf, color, arc_rect1, -1.1, 1.1, 1)
        arc_rect2 = pygame.Rect(8, cy - 8, 13, 16)
        pygame.draw.arc(surf, color, arc_rect2, -1.0, 1.0, 1)

    return surf


def make_chart_icon(color: tuple[int, int, int] = (220, 235, 255), size: int = 18) -> pygame.Surface:
    """Draw a mini 3-bar analytical graph."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    bot = size - 2
    bar_w = 3
    # Bar 1 (low)
    pygame.draw.rect(surf, color, (2, bot - 5, bar_w, 5), border_radius=1)
    # Bar 2 (mid)
    pygame.draw.rect(surf, color, (7, bot - 9, bar_w, 9), border_radius=1)
    # Bar 3 (high)
    pygame.draw.rect(surf, color, (12, bot - 14, bar_w, 14), border_radius=1)
    return surf


def make_demo_icon(color: tuple[int, int, int] = (220, 235, 255), size: int = 18) -> pygame.Surface:
    """Draw a play / presentation clapboard arrow."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cy = size // 2
    pts = [(4, cy - 6), (size - 4, cy), (4, cy + 6)]
    pygame.draw.polygon(surf, color, pts)
    return surf


def make_clock_icon(color: tuple[int, int, int] = (220, 235, 255), size: int = 18) -> pygame.Surface:
    """Draw a simple analog clock face for per-player timer display."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2
    r = size // 2 - 1
    pygame.draw.circle(surf, color, (cx, cy), r, 1)
    # Minute hand (pointing up)
    pygame.draw.line(surf, color, (cx, cy), (cx, cy - int(r * 0.6)), 1)
    # Hour hand (pointing to ~3 o'clock)
    pygame.draw.line(surf, color, (cx, cy), (cx + int(r * 0.4), cy), 1)
    return surf


def make_export_icon(color: tuple[int, int, int] = (220, 235, 255), size: int = 18) -> pygame.Surface:
    """Draw a small save/download arrow icon."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = size // 2
    # Arrow shaft + head pointing down
    pygame.draw.line(surf, color, (cx, 2), (cx, size - 5), 2)
    pygame.draw.polygon(surf, color, [(cx - 4, size - 7), (cx + 4, size - 7), (cx, size - 2)])
    # Base line
    pygame.draw.line(surf, color, (2, size - 2), (size - 2, size - 2), 1)
    return surf


# ─── Agent personality avatars ─────────────────────────────────────────────────

_AGENT_BG_ALPHA = 55


def draw_agent_avatar(
    surf: pygame.Surface,
    agent_name: str,
    cx: int,
    cy: int,
    size: int = 52,
) -> None:
    """Draw an agent avatar on a transparent layer so its soft fill blends in."""
    pad = 4
    layer = pygame.Surface((size + 2 * pad, size + 2 * pad), pygame.SRCALPHA)
    _draw_agent_shape(layer, agent_name, layer.get_width() // 2, layer.get_height() // 2, size)
    surf.blit(layer, (cx - layer.get_width() // 2, cy - layer.get_height() // 2))


def _draw_agent_shape(
    surf: pygame.Surface,
    agent_name: str,
    cx: int,
    cy: int,
    size: int,
) -> None:
    """Draw a distinct procedural geometric avatar for each agent personality."""
    name = agent_name.lower()

    if "rookie" in name or "random" in name:
        # Rookie: cheerful circle with smiley — naive and open
        color = (160, 220, 120)
        r = size // 2
        pygame.draw.circle(surf, (*color, _AGENT_BG_ALPHA), (cx, cy), r)
        pygame.draw.circle(surf, color, (cx, cy), r, 2)
        pygame.draw.circle(surf, color, (cx - size // 6, cy - size // 8), 2)
        pygame.draw.circle(surf, color, (cx + size // 6, cy - size // 8), 2)
        pts = [
            (cx - size // 5, cy + size // 8),
            (cx,             cy + size // 4),
            (cx + size // 5, cy + size // 8),
        ]
        pygame.draw.lines(surf, color, False, pts, 2)

    elif "tactician" in name or "alpha" in name or "alphabeta" in name:
        # Tactician: diamond — sharp and strategic
        color = (100, 180, 255)
        r = size // 2
        pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        pygame.draw.polygon(surf, (*color, _AGENT_BG_ALPHA), pts)
        pygame.draw.polygon(surf, color, pts, 2)
        pygame.draw.line(surf, (*color, 160), (cx, cy - r // 2), (cx, cy + r // 2), 1)
        pygame.draw.line(surf, (*color, 160), (cx - r // 2, cy), (cx + r // 2, cy), 1)

    elif "grandmaster" in name or "grand" in name:
        # Grandmaster: nested hexagon — complex and precise
        color = (255, 160, 60)
        r = size // 2
        pts_outer = [
            (int(cx + r * math.cos(math.pi / 6 + i * math.pi / 3)),
             int(cy + r * math.sin(math.pi / 6 + i * math.pi / 3)))
            for i in range(6)
        ]
        pts_inner = [
            (int(cx + (r // 2) * math.cos(math.pi / 6 + i * math.pi / 3)),
             int(cy + (r // 2) * math.sin(math.pi / 6 + i * math.pi / 3)))
            for i in range(6)
        ]
        pygame.draw.polygon(surf, (*color, _AGENT_BG_ALPHA), pts_outer)
        pygame.draw.polygon(surf, color, pts_outer, 2)
        pygame.draw.polygon(surf, (*color, 120), pts_inner)

    else:
        # Gambler / MCTS: starburst — chaotic and probabilistic
        color = (200, 100, 255)
        r_outer = size // 2
        r_inner = size // 4
        n_pts = 8
        pts = []
        for i in range(n_pts * 2):
            r = r_outer if i % 2 == 0 else r_inner
            angle = math.pi / n_pts * i - math.pi / 2
            pts.append((int(cx + r * math.cos(angle)), int(cy + r * math.sin(angle))))
        pygame.draw.polygon(surf, (*color, _AGENT_BG_ALPHA), pts)
        pygame.draw.polygon(surf, color, pts, 2)


def make_puzzle_icon(color: tuple[int, int, int] = (210, 160, 255), size: int = 18) -> pygame.Surface:
    """Draw a clean procedural interlocking puzzle piece icon with tabs."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    m = max(2, size // 6)
    body_sz = size - 2 * m
    pygame.draw.rect(surf, color, (m, m, body_sz, body_sz), border_radius=3)
    tab_r = max(2, size // 6)
    pygame.draw.circle(surf, color, (size // 2, m), tab_r)
    pygame.draw.circle(surf, color, (size - m, size // 2), tab_r)
    hi_col = (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2] + 50))
    pygame.draw.line(surf, hi_col, (m + 1, m + 1), (size - m - 1, m + 1), 1)
    pygame.draw.line(surf, hi_col, (m + 1, m + 1), (m + 1, size - m - 1), 1)
    return surf
