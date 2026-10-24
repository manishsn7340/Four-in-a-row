"""Smoke tests for the initial project setup."""

from pathlib import Path

import agents
import experiments
import game
import gui
from config import COLS, GLOBAL_SEED, MCTS_C, MOVE_ORDER, ROWS, WIN_SCORE


def test_configuration_matches_connect_four_board() -> None:
    """Expose the fixed board and search constants to later layers."""
    assert (ROWS, COLS) == (6, 7)
    assert MOVE_ORDER == (3, 2, 4, 1, 5, 0, 6)
    assert WIN_SCORE == 1_000_000
    assert GLOBAL_SEED == 42
    assert MCTS_C == 1.41


def test_initial_packages_are_importable() -> None:
    """Verify that each planned Python package is available."""
    assert all((agents.__doc__, experiments.__doc__, game.__doc__, gui.__doc__))


def test_required_project_directories_exist() -> None:
    """Keep the v0 folder layout available to subsequent layers."""
    root = Path(__file__).resolve().parents[1]
    expected_directories = ("agents", "experiments", "game", "gui", "report", "results")
    assert all((root / directory).is_dir() for directory in expected_directories)
