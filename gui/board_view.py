"""Drawing the board: holes, discs, hover preview and hint overlay."""

from __future__ import annotations

import math

import pygame

import gui.theme as T
from config import WIN_SCORE
from game.board import Board

BOARD_W = T.BOARD_COLS * T.CELL_SIZE
BOARD_H = T.BOARD_ROWS * T.CELL_SIZE


def board_pixel(row: int, col: int) -> tuple[int, int]:
    """Screen centre of a cell (row 0 is the bottom row)."""
    return (T.BOARD_LEFT + col * T.CELL_SIZE + T.CELL_SIZE // 2,
            T.BOARD_TOP + (T.BOARD_ROWS - 1 - row) * T.CELL_SIZE + T.CELL_SIZE // 2)


def column_from_x(x: int) -> int | None:
    col = (x - T.BOARD_LEFT) // T.CELL_SIZE
    return col if 0 <= x - T.BOARD_LEFT < BOARD_W else None


def shade(color: tuple, factor: float) -> tuple:
    return tuple(min(255, int(c * factor)) for c in color[:3])


def player_color(player: int) -> tuple:
    return T.P1_DISC if player == 1 else T.P2_DISC


def draw_disc(surf: pygame.Surface, center: tuple[int, int], color: tuple,
              radius: int = T.DISC_RADIUS) -> None:
    """A shaded disc with a dot (player 1) or ring (player 2) so colour-blind players can tell them apart."""
    pygame.draw.circle(surf, shade(color, 0.72), center, radius)
    pygame.draw.circle(surf, color, center, radius - 3)
    pygame.draw.circle(surf, shade(color, 0.86), center, radius - 11, width=2)
    pygame.draw.circle(surf, tuple(min(255, c + 38) for c in color),
                       (center[0] - radius // 3, center[1] - radius // 3), radius // 6)
    if color == T.P1_DISC:
        pygame.draw.circle(surf, shade(color, 0.62), center, 7)
    else:
        pygame.draw.circle(surf, shade(color, 0.62), center, 12, width=3)


def _shadow(surf: pygame.Surface, rect: pygame.Rect, radius: int) -> None:
    layer = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
    pygame.draw.rect(layer, (0, 0, 0, T.SHADOW_ALPHA), layer.get_rect(), border_radius=radius)
    surf.blit(layer, (rect.x - 10, rect.y - 2))


def draw_board(surf: pygame.Surface, board: Board, win_cells: list[tuple[int, int]],
               skip_cell: tuple[int, int] | None = None, ghost_col: int | None = None,
               ghost_player: int = 1) -> None:
    """Draw the slab, every hole and disc, a ghost disc for the hovered column
    and white rings round the winning four. `skip_cell` is left empty while
    a disc is still falling into it."""
    slab = pygame.Rect(T.BOARD_LEFT - 12, T.BOARD_TOP - 12, BOARD_W + 24, BOARD_H + 24)
    _shadow(surf, slab, 26)
    pygame.draw.rect(surf, T.BOARD_FRAME, slab, border_radius=18)
    pygame.draw.rect(surf, T.BOARD_BG, slab.inflate(-6, -6), border_radius=15)

    ghost = None
    if ghost_col is not None and ghost_col in board.legal_moves():
        ghost = (board.height(ghost_col), ghost_col)

    for row in range(T.BOARD_ROWS):
        for col in range(T.BOARD_COLS):
            center = board_pixel(row, col)
            pygame.draw.circle(surf, T.BOARD_FRAME, center, T.DISC_RADIUS + 4)
            pygame.draw.circle(surf, T.BG, center, T.DISC_RADIUS + 1)
            cell = board.grid[row][col]
            if (row, col) == skip_cell:
                continue
            if cell:
                draw_disc(surf, center, player_color(cell))
                if (row, col) in win_cells:
                    pygame.draw.circle(surf, (255, 255, 255), center, T.DISC_RADIUS + 4, width=4)
            elif (row, col) == ghost:
                layer = pygame.Surface((T.DISC_RADIUS * 2,) * 2, pygame.SRCALPHA)
                pygame.draw.circle(layer, (*player_color(ghost_player), 70),
                                   (T.DISC_RADIUS, T.DISC_RADIUS), T.DISC_RADIUS - 2)
                surf.blit(layer, layer.get_rect(center=center))


def draw_hover_arrow(surf: pygame.Surface, col: int, color: tuple, t: float) -> None:
    """Small bobbing triangle above the hovered column."""
    cx = board_pixel(0, col)[0]
    y = T.BOARD_TOP - 26 + int(math.sin(t * 5.5) * 4)
    pygame.draw.polygon(surf, color, [(cx, y + 18), (cx - 12, y), (cx + 12, y)])


def draw_hint_overlay(surf: pygame.Surface, fonts: dict, scores: dict[int, int], reason: str) -> None:
    """Score chip above each column, a highlight on the best one, and the reason below the board."""
    if not scores:
        return
    best = max(scores, key=scores.get)

    halo = pygame.Rect(0, 0, (T.DISC_RADIUS + 8) * 2, BOARD_H + 20)
    halo.midtop = (board_pixel(0, best)[0], T.BOARD_TOP - 10)
    layer = pygame.Surface(halo.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, (*T.WIN_GLOW, 40), layer.get_rect(), border_radius=14)
    pygame.draw.rect(layer, (*T.WIN_GLOW, 190), layer.get_rect(), width=3, border_radius=14)
    surf.blit(layer, halo)

    for col, score in scores.items():
        if score >= WIN_SCORE:
            label, color = "Win", T.WIN_GLOW
        elif score <= -WIN_SCORE:
            label, color = "Loss", T.P1_DISC
        else:
            label = f"{score:+d}" if score else "0"
            color = T.TEXT if score > 0 else T.DIM_TEXT if score == 0 else T.P1_DISC
        chip = pygame.Rect(0, 0, 58, 26)
        chip.midtop = (board_pixel(0, col)[0], T.BOARD_TOP - 64)
        pygame.draw.rect(surf, T.SURFACE_HI if col == best else T.SURFACE, chip, border_radius=13)
        pygame.draw.rect(surf, T.WIN_GLOW if col == best else T.BORDER, chip,
                         width=2 if col == best else 1, border_radius=13)
        text = fonts["sm"].render(label, True, color)
        surf.blit(text, text.get_rect(center=chip.center))

    if reason:
        text = fonts["md"].render(reason, True, T.TEXT)
        card = pygame.Rect(T.BOARD_LEFT - 12, T.BOARD_TOP + BOARD_H + 22,
                           min(BOARD_W + 24, text.get_width() + 56), 38)
        pygame.draw.rect(surf, T.SURFACE, card, border_radius=12)
        pygame.draw.rect(surf, T.BORDER, card, width=1, border_radius=12)
        pygame.draw.circle(surf, T.WIN_GLOW, (card.left + 20, card.centery), 5)
        surf.blit(text, (card.left + 36, card.centery - text.get_height() // 2))
