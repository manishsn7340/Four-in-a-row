"""The coach panel on the right: who is ahead, the players, and engine statistics."""

from __future__ import annotations

import math

import pygame

import gui.theme as T
from agents.evaluation import evaluate
from agents.predictor import describe_style, predict_next_move
from game.board import Board
from gui.banner import wrap_text
from gui.icons import draw_agent_avatar
from gui.puzzles import PUZZLES

MODE_HVA = "human_vs_ai"
MODE_HVH = "human_vs_human"
MODE_AVAI = "ai_vs_ai"
MODE_PUZZLE = "puzzle"

PANEL = pygame.Rect(T.BOARD_LEFT + T.BOARD_COLS * T.CELL_SIZE + 36, 54, 0, T.WIN_H - 110)
PANEL.width = T.WIN_W - PANEL.left - 20
X, INNER_W = PANEL.left + 20, PANEL.width - 40


def _norm_eval(board: Board) -> float:
    """Evaluation squashed into [-1, 1]; positive means player 1 is ahead."""
    winner = board.winner()
    if winner:
        return 1.0 if winner == 1 else -1.0
    if board.is_full():
        return 0.0
    return math.tanh(evaluate(board, 1) / 150.0)


def eval_sentence(value: float, name1: str, name2: str) -> str:
    lead, who = (value, name1) if value >= 0 else (-value, name2)
    verb = "are" if who == "You" else "is"
    if lead < 0.08:
        return "The game is evenly balanced"
    if lead < 0.35:
        return f"{who} {verb} slightly ahead"
    if lead < 0.7:
        return f"{who} {verb} clearly ahead"
    return f"{who} {verb} close to winning"


def _card(surf: pygame.Surface, y: int, height: int, border: tuple, width: int = 1,
          fill: tuple | None = None) -> pygame.Rect:
    rect = pygame.Rect(X, y, INNER_W, height)
    pygame.draw.rect(surf, fill or T.BG, rect, border_radius=12)
    pygame.draw.rect(surf, border, rect, width=width, border_radius=12)
    return rect


def _eval_bar(surf: pygame.Surface, fonts: dict, y: int, value: float, name1: str, name2: str) -> None:
    """Coral share on the left, gold on the right, a tick in the middle, and a sentence below."""
    track = pygame.Rect(X, y, INNER_W, 14)
    split = X + int((value + 1) / 2 * INNER_W)
    pygame.draw.rect(surf, T.P2_DISC, track, border_radius=7)
    surf.set_clip(pygame.Rect(X, y, split - X, 14))
    pygame.draw.rect(surf, T.P1_DISC, track, border_radius=7)
    surf.set_clip(None)
    pygame.draw.line(surf, T.SURFACE, (track.centerx, y - 2), (track.centerx, y + 15), 2)
    surf.blit(fonts["md"].render(eval_sentence(value, name1, name2), True, T.TEXT), (X, y + 24))


def _player_card(surf: pygame.Surface, fonts: dict, y: int, agent, role: str, color: tuple,
                 active: bool) -> int:
    card = _card(surf, y, 64, color if active else T.BORDER, 2 if active else 1,
                 T.SURFACE_HI if active else T.BG)
    draw_agent_avatar(surf, agent.name, card.left + 36, card.centery, size=40)
    surf.blit(fonts["mdb"].render(agent.name, True, T.TEXT), (card.left + 70, card.top + 12))
    pygame.draw.circle(surf, color, (card.left + 76, card.top + 44), 5)
    surf.blit(fonts["sm"].render(role, True, T.DIM_TEXT), (card.left + 88, card.top + 36))
    return y + 74


def _engine_details(surf: pygame.Surface, fonts: dict, y: int, game) -> None:
    shown = [(game.agents[1], "Player 1"), (game.agents[2], "Player 2")] if game.mode == MODE_AVAI \
        else [(game.agents[2], game.agents[2].name)]
    for agent, label in shown:
        s = agent.last_stats
        total = s.nodes + s.cutoffs
        rows = [("Positions searched", f"{s.nodes:,}"),
                ("Branches pruned", f"{s.cutoffs / total:.0%}" if s.cutoffs else "–"),
                ("Table hits", f"{s.tt_hits:,}"), ("Simulations", f"{s.simulations:,}"),
                ("Depth", str(s.depth_reached)), ("Time", f"{s.time_s:.2f} s")]
        if len(shown) > 1:
            surf.blit(fonts["mdb"].render(label, True, T.TEXT), (X, y))
            y += 24
        for i, (key, value) in enumerate(rows):
            x, row_y = X + (i % 2) * (INNER_W // 2), y + (i // 2) * 40
            surf.blit(fonts["sm"].render(key, True, T.DIM_TEXT), (x, row_y))
            surf.blit(fonts["md"].render(value, True, T.TEXT), (x, row_y + 17))
        y += 126

    scores = game.progress.get("column_scores") if game.thinking else None
    if scores:
        surf.blit(fonts["cap"].render("BEST MOVES SO FAR", True, T.DIM_TEXT), (X, y))
        y += 22
        top = max(abs(v) for v in scores.values()) or 1.0
        for rank, (col, score) in enumerate(sorted(scores.items(), key=lambda kv: -kv[1])[:3]):
            surf.blit(fonts["sm"].render(f"Column {col + 1}", True, T.TEXT), (X, y))
            track = pygame.Rect(X + 78, y + 4, INNER_W - 90, 8)
            pygame.draw.rect(surf, T.BG, track, border_radius=4)
            fill = int(min(1.0, (score + top) / (2 * top)) * track.width)
            pygame.draw.rect(surf, T.WIN_GLOW if rank == 0 else T.DIM_TEXT, (track.x, track.y, fill, 8),
                             border_radius=4)
            y += 22


def draw_panel(surf: pygame.Surface, fonts: dict, game, t: float) -> pygame.Rect:
    """Draw the panel for the current game state and return the 'Engine details' toggle rect."""
    pygame.draw.rect(surf, T.SURFACE, PANEL, border_radius=16)
    pygame.draw.rect(surf, T.BORDER, PANEL, width=1, border_radius=16)
    mode, board = game.mode, game.board
    turn = board.current_player()

    headline, sub, names = {
        MODE_HVA: ("You vs the computer", "Drop discs, ask for a hint any time", ("You", game.agents[2].name)),
        MODE_HVH: ("Two players", "Pass the mouse and take turns", ("Coral", "Gold")),
        MODE_PUZZLE: ("Tactics trainer", f"Puzzle {game.puzzle_idx + 1} of {len(PUZZLES)}", ("You", "The opponent")),
        MODE_AVAI: ("AI vs AI", "Watch two engines play each other", (game.agents[1].name, game.agents[2].name)),
    }[mode]
    y = PANEL.top + 20
    surf.blit(fonts["lg"].render(headline, True, T.TEXT), (X, y))
    surf.blit(fonts["sm"].render(sub, True, T.DIM_TEXT), (X, y + 34))
    surf.blit(fonts["cap"].render("WHO IS AHEAD", True, T.DIM_TEXT), (X, y + 72))
    _eval_bar(surf, fonts, y + 94, game.display_eval, *names)
    y += 156

    if mode == MODE_HVH:
        color = T.P1_DISC if turn == 1 else T.P2_DISC
        card = _card(surf, y, 84, T.BORDER if game.game_over else color)
        title = game.banner if game.game_over else f"{names[turn - 1]}'s turn"
        surf.blit(fonts["mdb"].render(title, True, T.TEXT if game.game_over else color),
                  (card.left + 16, card.top + 14))
        detail = "Press R for a rematch" if game.game_over else \
            f"Move {len(board.move_history) + 1}  ·  Press H for a hint"
        surf.blit(fonts["sm"].render(detail, True, T.DIM_TEXT), (card.left + 16, card.top + 46))
        y += 96
    elif mode == MODE_PUZZLE:
        puzzle = PUZZLES[game.puzzle_idx]
        card = _card(surf, y, 170, T.BORDER)
        surf.blit(fonts["mdb"].render(puzzle.title, True, T.TEXT), (card.left + 16, card.top + 14))
        diff_color = {"Easy": T.WIN_GLOW, "Medium": T.P2_DISC}.get(puzzle.difficulty, T.P1_DISC)
        surf.blit(fonts["sm"].render(puzzle.difficulty, True, diff_color), (card.left + 16, card.top + 40))
        text = puzzle.explanation if game.game_over else puzzle.description
        for i, line in enumerate(wrap_text(fonts["sm"], text, INNER_W - 32)[:4]):
            surf.blit(fonts["sm"].render(line, True, T.TEXT), (card.left + 16, card.top + 68 + i * 20))
        y += 182
    elif mode == MODE_AVAI:
        y = _player_card(surf, fonts, y, game.agents[1], "Player 1 · Coral", T.P1_DISC, turn == 1)
        y = _player_card(surf, fonts, y, game.agents[2], "Player 2 · Gold", T.P2_DISC, turn == 2)
    else:
        y = _player_card(surf, fonts, y, game.agents[2], "Computer · Gold", T.P2_DISC, turn == 2)

    if game.thinking:
        depth = game.progress.get("depth")
        dots = "." * (int(t * 2.5) % 4)
        text = f"Thinking{dots}" + (f"  ·  looking {depth} moves ahead" if depth else "")
        surf.blit(fonts["md"].render(text, True, T.WIN_GLOW), (X, y))
    elif mode == MODE_HVA and turn == 1 and not game.game_over:
        guess = predict_next_move(board, 1)
        style = describe_style(board.move_history, 1)
        surf.blit(fonts["sm"].render(f"Likely next move for you: column {guess + 1}", True, T.DIM_TEXT), (X, y - 4))
        if style:
            surf.blit(fonts["sm"].render(style, True, T.DIM_TEXT), (X, y + 12))
    y += 34

    toggle = pygame.Rect(X - 6, y - 4, INNER_W + 12, 30)
    if toggle.collidepoint(pygame.mouse.get_pos()):
        pygame.draw.rect(surf, T.SURFACE_HI, toggle, border_radius=8)
    cx, cy = X + 6, y + 11  # triangle pointing down when open, right when closed
    points = [(cx - 5, cy - 3), (cx + 5, cy - 3), (cx, cy + 4)] if game.show_details \
        else [(cx - 3, cy - 5), (cx - 3, cy + 5), (cx + 4, cy)]
    pygame.draw.polygon(surf, T.DIM_TEXT, points)
    surf.blit(fonts["cap"].render("ENGINE DETAILS", True, T.DIM_TEXT), (X + 22, y + 4))
    if game.show_details:
        _engine_details(surf, fonts, y + 36, game)

    pygame.draw.line(surf, T.BORDER, (PANEL.left + 16, PANEL.bottom - 52), (PANEL.right - 16, PANEL.bottom - 52))
    font = fonts["md"] if fonts["md"].size(game.status)[0] <= INNER_W else fonts["sm"]
    surf.blit(font.render(game.status, True, T.TEXT), (X, PANEL.bottom - 34))
    return toggle
