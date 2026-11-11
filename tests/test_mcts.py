"""Acceptance tests for MCTSAgent (v7)."""

from __future__ import annotations

from agents.mcts import MCTSAgent
from agents.simple import RandomAgent
from game.board import Board
from helpers import snapshot


def _play_game(a1: MCTSAgent, a2: RandomAgent) -> int:
    """Play one game with a1 moving first; return the winner (0 = draw)."""
    board = Board()
    while not board.is_terminal():
        agent = a1 if board.current_player() == 1 else a2
        col = agent.choose_move(board)
        board.drop(col)
    return board.winner()


# --- beats RandomAgent 19/20 seeded games ---

def test_mcts_beats_random_19_of_20() -> None:
    wins = 0
    for seed in range(20):
        mcts = MCTSAgent(simulations=800, seed=seed)
        rand = RandomAgent(seed=seed + 100)
        if _play_game(mcts, rand) == 1:
            wins += 1
    assert wins >= 19, f"MCTS won only {wins}/20 games"


# --- takes an immediate win ---

def test_takes_immediate_win() -> None:
    board = Board()
    for p1c, p2c in [(0, 6), (1, 5), (2, 4)]:
        board.drop(p1c)
        board.drop(p2c)
    agent = MCTSAgent(simulations=200, seed=42)
    assert agent.choose_move(board) == 3


# --- blocks an immediate loss ---

def test_blocks_immediate_loss() -> None:
    # P2 has three in a row in columns 1-3; column 0 is already taken, so only 4 blocks.
    board = Board()
    for p1c, p2c in [(6, 1), (5, 2), (0, 3)]:
        board.drop(p1c)
        board.drop(p2c)
    agent = MCTSAgent(simulations=1500, rollout="light", seed=42)
    move = agent.choose_move(board)
    assert move == 4


# --- same seed → same move ---

def test_same_seed_same_move() -> None:
    board = Board()
    board.drop(3); board.drop(2); board.drop(1); board.drop(5)
    a1 = MCTSAgent(simulations=300, seed=99)
    a2 = MCTSAgent(simulations=300, seed=99)
    assert a1.choose_move(board) == a2.choose_move(board)


# --- board unchanged after search ---

def test_board_unchanged() -> None:
    board = Board()
    for col in [3, 2, 4, 1, 5, 0]:
        board.drop(col)
    before = snapshot(board)
    MCTSAgent(simulations=300, seed=42).choose_move(board)
    assert snapshot(board) == before


# --- visit counts sum correctly ---

def test_visit_counts() -> None:
    board = Board()
    agent = MCTSAgent(simulations=400, seed=42)
    agent.choose_move(board)
    assert agent.last_stats.column_scores is not None
    assert agent.last_stats.simulations == 400


# --- more simulations never crashes ---

def test_many_simulations_no_crash() -> None:
    board = Board()
    MCTSAgent(simulations=3000, seed=7).choose_move(board)
