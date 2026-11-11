"""Unit tests for experiments/arena.py."""

from __future__ import annotations

from agents.alphabeta import AlphaBetaAgent
from agents.evaluation import WEIGHTS
from agents.simple import RandomAgent
from experiments.arena import MatchResult, play_match


def test_match_result_counts_sum_to_n_games() -> None:
    a = RandomAgent(seed=1, name="Random-A")
    b = RandomAgent(seed=2, name="Random-B")
    r = play_match(a, b, n_games=10, seed=0)

    assert r.wins_a + r.wins_b + r.draws == 10
    assert len(r.move_counts) == 10


def test_match_result_win_rates_sum_to_one() -> None:
    a = RandomAgent(seed=3, name="Random-A")
    b = RandomAgent(seed=4, name="Random-B")
    r = play_match(a, b, n_games=10, seed=0)

    total = r.win_rate_a + r.win_rate_b + r.draw_rate
    assert abs(total - 1.0) < 1e-9


def test_ab_beats_random_most_of_the_time() -> None:
    """AlphaBeta d=2 should win at least 70 % of games against a random player."""
    strong = AlphaBetaAgent(depth=2, use_ordering=True, weights=WEIGHTS, name="AB-d2")
    weak   = RandomAgent(seed=99, name="Random")
    r = play_match(strong, weak, n_games=20, seed=0)

    assert r.win_rate_a >= 0.70, (
        f"AB-d2 expected ≥70% vs random, got {r.win_rate_a:.0%}"
    )


def test_as_dict_has_expected_keys() -> None:
    a = RandomAgent(seed=5, name="R1")
    b = RandomAgent(seed=6, name="R2")
    r = play_match(a, b, n_games=4, seed=0)
    d = r.as_dict()

    for key in ("agent_a", "agent_b", "n_games", "wins_a", "wins_b",
                "draws", "win_rate_a", "win_rate_b", "draw_rate",
                "avg_moves", "total_time_s"):
        assert key in d, f"Missing key: {key}"


def test_move_counts_are_positive() -> None:
    a = RandomAgent(seed=7, name="R1")
    b = RandomAgent(seed=8, name="R2")
    r = play_match(a, b, n_games=6, seed=0)

    assert all(m > 0 for m in r.move_counts)


def test_openings_make_deterministic_agents_play_different_games() -> None:
    """From an empty board two deterministic agents replay the same two games;
    seeded openings give varied games and the same result for the same seed."""
    def run(openings: int):
        a = AlphaBetaAgent(depth=1, weights=WEIGHTS, name="A")
        b = AlphaBetaAgent(depth=2, weights=WEIGHTS, name="B")
        return play_match(a, b, n_games=8, seed=3, openings=openings)

    plain, first, second = run(0), run(4), run(4)
    assert plain.move_counts[0::2] == [plain.move_counts[0]] * 4
    assert plain.move_counts[1::2] == [plain.move_counts[1]] * 4
    assert len(set(first.move_counts)) > 2
    assert first.move_counts == second.move_counts
    assert (first.wins_a, first.wins_b, first.draws) == (second.wins_a, second.wins_b, second.draws)


def test_random_opening_is_seeded_and_never_finishes_the_game() -> None:
    import random

    from experiments.arena import random_opening
    from helpers import play

    first = [random_opening(random.Random(s), 6) for s in range(30)]
    assert first == [random_opening(random.Random(s), 6) for s in range(30)]
    assert len(set(map(tuple, first))) > 1
    assert all(len(o) == 6 and not play(o).is_terminal() for o in first)
