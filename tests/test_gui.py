"""Unit tests for the GUI layer (headless safe)."""

from __future__ import annotations

import os

# Ensure pygame runs in headless dummy video mode during tests
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import pytest

from game.board import Board
from gui import theme as T
from gui.animation import ConfettiBurst, DiscDrop, WinPulse, _bounce_out
from gui.app import (
    MODE_AVAI,
    MODE_HVA,
    MODE_HVH,
    MODE_PUZZLE,
    _SearchResultGate,
    _make_agent,
    _norm_eval,
    column_from_x,
)
from gui.screens import demo_board
from gui.sound import SoundManager
from gui.widgets import Dropdown, Slider


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


def test_theme_constants_and_fonts():
    assert T.WIN_W == 1280
    assert T.WIN_H == 800
    assert T.BOARD_COLS == 7
    assert T.BOARD_ROWS == 6
    assert len(T.P1_DISC) == 3
    assert len(T.P2_DISC) == 3

    fonts = T.load_fonts()
    assert "sm" in fonts and fonts["sm"] is not None
    assert "md" in fonts and fonts["md"] is not None
    assert "lg" in fonts and fonts["lg"] is not None


def test_column_from_x():
    # Outside left
    assert column_from_x(T.BOARD_LEFT - 10) is None
    # Outside right
    assert column_from_x(T.BOARD_LEFT + T.BOARD_COLS * T.CELL_SIZE + 10) is None
    # Col 0
    assert column_from_x(T.BOARD_LEFT + 10) == 0
    # Col 3 (center)
    assert column_from_x(T.BOARD_LEFT + 3 * T.CELL_SIZE + 10) == 3
    # Col 6 (rightmost)
    assert column_from_x(T.BOARD_LEFT + 6 * T.CELL_SIZE + 10) == 6


def test_norm_eval():
    b = Board()
    assert _norm_eval(b) == 0.0

    # P1 win
    for c in (0, 1, 2, 3):
        b.drop(c)
        if not b.is_terminal():
            b.drop(c)
    assert _norm_eval(b) == 1.0


def test_make_agent():
    r = _make_agent("Rookie (AB d=2)")
    assert r.name == "Rookie"

    t = _make_agent("Tactician (AB d=5)")
    assert t.name == "Tactician"

    g = _make_agent("Gambler (MCTS)")
    assert g.name == "Gambler"


def test_game_modes():
    assert MODE_HVA == "human_vs_ai"
    assert MODE_HVH == "human_vs_human"
    assert MODE_AVAI == "ai_vs_ai"
    assert MODE_PUZZLE == "puzzle"


def test_stale_ai_results_are_discarded_after_a_game_reset():
    """Never reuse a move produced by a search from an earlier game session."""
    results = _SearchResultGate()
    old_generation = results.generation

    results.invalidate()
    current_generation = results.generation
    results.submit(old_generation, 0)
    results.submit(current_generation, 4)

    assert results.take_current() == 4
    assert results.take_current() is None


def test_bounce_easing():
    assert _bounce_out(0.0) == 0.0
    assert pytest.approx(_bounce_out(1.0), abs=1e-3) == 1.0


def test_disc_drop_animation():
    drop = DiscDrop(col=3, row=0, color=T.P1_DISC)
    assert not drop.done
    drop.update(0.1)
    assert not drop.done
    drop.update(0.3)
    assert drop.done

    surf = pygame.Surface((T.WIN_W, T.WIN_H))
    drop.draw(surf)


def test_win_pulse_animation():
    win_cells = [(0, 0), (0, 1), (0, 2), (0, 3)]
    pulse = WinPulse(win_cells)
    pulse.update(0.1)
    surf = pygame.Surface((T.WIN_W, T.WIN_H))
    pulse.draw(surf)


def test_confetti_burst():
    win_cells = [(0, 0), (0, 1), (0, 2), (0, 3)]
    burst = ConfettiBurst(win_cells)
    assert not burst.done
    burst.update(0.05)
    surf = pygame.Surface((T.WIN_W, T.WIN_H))
    burst.draw(surf)


def test_widgets_dropdown():
    drop = Dropdown((10, 10, 100, 30), ["Option A", "Option B"], initial=0)
    assert drop.value == "Option A"


def test_widgets_slider():
    sl = Slider((10, 10, 100, 14), min_val=0.0, max_val=2.0, initial=0.5, label="Delay")
    assert sl.value == 0.5
    sl._set_from_x(10)
    assert sl.value == 0.0
    sl._set_from_x(110)
    assert sl.value == 2.0


def test_sound_manager():
    sm = SoundManager()
    assert sm.muted is False
    muted = sm.toggle_mute()
    assert muted is True
    # Safe methods should never crash regardless of hardware
    sm.play_drop()
    sm.play_hint()
    sm.play_win()
    sm.play_click()


def test_demo_board():
    b = demo_board()
    assert not b.is_terminal()
    assert len(b.move_history) > 0


def test_procedural_icons():
    from gui.icons import (
        make_bulb_icon,
        make_chart_icon,
        make_demo_icon,
        make_sound_icon,
    )
    for fn in (make_bulb_icon, make_chart_icon, make_demo_icon):
        surf = fn()
        assert surf.get_width() > 0 and surf.get_height() > 0

    snd = make_sound_icon(muted=False)
    assert snd.get_width() > 0
    snd_muted = make_sound_icon(muted=True)
    assert snd_muted.get_width() > 0


def test_opening_book():
    from gui.opening_book import lookup
    assert lookup([]) == 3
    assert lookup([3]) == 3
    assert lookup([0]) == 3
    assert lookup([3, 3]) == 3
    # Unknown sequence returns None
    assert lookup([0, 1, 2, 3, 4, 5, 6]) is None



def test_extra_icons_and_avatars():
    from gui.icons import draw_agent_avatar, make_puzzle_icon
    puz = make_puzzle_icon()
    assert puz.get_width() > 0

    surf = pygame.Surface((100, 100), pygame.SRCALPHA)
    for name in ("Rookie", "Tactician", "Grandmaster", "Gambler", "AlphaBeta"):
        draw_agent_avatar(surf, name, 50, 50, size=40)


def test_wrap_text_and_puzzle_banner():
    from gui.banner import draw_puzzle_banner, wrap_text
    fonts = T.load_fonts()
    sample = "Player 2 is about to win vertically. Find the only legal move that prevents defeat."
    lines = wrap_text(fonts["sm"], sample, 320)
    assert len(lines) >= 2
    for line in lines:
        assert fonts["sm"].size(line)[0] <= 320

    surf = pygame.Surface((T.WIN_W, T.WIN_H))
    draw_puzzle_banner(surf, fonts, 1, 5, 0.5)
    draw_puzzle_banner(surf, fonts, 5, 5, 1.0)



def test_demo_board_seeded_is_reproducible_and_varied():
    first = demo_board(1)
    assert first.move_history == demo_board(1).move_history
    openings = {tuple(demo_board(seed).move_history) for seed in range(1, 11)}
    assert len(openings) > 1
    for seed in range(1, 11):
        board = demo_board(seed)
        assert not board.is_terminal()
        assert 6 <= len(board.move_history) <= 8
