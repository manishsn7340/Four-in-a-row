"""Connect Four board: a 6x7 grid with row 0 at the bottom."""

from __future__ import annotations

from agents.zobrist import zobrist_key
from config import COLS, ROWS

SYMBOLS = {0: ".", 1: "X", 2: "O"}
DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


class Board:
    ROWS = ROWS
    COLS = COLS

    def __init__(self) -> None:
        self.grid = [[0] * COLS for _ in range(ROWS)]
        self.move_history: list[int] = []
        self.hash = 0  # Zobrist hash, updated on every drop/undo

    def legal_moves(self) -> list[int]:
        return [c for c in range(COLS) if self.grid[ROWS - 1][c] == 0]

    def current_player(self) -> int:
        return 1 if len(self.move_history) % 2 == 0 else 2

    def drop(self, col: int) -> int:
        """Drop the current player's disc into `col` and return the row it lands on."""
        if type(col) is not int or not 0 <= col < COLS:
            raise ValueError(f"Column must be an integer from 0 to {COLS - 1}.")
        if self.grid[ROWS - 1][col]:
            raise ValueError("Column is full.")
        row = self.height(col)
        player = self.current_player()
        self.grid[row][col] = player
        self.hash ^= zobrist_key(row, col, player)
        self.move_history.append(col)
        return row

    def undo(self) -> int:
        """Take back the last move and return its column."""
        if not self.move_history:
            raise ValueError("Cannot undo an empty board.")
        col = self.move_history.pop()
        row = self.height(col) - 1
        self.hash ^= zobrist_key(row, col, self.grid[row][col])
        self.grid[row][col] = 0
        return col

    def winner(self) -> int:
        """Return 1 or 2 if the last move made four in a row, otherwise 0."""
        cells = self.winning_cells()
        return self.grid[cells[0][0]][cells[0][1]] if cells else 0

    def winning_cells(self) -> list[tuple[int, int]]:
        """Return four winning cells through the last move, or [] if there are none."""
        if not self.move_history:
            return []
        col = self.move_history[-1]
        row = self.height(col) - 1
        player = self.grid[row][col]
        for dr, dc in DIRECTIONS:
            back = self._run(row, col, -dr, -dc, player)
            line = back[::-1] + [(row, col)] + self._run(row, col, dr, dc, player)
            if len(line) >= 4:
                # Prefer a window that contains the last move as early as possible.
                start = min(max(0, len(back) - 3), len(line) - 4)
                return line[start:start + 4]
        return []

    def would_win(self, col: int, player: int) -> bool:
        """True if `player` dropping into the (non-full) column `col` makes four."""
        row = self.height(col)
        return any(
            len(self._run(row, col, -dr, -dc, player)) + len(self._run(row, col, dr, dc, player)) >= 3
            for dr, dc in DIRECTIONS
        )

    def is_full(self) -> bool:
        return all(self.grid[ROWS - 1])

    def is_terminal(self) -> bool:
        return self.is_full() or self.winner() != 0

    def copy(self) -> Board:
        clone = Board()
        clone.grid = [row[:] for row in self.grid]
        clone.move_history = self.move_history[:]
        clone.hash = self.hash
        return clone

    def to_string(self) -> str:
        """Top row first, using '.', 'X' (player 1) and 'O' (player 2)."""
        return "\n".join("".join(SYMBOLS[v] for v in row) for row in reversed(self.grid))

    @classmethod
    def from_string(cls, text: str) -> Board:
        """Parse the format produced by `to_string` and rebuild a legal move history."""
        lines = [line.strip() for line in text.strip().splitlines()]
        if len(lines) != ROWS or any(len(line) != COLS for line in lines):
            raise ValueError(f"Board text must have {ROWS} rows of {COLS} cells.")
        lookup = {s: v for v, s in SYMBOLS.items()}
        board = cls()
        try:
            board.grid = [[lookup[ch] for ch in line] for line in reversed(lines)]
        except KeyError:
            raise ValueError("Board text may contain only '.', 'X' and 'O'.") from None
        for c in range(COLS):
            column = [board.grid[r][c] for r in range(ROWS)]
            if 0 in column and any(column[column.index(0):]):
                raise ValueError("Board text contains a floating disc.")
        board.move_history = board._rebuild_history()
        board.hash = board._calculate_hash()
        return board

    # ── helpers ──────────────────────────────────────────────────────────────

    def height(self, col: int) -> int:
        """Number of discs in `col`."""
        return sum(1 for r in range(ROWS) if self.grid[r][col])

    def _run(self, row: int, col: int, dr: int, dc: int, player: int) -> list[tuple[int, int]]:
        """Cells of `player` next to (row, col), walking in direction (dr, dc)."""
        cells = []
        row, col = row + dr, col + dc
        while 0 <= row < ROWS and 0 <= col < COLS and self.grid[row][col] == player:
            cells.append((row, col))
            row, col = row + dr, col + dc
        return cells

    def _calculate_hash(self) -> int:
        h = 0
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c]:
                    h ^= zobrist_key(r, c, self.grid[r][c])
        return h

    def _rebuild_history(self) -> list[int]:
        """Find one alternating move order that produces the current grid (DFS)."""
        stacks = [[self.grid[r][c] for r in range(ROWS) if self.grid[r][c]] for c in range(COLS)]
        total = sum(map(len, stacks))
        used = [0] * COLS
        history: list[int] = []
        dead_ends: set[tuple[int, ...]] = set()

        def search() -> bool:
            if len(history) == total:
                return True
            if tuple(used) in dead_ends:
                return False
            player = 1 if len(history) % 2 == 0 else 2
            for c in range(COLS):
                if used[c] < len(stacks[c]) and stacks[c][used[c]] == player:
                    used[c] += 1
                    history.append(c)
                    if search():
                        return True
                    used[c] -= 1
                    history.pop()
            dead_ends.add(tuple(used))
            return False

        if not search():
            raise ValueError("Board text cannot be reached by alternating legal moves.")
        return history
