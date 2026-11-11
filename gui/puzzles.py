"""Five tactics puzzles: play the given moves, then find `solution_col`."""

from __future__ import annotations

from dataclasses import dataclass

from game.board import Board


@dataclass
class Puzzle:
    id: int
    title: str
    difficulty: str  # "Easy", "Medium", "Hard"
    description: str
    solution_col: int
    moves: list[int]
    player_to_move: int
    explanation: str

    def create_board(self) -> Board:
        b = Board()
        for col in self.moves:
            b.drop(col)
        return b


PUZZLES: list[Puzzle] = [
    Puzzle(
        id=1,
        title="Instant Kill",
        difficulty="Easy",
        description="Player 1 (Coral) has 3 in a row. Find the immediate horizontal winning move!",
        solution_col=4,
        moves=[1, 5, 2, 6, 3, 0],
        player_to_move=1,
        explanation="Playing Column 5 (index 4) completes the horizontal four-in-a-row along the bottom rank!",
    ),
    Puzzle(
        id=2,
        title="Emergency Block",
        difficulty="Easy",
        description="Player 2 (Gold) is about to win vertically. Find the only legal move that prevents instant defeat!",
        solution_col=2,
        moves=[3, 2, 4, 2, 5, 2],
        player_to_move=1,
        explanation="Column 3 (index 2) blocks Player 2's vertical stack before they connect 4!",
    ),
    Puzzle(
        id=3,
        title="The Double-Threat Fork",
        difficulty="Medium",
        description="Create an open-ended 3-in-a-row that creates two simultaneous win threats your opponent cannot stop!",
        solution_col=4,
        moves=[2, 0, 3, 6],
        player_to_move=1,
        explanation="Playing Column 5 (index 4) forms an open-ended 3-in-a-row (cols 2, 3, 4). The opponent can only block one side, guaranteeing your victory next turn!",
    ),
    Puzzle(
        id=4,
        title="Ascending Diagonal Strike",
        difficulty="Hard",
        description="Spot the hidden diagonal alignment across multiple column levels for an instant win!",
        solution_col=3,
        moves=[0, 1, 1, 2, 3, 2, 2, 3, 4, 3],
        player_to_move=1,
        explanation="Dropping into Column 4 (index 3) lands at row height 3, completing the ascending diagonal from (0,0) to (3,3)!",
    ),
    Puzzle(
        id=5,
        title="Inside Gap Strike",
        difficulty="Medium",
        description="Recognize the split 3-in-a-row pattern and fill the internal pocket for a clean kill!",
        solution_col=2,
        moves=[0, 6, 1, 5, 3, 4],
        player_to_move=1,
        explanation="Playing Column 3 (index 2) fills the internal gap between columns 0, 1, and 3, locking the 4-in-a-row!",
    ),
]


def get_puzzle(puzzle_id: int) -> Puzzle:
    """Puzzle by 1-based id, clamped to the valid range."""
    return PUZZLES[max(0, min(len(PUZZLES) - 1, puzzle_id - 1))]
