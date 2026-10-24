"""Board canvas rendering, piece animations, hover indicators, and hint overlays."""

from __future__ import annotations

import math
import pygame
from agents.evaluation import WIN_SCORE
from game.board import Board
import gui.theme as T
from gui.animation import draw_disc

P1_COLOR = T.P1_DISC
P2_COLOR = T.P2_DISC


def board_pixel(row: int, col: int) -> tuple[int, int]:
    """Convert grid (row, col) to screen pixel center (x, y)."""
    x = T.BOARD_LEFT + col * T.CELL_SIZE + T.CELL_SIZE // 2
    y = T.BOARD_TOP + (T.BOARD_ROWS - 1 - row) * T.CELL_SIZE + T.CELL_SIZE // 2
    return x, y


def darken(color: tuple[int, int, int], factor: float = 0.50) -> tuple[int, int, int]:
    return tuple(int(c * factor) for c in color)  # type: ignore[return-value]


def _lerp_color(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_background(surf: pygame.Surface, t_anim: float = 0.0) -> None:
    """Fill the window with the flat background colour (``t_anim`` kept for API stability)."""
    surf.fill(T.BG)


def draw_board(
    surf: pygame.Surface,
    board: Board,
    win_cells: list[tuple[int, int]],
    skip_cell: tuple[int, int] | None = None,
    ghost_col: int | None = None,
    ghost_player: int = 1,
    t_anim: float = 0.0,
) -> None:
    """Draw the board slab with real round holes, discs, ghost preview and win rings."""
    bw = T.BOARD_COLS * T.CELL_SIZE
    bh = T.BOARD_ROWS * T.CELL_SIZE
    panel = pygame.Rect(T.BOARD_LEFT - 12, T.BOARD_TOP - 12, bw + 24, bh + 24)

    # Soft drop shadow, then the slab with a darker edge
    shadow = pygame.Surface((panel.width + 20, panel.height + 20), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, T.SHADOW_ALPHA), shadow.get_rect(), border_radius=26)
    surf.blit(shadow, (panel.x - 10, panel.y - 2))
    pygame.draw.rect(surf, T.BOARD_FRAME, panel, border_radius=18)
    pygame.draw.rect(surf, T.BOARD_BG, panel.inflate(-6, -6), border_radius=15)

    win_set = set(win_cells)

    ghost_row: int | None = None
    if ghost_col is not None and ghost_col in board.legal_moves():
        for r in range(T.BOARD_ROWS):
            if board.grid[r][ghost_col] == 0:
                ghost_row = r
                break

    for row in range(T.BOARD_ROWS):
        for col in range(T.BOARD_COLS):
            cx, cy = board_pixel(row, col)
            cell = board.grid[row][col]

            # Hole: dark rim for depth, then the background shows through
            pygame.draw.circle(surf, T.BOARD_FRAME, (cx, cy), T.DISC_RADIUS + 4)
            pygame.draw.circle(surf, T.EMPTY, (cx, cy), T.DISC_RADIUS + 1)

            if skip_cell and (row, col) == skip_cell:
                continue

            if cell == 0:
                if ghost_col == col and ghost_row == row:
                    g_color = P1_COLOR if ghost_player == 1 else P2_COLOR
                    ghost = pygame.Surface((T.DISC_RADIUS * 2 + 4,) * 2, pygame.SRCALPHA)
                    pygame.draw.circle(ghost, (*g_color, 70),
                                       (T.DISC_RADIUS + 2, T.DISC_RADIUS + 2), T.DISC_RADIUS - 2)
                    surf.blit(ghost, (cx - T.DISC_RADIUS - 2, cy - T.DISC_RADIUS - 2))
            else:
                color = P1_COLOR if cell == 1 else P2_COLOR
                draw_disc(surf, (cx, cy), color)
                if (row, col) in win_set:
                    pygame.draw.circle(surf, (255, 255, 255), (cx, cy), T.DISC_RADIUS + 4, width=4)


def column_from_x(x: int) -> int | None:
    """Map window x-coordinate to a board column index (0-6) or None."""
    bx = x - T.BOARD_LEFT
    if 0 <= bx < T.BOARD_COLS * T.CELL_SIZE:
        return bx // T.CELL_SIZE
    return None


def draw_hover_arrow(
    surf: pygame.Surface,
    col: int,
    color: tuple[int, int, int],
    t_anim: float = 0.0,
) -> None:
    """Draw a bouncing guide chevron above the active hover column."""
    cx, _ = board_pixel(T.BOARD_ROWS - 1, col)
    bob = int(math.sin(t_anim * 5.5) * 4)
    top_y = T.BOARD_TOP - 26 + bob
    pygame.draw.polygon(surf, color, [(cx, top_y + 18), (cx - 12, top_y), (cx + 12, top_y)])
    pygame.draw.polygon(surf, (*color, 90),
                        [(cx, top_y + 20), (cx - 14, top_y - 2), (cx + 14, top_y - 2)], 2)


def draw_column_scores(surf: pygame.Surface, fonts: dict, column_scores: dict[int, float]) -> None:
    """Draw heatmap bars above each column showing normalised move quality."""
    bar_max_h = 24
    for col, score in column_scores.items():
        cx, _ = board_pixel(T.BOARD_ROWS - 1, col)
        norm = max(0.0, min(1.0, (score + 1.0) / 2.0))
        bar_h = max(2, int(norm * bar_max_h))
        bar_y = T.BOARD_TOP - 56
        if norm >= 0.6:
            color = _lerp_color(P2_COLOR, T.WIN_GLOW, (norm - 0.6) / 0.4)
        elif norm >= 0.4:
            color = _lerp_color(P1_COLOR, P2_COLOR, (norm - 0.4) / 0.2)
        else:
            color = _lerp_color(T.DIM_TEXT, P1_COLOR, norm / 0.4)
        pygame.draw.rect(surf, color,
                         pygame.Rect(cx - 14, bar_y + (bar_max_h - bar_h), 28, bar_h),
                         border_radius=3)
        pct_surf = fonts["sm"].render(f"{norm:.0%}", True, color)
        surf.blit(pct_surf, pct_surf.get_rect(center=(cx, bar_y - 12)))


def draw_hint_overlay(
    surf: pygame.Surface,
    fonts: dict,
    hint_scores: dict[int, int],
    hint_reason: str,
) -> None:
    """Render per-column score chips, a highlight on the best column and the reason card."""
    if not hint_scores:
        return
    best_col = max(hint_scores, key=lambda c: hint_scores[c])

    # Soft highlight behind the best column (drawn first so chips stay crisp)
    cx, _ = board_pixel(T.BOARD_ROWS - 1, best_col)
    col_rect = pygame.Rect(cx - T.DISC_RADIUS - 8, T.BOARD_TOP - 10,
                           (T.DISC_RADIUS + 8) * 2, T.BOARD_ROWS * T.CELL_SIZE + 20)
    halo = pygame.Surface(col_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(halo, (*T.WIN_GLOW, 40), halo.get_rect(), border_radius=14)
    pygame.draw.rect(halo, (*T.WIN_GLOW, 190), halo.get_rect(), width=3, border_radius=14)
    surf.blit(halo, col_rect.topleft)

    for col, score in hint_scores.items():
        ccx, _ = board_pixel(T.BOARD_ROWS - 1, col)
        box = pygame.Rect(0, 0, 58, 26)
        box.midtop = (ccx, T.BOARD_TOP - 64)

        if score >= WIN_SCORE:
            label, color = "Win", T.WIN_GLOW
        elif score <= -WIN_SCORE:
            label, color = "Loss", P1_COLOR
        else:
            label = f"{score:+d}" if score else "0"
            color = T.TEXT if score > 0 else (T.DIM_TEXT if score == 0 else P1_COLOR)

        is_best = col == best_col
        pygame.draw.rect(surf, T.SURFACE_HI if is_best else T.SURFACE, box, border_radius=13)
        pygame.draw.rect(surf, T.WIN_GLOW if is_best else T.BORDER, box,
                         width=2 if is_best else 1, border_radius=13)
        txt = fonts["sm"].render(label, True, color)
        surf.blit(txt, txt.get_rect(center=box.center))

    if hint_reason:
        text = fonts["md"].render(hint_reason, True, T.TEXT)
        card = pygame.Rect(T.BOARD_LEFT - 12, T.BOARD_TOP + T.BOARD_ROWS * T.CELL_SIZE + 22,
                           min(T.BOARD_COLS * T.CELL_SIZE + 24, text.get_width() + 56), 38)
        pygame.draw.rect(surf, T.SURFACE, card, border_radius=12)
        pygame.draw.rect(surf, T.BORDER, card, width=1, border_radius=12)
        pygame.draw.circle(surf, T.WIN_GLOW, (card.left + 20, card.centery), 5)
        surf.blit(text, (card.left + 36, card.centery - text.get_height() // 2))
