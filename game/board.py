"""Rules-only board model for a 6-by-7 Four in a Row game."""

from __future__ import annotations

from typing import ClassVar

from agents.zobrist import zobrist_key
from config import COLS as CONFIG_COLS
from config import ROWS as CONFIG_ROWS


class Board:
    """Represent a Four in a Row board with row zero at the bottom."""

    ROWS: ClassVar[int] = CONFIG_ROWS
    COLS: ClassVar[int] = CONFIG_COLS

    def __init__(self) -> None:
        """Create an empty board with player one to move first."""
        self.grid: list[list[int]] = [
            [0 for _ in range(self.COLS)] for _ in range(self.ROWS)
        ]
        self.move_history: list[int] = []
        self.hash: int = 0
        self._last_move: tuple[int, int] | None = None

    def legal_moves(self) -> list[int]:
        """Return non-full columns in ascending order."""
        return [
            col for col in range(self.COLS) if self.grid[self.ROWS - 1][col] == 0
        ]

    def current_player(self) -> int:
        """Return the player whose turn it is, derived from the move count."""
        return 1 if len(self.move_history) % 2 == 0 else 2

    def drop(self, col: int) -> int:
        """Place the current player's disc in ``col`` and return its row."""
        if isinstance(col, bool) or not isinstance(col, int):
            raise ValueError("Column must be an integer.")
        if col < 0 or col >= self.COLS:
            raise ValueError(f"Column must be between 0 and {self.COLS - 1}.")

        for row in range(self.ROWS):
            if self.grid[row][col] == 0:
                player = self.current_player()
                self.grid[row][col] = player
                self.hash ^= zobrist_key(row, col, player)
                self.move_history.append(col)
                self._last_move = (row, col)
                return row
        raise ValueError("Column is full.")

    def undo(self) -> int:
        """Remove the most recently played disc and return its column."""
        if not self.move_history:
            raise ValueError("Cannot undo an empty board.")

        col = self.move_history.pop()
        for row in range(self.ROWS - 1, -1, -1):
            if self.grid[row][col] != 0:
                player = self.grid[row][col]
                self.grid[row][col] = 0
                self.hash ^= zobrist_key(row, col, player)
                self._last_move = self._last_move_from_history()
                return col
        raise RuntimeError("Move history does not match the board state.")

    def winner(self) -> int:
        """Return the winning player, or zero when no last move made a line of four."""
        cells = self._winning_line_from_last_move()
        return self.grid[cells[0][0]][cells[0][1]] if cells else 0

    def is_full(self) -> bool:
        """Return whether every column is full."""
        return all(self.grid[self.ROWS - 1][col] != 0 for col in range(self.COLS))

    def is_terminal(self) -> bool:
        """Return whether the game has a winner or no legal moves left."""
        return self.winner() != 0 or self.is_full()

    def winning_cells(self) -> list[tuple[int, int]]:
        """Return the four cells of the line made by the last winning move."""
        return self._winning_line_from_last_move()

    def copy(self) -> Board:
        """Return an independent board with the same state and move history."""
        duplicate = Board()
        duplicate.grid = [row.copy() for row in self.grid]
        duplicate.move_history = self.move_history.copy()
        duplicate.hash = self.hash
        duplicate._last_move = self._last_move
        return duplicate

    def to_string(self) -> str:
        """Return the board as six top-to-bottom rows using ``.``/``X``/``O``."""
        symbols = {0: ".", 1: "X", 2: "O"}
        return "\n".join(
            "".join(symbols[self.grid[row][col]] for col in range(self.COLS))
            for row in range(self.ROWS - 1, -1, -1)
        )

    @classmethod
    def from_string(cls, s: str) -> Board:
        """Create a board from six top-first rows of ``.``/``X``/``O`` cells."""
        if not isinstance(s, str):
            raise ValueError("Board text must be a string.")

        lines = [line.strip() for line in s.strip().splitlines()]
        if len(lines) != cls.ROWS or any(len(line) != cls.COLS for line in lines):
            raise ValueError("Board text must contain six rows of seven cells.")

        board = cls()
        symbols = {".": 0, "X": 1, "O": 2}
        for display_row, line in enumerate(lines):
            if any(cell not in symbols for cell in line):
                raise ValueError("Board text may contain only '.', 'X', and 'O'.")
            row = cls.ROWS - 1 - display_row
            board.grid[row] = [symbols[cell] for cell in line]

        board._validate_position()
        board.hash = board._calculate_hash()
        board.move_history = board._reconstruct_history()
        board._last_move = board._last_move_from_history()
        return board

    def _validate_position(self) -> None:
        """Reject board text that cannot describe a gravity-based game state."""
        player_one = sum(cell == 1 for row in self.grid for cell in row)
        player_two = sum(cell == 2 for row in self.grid for cell in row)
        if player_two > player_one or player_one - player_two > 1:
            raise ValueError("Board text has an invalid number of discs per player.")

        for col in range(self.COLS):
            found_empty = False
            for row in range(self.ROWS):
                if self.grid[row][col] == 0:
                    found_empty = True
                elif found_empty:
                    raise ValueError("Board text contains a disc floating above an empty cell.")

    def _reconstruct_history(self) -> list[int]:
        """Rebuild one legal alternating move order for a parsed board state."""
        stacks = [
            [self.grid[row][col] for row in range(self.ROWS) if self.grid[row][col]]
            for col in range(self.COLS)
        ]
        used = [0] * self.COLS
        history: list[int] = []
        failed_states: set[tuple[int, ...]] = set()

        def build() -> bool:
            if len(history) == sum(len(stack) for stack in stacks):
                return True
            state = tuple(used)
            if state in failed_states:
                return False

            player = 1 if len(history) % 2 == 0 else 2
            for col, stack in enumerate(stacks):
                if used[col] < len(stack) and stack[used[col]] == player:
                    used[col] += 1
                    history.append(col)
                    if build():
                        return True
                    history.pop()
                    used[col] -= 1
            failed_states.add(state)
            return False

        if not build():
            raise ValueError("Board text cannot be reached by alternating legal moves.")
        return history

    def _last_move_from_history(self) -> tuple[int, int] | None:
        """Find the board location of the most recent recorded move."""
        if not self.move_history:
            return None

        col = self.move_history[-1]
        for row in range(self.ROWS - 1, -1, -1):
            if self.grid[row][col] != 0:
                return row, col
        return None

    def _calculate_hash(self) -> int:
        """Calculate the Zobrist hash of the current grid for parsed positions."""
        value = 0
        for row in range(self.ROWS):
            for col in range(self.COLS):
                player = self.grid[row][col]
                if player != 0:
                    value ^= zobrist_key(row, col, player)
        return value

    def _winning_line_from_last_move(self) -> list[tuple[int, int]]:
        """Find a four-cell line through the last played disc, if one exists."""
        if self._last_move is None:
            return []

        row, col = self._last_move
        player = self.grid[row][col]
        if player == 0:
            return []

        for row_step, col_step in ((0, 1), (1, 0), (1, 1), (1, -1)):
            before = self._collect_matching_cells(
                row, col, -row_step, -col_step, player
            )
            after = self._collect_matching_cells(row, col, row_step, col_step, player)
            line = list(reversed(before)) + [(row, col)] + after
            if len(line) >= 4:
                last_index = len(before)
                start = min(max(0, last_index - 3), len(line) - 4)
                return line[start : start + 4]
        return []

    def _collect_matching_cells(
        self, row: int, col: int, row_step: int, col_step: int, player: int
    ) -> list[tuple[int, int]]:
        """Collect adjacent cells for ``player`` in one direction."""
        cells: list[tuple[int, int]] = []
        row += row_step
        col += col_step
        while 0 <= row < self.ROWS and 0 <= col < self.COLS:
            if self.grid[row][col] != player:
                break
            cells.append((row, col))
            row += row_step
            col += col_step
        return cells
