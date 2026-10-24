"""Coach panel rendering, live position evaluation bar, and search metrics."""

from __future__ import annotations

import math
import pygame

from agents.base import Agent
from agents.evaluation import evaluate
from game.board import Board
import gui.theme as T
from gui.banner import wrap_text
from gui.board_view import P1_COLOR, P2_COLOR, _lerp_color
from gui.icons import (
    draw_agent_avatar,
    make_human_icon,
    make_puzzle_icon,
    make_robot_icon,
)
from gui.puzzles import PUZZLES

# Game mode constants used by panel branching
MODE_HVA = "human_vs_ai"
MODE_HVH = "human_vs_human"
MODE_AVAI = "ai_vs_ai"
MODE_PUZZLE = "puzzle"


def _norm_eval(board: Board) -> float:
    """Return a position evaluation in [-1.0, 1.0] from P1's perspective."""
    w = board.winner()
    if w == 1:
        return 1.0
    if w == 2:
        return -1.0
    if board.is_full():
        return 0.0
    raw = evaluate(board, 1)
    norm = math.tanh(raw / 150.0)
    return max(-1.0, min(1.0, norm))


def eval_sentence(val: float, name1: str, name2: str) -> str:
    """Describe an evaluation in [-1, 1] (P1 positive) in plain language."""
    lead, who = (val, name1) if val >= 0 else (-val, name2)
    verb = "are" if who == "You" else "is"
    if lead < 0.08:
        return "The game is evenly balanced"
    if lead < 0.35:
        return f"{who} {verb} slightly ahead"
    if lead < 0.7:
        return f"{who} {verb} clearly ahead"
    return f"{who} {verb} close to winning"


def _section_label(surf: pygame.Surface, fonts: dict, text: str, x: int, y: int) -> int:
    """Draw a small uppercase section label; return the y below it."""
    surf.blit(fonts["cap"].render(text.upper(), True, T.DIM_TEXT), (x, y))
    return y + 22


def _chevron(surf: pygame.Surface, cx: int, cy: int, open_: bool, color: tuple) -> None:
    """Draw a small triangle: pointing down when open, right when closed."""
    if open_:
        pts = [(cx - 5, cy - 3), (cx + 5, cy - 3), (cx, cy + 4)]
    else:
        pts = [(cx - 3, cy - 5), (cx - 3, cy + 5), (cx + 4, cy)]
    pygame.draw.polygon(surf, color, pts)


def draw_eval_bar(
    surf: pygame.Surface, fonts: dict, px: int, pw: int, y: int, val: float,
    name1: str = "P1", name2: str = "P2",
) -> None:
    """Draw the who-is-ahead bar with a centre tick and a plain-language caption."""
    bar_w = pw - 40
    bar_h = 14
    bx = px + 20
    track = pygame.Rect(bx, y, bar_w, bar_h)
    pygame.draw.rect(surf, T.BG, track, border_radius=7)

    p1_w = max(0, min(bar_w, int((val + 1.0) / 2.0 * bar_w)))
    clip = surf.get_clip()
    surf.set_clip(track)
    if p1_w:
        pygame.draw.rect(surf, P1_COLOR, (bx, y, p1_w + 8, bar_h), border_radius=7)
    if p1_w < bar_w:
        pygame.draw.rect(surf, P2_COLOR, (bx + p1_w, y, bar_w - p1_w, bar_h), border_radius=7)
        if p1_w:
            pygame.draw.rect(surf, P1_COLOR, (bx, y, p1_w, bar_h))
    surf.set_clip(clip)
    mid = bx + bar_w // 2
    pygame.draw.line(surf, T.SURFACE, (mid, y - 2), (mid, y + bar_h + 1), 2)

    cap = fonts["md"].render(eval_sentence(val, name1, name2), True, T.TEXT)
    surf.blit(cap, (bx, y + bar_h + 10))


def _player_row(surf: pygame.Surface, fonts: dict, x: int, y: int, w: int,
                agent: Agent, role: str, color: tuple, active: bool) -> int:
    """Draw one player card (avatar, name, role); return the y below it."""
    card = pygame.Rect(x, y, w, 64)
    pygame.draw.rect(surf, T.SURFACE_HI if active else T.BG, card, border_radius=12)
    pygame.draw.rect(surf, color if active else T.BORDER, card, width=2 if active else 1,
                     border_radius=12)
    draw_agent_avatar(surf, agent.name, card.left + 36, card.centery, size=40)
    surf.blit(fonts["mdb"].render(agent.name, True, T.TEXT), (card.left + 70, card.top + 12))
    pygame.draw.circle(surf, color, (card.left + 76, card.top + 44), 5)
    surf.blit(fonts["sm"].render(role, True, T.DIM_TEXT), (card.left + 88, card.top + 36))
    return y + 64 + 10


def _info_card(surf: pygame.Surface, fonts: dict, x: int, y: int, w: int, h: int,
               accent: tuple) -> pygame.Rect:
    card = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surf, T.BG, card, border_radius=12)
    pygame.draw.rect(surf, accent, card, width=1, border_radius=12)
    return card


def draw_panel(
    surf: pygame.Surface,
    fonts: dict,
    p1_agent: Agent | None,
    p2_agent: Agent,
    status: str,
    display_eval: float,
    ai_thinking: bool,
    progress: dict,
    mode: str,
    board: Board,
    t_anim: float,
    puzzle_idx: int = 0,
    show_details: bool = False,
) -> pygame.Rect:
    """Draw the coach panel and return the clickable rect of the details toggle."""
    px = T.BOARD_LEFT + T.BOARD_COLS * T.CELL_SIZE + 36
    pw = T.WIN_W - px - 20
    panel = pygame.Rect(px, 54, pw, T.WIN_H - 110)
    pygame.draw.rect(surf, T.SURFACE, panel, border_radius=16)
    pygame.draw.rect(surf, T.BORDER, panel, width=1, border_radius=16)

    x = px + 20
    inner_w = pw - 40
    y = panel.top + 20
    current = board.current_player()

    # ── Mode headline ─────────────────────────────────────────────────────────
    if mode == MODE_HVA:
        headline, sub = "You vs the computer", "Drop discs, ask for a hint any time"
        name1, name2 = "You", p2_agent.name
    elif mode == MODE_HVH:
        headline, sub = "Two players", "Pass the mouse and take turns"
        name1, name2 = "Coral", "Gold"
    elif mode == MODE_PUZZLE:
        headline, sub = "Tactics trainer", f"Puzzle {puzzle_idx + 1} of {len(PUZZLES)}"
        name1, name2 = "You", "The opponent"
    else:
        headline, sub = "AI vs AI", "Watch two engines play each other"
        name1 = p1_agent.name if p1_agent else "Player 1"
        name2 = p2_agent.name
    surf.blit(fonts["lg"].render(headline, True, T.TEXT), (x, y))
    surf.blit(fonts["sm"].render(sub, True, T.DIM_TEXT), (x, y + 34))
    y += 72

    # ── Position evaluation ───────────────────────────────────────────────────
    y = _section_label(surf, fonts, "Who is ahead", x, y)
    draw_eval_bar(surf, fonts, px, pw, y, display_eval, name1, name2)
    y += 62

    # ── Mode-specific cards ───────────────────────────────────────────────────
    if mode == MODE_HVH:
        cur_col = P1_COLOR if current == 1 else P2_COLOR
        card = _info_card(surf, fonts, x, y, inner_w, 84, cur_col)
        who = "Coral" if current == 1 else "Gold"
        surf.blit(fonts["mdb"].render(f"{who}'s turn", True, cur_col), (card.left + 16, card.top + 14))
        n = len(board.move_history)
        surf.blit(fonts["sm"].render(f"Move {n + 1}  ·  Press H for a hint", True, T.DIM_TEXT),
                  (card.left + 16, card.top + 46))
        y += 96
    elif mode == MODE_PUZZLE:
        p = PUZZLES[puzzle_idx]
        solved = board.winner() == 1 or board.is_terminal() or status.startswith("✓")
        card = _info_card(surf, fonts, x, y, inner_w, 170, T.BORDER)
        diff_col = {"Easy": T.WIN_GLOW, "Medium": P2_COLOR}.get(p.difficulty, P1_COLOR)
        surf.blit(fonts["mdb"].render(p.title, True, T.TEXT), (card.left + 16, card.top + 14))
        surf.blit(fonts["sm"].render(p.difficulty, True, diff_col), (card.left + 16, card.top + 40))
        body = p.explanation if solved else p.description
        ty = card.top + 68
        for line in wrap_text(fonts["sm"], body, inner_w - 32)[:4]:
            surf.blit(fonts["sm"].render(line, True, T.TEXT), (card.left + 16, ty))
            ty += 20
        y += 182
    else:
        if mode == MODE_AVAI and p1_agent:
            y = _player_row(surf, fonts, x, y, inner_w, p1_agent, "Player 1 · Coral",
                            P1_COLOR, current == 1)
            y = _player_row(surf, fonts, x, y, inner_w, p2_agent, "Player 2 · Gold",
                            P2_COLOR, current == 2)
        else:
            y = _player_row(surf, fonts, x, y, inner_w, p2_agent, "Computer · Gold",
                            P2_COLOR, current == 2)

    # ── Live thinking line ────────────────────────────────────────────────────
    if ai_thinking:
        dots = "." * (int(t_anim * 2.5) % 4)
        depth = progress.get("depth")
        extra = f"  ·  looking {depth} moves ahead" if depth else ""
        surf.blit(fonts["md"].render(f"Thinking{dots}{extra}", True, T.WIN_GLOW), (x, y))
    y += 34

    # ── Engine details (collapsed by default) ─────────────────────────────────
    toggle = pygame.Rect(x - 6, y - 4, inner_w + 12, 30)
    hover = toggle.collidepoint(pygame.mouse.get_pos())
    if hover:
        pygame.draw.rect(surf, T.SURFACE_HI, toggle, border_radius=8)
    _chevron(surf, x + 6, y + 11, show_details, T.DIM_TEXT)
    surf.blit(fonts["cap"].render("ENGINE DETAILS", True, T.DIM_TEXT), (x + 22, y + 4))
    y += 36

    if show_details:
        agents = [(p1_agent, "Player 1")] if mode == MODE_AVAI and p1_agent else []
        agents.append((p2_agent, "Player 2" if mode == MODE_AVAI else p2_agent.name))
        col_w = inner_w // 2
        for agent, label in agents:
            last = agent.last_stats
            total = last.nodes + last.cutoffs
            pruned = f"{last.cutoffs / total:.0%}" if total and last.cutoffs else "–"
            rows = [("Positions searched", f"{last.nodes:,}"), ("Branches pruned", pruned),
                    ("Table hits", f"{last.tt_hits:,}"), ("Simulations", f"{last.simulations:,}"),
                    ("Depth", f"{last.depth_reached}"), ("Time", f"{last.time_s:.2f} s")]
            if len(agents) > 1:
                surf.blit(fonts["mdb"].render(label, True, T.TEXT), (x, y))
                y += 24
            for i, (k, v) in enumerate(rows):
                rx = x + (i % 2) * col_w
                ry = y + (i // 2) * 40
                surf.blit(fonts["sm"].render(k, True, T.DIM_TEXT), (rx, ry))
                surf.blit(fonts["md"].render(v, True, T.TEXT), (rx, ry + 17))
            y += 3 * 40 + 6

        col_scores = progress.get("column_scores", {}) if ai_thinking else {}
        if col_scores:
            y = _section_label(surf, fonts, "Best moves so far", x, y)
            ranked = sorted(col_scores.items(), key=lambda kv: kv[1], reverse=True)[:3]
            top = max(abs(v) for _, v in col_scores.items()) or 1.0
            bar_max = inner_w - 90
            for rank, (col, score) in enumerate(ranked):
                color = T.WIN_GLOW if rank == 0 else T.DIM_TEXT
                surf.blit(fonts["sm"].render(f"Column {col + 1}", True, T.TEXT), (x, y))
                track = pygame.Rect(x + 78, y + 4, bar_max, 8)
                pygame.draw.rect(surf, T.BG, track, border_radius=4)
                fill = int(min(1.0, (score + top) / (2 * top)) * bar_max)
                if fill:
                    pygame.draw.rect(surf, color, (track.x, track.y, fill, 8), border_radius=4)
                y += 22

    # ── Status footer ─────────────────────────────────────────────────────────
    pygame.draw.line(surf, T.BORDER, (px + 16, panel.bottom - 52), (px + pw - 16, panel.bottom - 52))
    font = fonts["md"] if fonts["md"].size(status)[0] <= inner_w else fonts["sm"]
    surf.blit(font.render(status.lstrip("✦ "), True, T.TEXT), (x, panel.bottom - 34))
    return toggle
