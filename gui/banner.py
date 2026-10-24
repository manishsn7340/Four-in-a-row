"""Banner overlays, celebration toasts, and text wrapping for the GUI."""

from __future__ import annotations

import pygame
import gui.theme as T


def wrap_text(font: pygame.font.Font, text: str, max_w: int) -> list[str]:
    """Wrap words to fit strictly within max_w pixels without clipping or spilling."""
    words = text.split()
    lines: list[str] = []
    cur: list[str] = []
    for w in words:
        test_line = " ".join(cur + [w])
        if font.size(test_line)[0] <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines


def _draw_card(
    surf: pygame.Surface,
    title: str,
    title_color: tuple,
    sub: str,
    fonts: dict,
    height: int = 112,
) -> None:
    """Draw a rounded message card centred on the board."""
    bw = T.BOARD_COLS * T.CELL_SIZE
    cx = T.BOARD_LEFT + bw // 2
    cy = T.BOARD_TOP + (T.BOARD_ROWS * T.CELL_SIZE) // 2

    font = fonts["xl"]
    for key in ("xl", "lg", "md"):
        font = fonts[key]
        if font.size(title)[0] <= bw - 80:
            break
    width = min(bw - 40, max(380, font.size(title)[0] + 80))
    rect = pygame.Rect(0, 0, width, height)
    rect.center = (cx, cy)

    shadow = pygame.Surface((rect.width + 24, rect.height + 24), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 60), shadow.get_rect(), border_radius=28)
    surf.blit(shadow, (rect.x - 12, rect.y - 4))
    pygame.draw.rect(surf, T.SURFACE, rect, border_radius=18)
    pygame.draw.rect(surf, title_color, rect, width=2, border_radius=18)

    t_surf = font.render(title, True, T.TEXT)
    surf.blit(t_surf, t_surf.get_rect(center=(cx, rect.top + height // 2 - 12)))
    sub_surf = fonts["md"].render(sub, True, T.DIM_TEXT)
    surf.blit(sub_surf, sub_surf.get_rect(center=(cx, rect.bottom - 26)))


def draw_puzzle_banner(
    surf: pygame.Surface,
    fonts: dict,
    puzzle_id: int,
    total_puzzles: int,
    t_anim: float,
) -> None:
    """Draw the puzzle-solved card over the board."""
    if puzzle_id >= total_puzzles:
        _draw_card(surf, f"All {total_puzzles} puzzles solved", T.P2_DISC,
                   "Click or press Space to start over", fonts)
    else:
        _draw_card(surf, f"Puzzle {puzzle_id} solved", T.WIN_GLOW,
                   "Next puzzle in 2 s  ·  click or press Space to skip", fonts)


def draw_banner(
    surf: pygame.Surface,
    fonts: dict,
    message: str,
    t_anim: float,
    sub_hint: str | None = None,
) -> None:
    """Draw the game-over card over the board (winning discs stay visible around it)."""
    lowered = message.lower()
    accent = T.WIN_GLOW if ("win" in lowered or "victory" in lowered) else T.DIM_TEXT
    _draw_card(surf, message, accent,
               sub_hint or "Press R for a rematch  ·  Esc to quit", fonts)
