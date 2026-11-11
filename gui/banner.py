"""Game-over and puzzle-solved cards, plus a small word-wrap helper."""

from __future__ import annotations

import pygame

import gui.theme as T
from gui.board_view import BOARD_H, BOARD_W


def wrap_text(font: pygame.font.Font, text: str, max_w: int) -> list[str]:
    """Split `text` into lines no wider than `max_w` pixels."""
    lines: list[str] = []
    for word in text.split():
        if lines and font.size(f"{lines[-1]} {word}")[0] <= max_w:
            lines[-1] += " " + word
        else:
            lines.append(word)
    return lines


def _card(surf: pygame.Surface, fonts: dict, title: str, subtitle: str, accent: tuple) -> None:
    """A rounded card centred on the board; the title shrinks to fit."""
    font = next((fonts[k] for k in ("xl", "lg") if fonts[k].size(title)[0] <= BOARD_W - 80), fonts["md"])
    rect = pygame.Rect(0, 0, min(BOARD_W - 40, max(380, font.size(title)[0] + 80)), 112)
    rect.center = (T.BOARD_LEFT + BOARD_W // 2, T.BOARD_TOP + BOARD_H // 2)
    shadow = pygame.Surface((rect.width + 24, rect.height + 24), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 60), shadow.get_rect(), border_radius=28)
    surf.blit(shadow, (rect.x - 12, rect.y - 4))
    pygame.draw.rect(surf, T.SURFACE, rect, border_radius=18)
    pygame.draw.rect(surf, accent, rect, width=2, border_radius=18)
    surf.blit(text := font.render(title, True, T.TEXT), text.get_rect(center=(rect.centerx, rect.top + 44)))
    surf.blit(text := fonts["md"].render(subtitle, True, T.DIM_TEXT),
              text.get_rect(center=(rect.centerx, rect.bottom - 26)))


def draw_banner(surf: pygame.Surface, fonts: dict, message: str) -> None:
    accent = T.WIN_GLOW if "win" in message.lower() or "victory" in message.lower() else T.DIM_TEXT
    _card(surf, fonts, message, "Press R for a rematch  ·  Esc to quit", accent)


def draw_puzzle_banner(surf: pygame.Surface, fonts: dict, puzzle_id: int, total: int, t: float = 0.0) -> None:
    if puzzle_id >= total:
        _card(surf, fonts, f"All {total} puzzles solved", "Click or press Space to start over", T.P2_DISC)
    else:
        _card(surf, fonts, f"Puzzle {puzzle_id} solved",
              "Next puzzle in 2 s  ·  click or press Space to skip", T.WIN_GLOW)
