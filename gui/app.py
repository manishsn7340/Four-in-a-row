"""Connect Four Lab: the Pygame app. Run with `python -m gui.app`.

The AI and the hint search run in background threads so the window never
freezes; their results come back through a _SearchResultGate, which drops
any result that belongs to a game that has since been reset."""

from __future__ import annotations

import threading
from time import perf_counter

import pygame

import gui.theme as T
from agents.alphabeta import AlphaBetaAgent
from agents.base import Agent
from agents.mcts import MCTSAgent
from agents.simple import RandomAgent
from game.board import Board
from gui.animation import ConfettiBurst, DiscDrop, WinPulse
from gui.banner import draw_banner, draw_puzzle_banner
from gui.board_view import (BOARD_H, BOARD_W, column_from_x, draw_board, draw_hint_overlay,
                            draw_hover_arrow, player_color)
from gui.hint import analyze
from gui.opening_book import lookup as book_lookup
from gui.panel import MODE_AVAI, MODE_HVA, MODE_HVH, MODE_PUZZLE, _norm_eval, draw_panel
from gui.puzzles import PUZZLES
from gui.screens import demo_board, show_results_screen, show_start_menu
from gui.sound import SoundManager
from gui.widgets import Button, Dropdown, Slider, is_left_click

AGENT_NAMES = ["Rookie (AB d=2)", "Tactician (AB d=5)", "Grandmaster (AB d=7)", "Gambler (MCTS)", "Random"]
MENU_MODES = {"hva": MODE_HVA, "hvh": MODE_HVH, "avai": MODE_AVAI}


def _make_agent(name: str) -> Agent:
    """Build an agent from its menu label."""
    if "Rookie" in name:
        return AlphaBetaAgent(depth=2, use_tt=True, name="Rookie")
    if "Tactician" in name:
        return AlphaBetaAgent(depth=5, use_tt=True, name="Tactician")
    if "Grandmaster" in name:
        return AlphaBetaAgent(depth=7, use_iterative_deepening=True, time_limit=1.5, use_tt=True, name="Grandmaster")
    if "Gambler" in name:
        return MCTSAgent(simulations=1000, name="Gambler")
    return RandomAgent(name="Random", seed=42)


class _SearchResultGate:
    """Thread-safe mailbox for background results, tagged with the game 'generation'
    that asked for them. invalidate() starts a new generation and old results are dropped."""

    def __init__(self) -> None:
        self._generation = 0
        self._pending: list[tuple[int, object]] = []
        self._lock = threading.Lock()

    @property
    def generation(self) -> int:
        with self._lock:
            return self._generation

    def invalidate(self) -> None:
        with self._lock:
            self._generation += 1
            self._pending.clear()

    def submit(self, generation: int, result: object) -> None:
        with self._lock:
            self._pending.append((generation, result))

    def take_current(self):
        with self._lock:
            while self._pending:
                generation, result = self._pending.pop(0)
                if generation == self._generation:
                    return result
        return None

    def run_in_background(self, work, *args) -> None:
        generation = self.generation
        threading.Thread(target=lambda: self.submit(generation, work(*args)), daemon=True).start()


def _layout() -> dict[str, Button]:
    y = T.WIN_H - 56
    spec = {  # name: (x, width, label, icon, variant)
        "hva": (20, 108, "You vs AI", None, "segment"), "hvh": (132, 108, "2 Players", None, "segment"),
        "avai": (244, 108, "AI vs AI", None, "segment"), "hint": (376, 88, "Hint", "bulb", "default"),
        "puzzle": (470, 106, "Puzzles", "puzzle", "default"), "demo": (582, 92, "Demo", "demo", "default"),
        "sound": (798, 44, "", "sound", "default"), "results": (T.WIN_W - 318, 106, "Results", "chart", "default"),
        "undo": (T.WIN_W - 208, 82, "Undo", None, "default"),
        "new": (T.WIN_W - 122, 102, "New Game", None, "primary"),
    }
    buttons = {name: Button((x, y, w, 40), label, icon, variant) for name, (x, w, label, icon, variant) in spec.items()}
    buttons["menu"] = Button((T.WIN_W - 540, 10, 92, 34), "Menu")
    buttons["theme"] = Button((T.WIN_W - 440, 10, 92, 34))
    return buttons


class Game:
    def __init__(self, screen: pygame.Surface, fonts: dict, clock: pygame.time.Clock, mode: str) -> None:
        self.screen, self.fonts, self.clock = screen, fonts, clock
        self.sound = SoundManager()
        self.buttons = _layout()
        self.opponent = Dropdown((T.WIN_W - 270, 10, 250, 34), AGENT_NAMES, initial=1)
        self.delay = Slider((690, T.WIN_H - 34, 92, 10), 0.0, 2.0, 0.5, label="AI delay")
        self.progress: dict = {}
        self.agents = {1: self._agent(AGENT_NAMES[0]), 2: self._agent(AGENT_NAMES[1])}
        self.ai_results, self.hint_results = _SearchResultGate(), _SearchResultGate()
        self.win_streak = 0
        self.puzzle_idx = 0
        self.demo_seed = 0
        self.show_details = False
        self.details_rect = pygame.Rect(0, 0, 0, 0)
        self.t = 0.0
        self.reset(mode)

    # ── game state ───────────────────────────────────────────────────────────

    def _agent(self, name: str) -> Agent:
        agent = _make_agent(name)
        agent.on_progress = self.progress.update
        return agent

    def reset(self, mode: str | None = None, board: Board | None = None) -> None:
        """Start a new game (optionally in another mode or from a given position)."""
        self.mode = mode or self.mode
        self.board = board or Board()
        self.ai_results.invalidate()
        self.hint_results.invalidate()
        self.thinking = self.hint_pending = self.game_over = False
        self.win_cells: list[tuple[int, int]] = []
        self.banner = ""
        self.drop = self.pulse = self.confetti = None
        self._clear_hint()
        self.display_eval = 0.0
        self.move_ready_at = 0.0
        self.puzzle_solved_at: float | None = None
        self.progress.clear()
        self.clocks = {1: 0.0, 2: 0.0}
        self.turn_started = perf_counter()
        self._update_status()

    def _clear_hint(self) -> None:
        """Hide the hint and drop any hint search still running."""
        self.hint_scores, self.hint_reason = {}, ""
        self.hint_results.invalidate()
        self.hint_pending = False

    def start_puzzle(self, idx: int) -> None:
        self.puzzle_idx = idx % len(PUZZLES)
        self.reset(MODE_PUZZLE, PUZZLES[self.puzzle_idx].create_board())

    def start_demo(self) -> None:
        """AI vs AI between two Rookies from a new seeded opening each time."""
        self.agents = {1: self._agent(AGENT_NAMES[0]), 2: self._agent(AGENT_NAMES[0])}
        self.demo_seed += 1
        self.reset(MODE_AVAI, demo_board(self.demo_seed))
        self.delay.value = 0.8
        self.status = f"Demo #{self.demo_seed}: click Demo again for a new opening"

    def is_ai_turn(self) -> bool:
        return self.mode == MODE_AVAI or (self.mode == MODE_HVA and self.board.current_player() == 2)

    def busy(self) -> bool:
        return self.game_over or self.thinking or (self.drop is not None and not self.drop.done)

    def play(self, col: int) -> None:
        """Drop a disc for the player to move and handle the consequences."""
        if col not in self.board.legal_moves():
            return
        player = self.board.current_player()
        now = perf_counter()
        self.clocks[player] += now - self.turn_started
        self.turn_started = now
        row = self.board.drop(col)
        self.drop = DiscDrop(col, row, player_color(player))
        self.pulse = self.confetti = None
        self._clear_hint()
        self.progress.clear()
        self.move_ready_at = now + self.delay.value
        self.sound.play_drop()
        if self.mode == MODE_PUZZLE:
            self._check_puzzle(col, row)
            return

        winner = self.board.winner()
        if winner or self.board.is_full():
            self.game_over = True
            self.win_cells = self.board.winning_cells()
            self.banner = self._result_text(winner)
            if winner:
                self.confetti = ConfettiBurst(self.win_cells)
                self.sound.play_win()
            if self.mode == MODE_HVA:
                self._adjust_difficulty(winner)
        self._update_status()

    def _check_puzzle(self, col: int, row: int) -> None:
        puzzle = PUZZLES[self.puzzle_idx]
        if col != puzzle.solution_col:
            self.sound.play_click()
            self.board = puzzle.create_board()
            self.drop = None
            self.status = f"Column {col + 1} is not correct. Try again!"
            return
        self.sound.play_win()
        self.game_over = True
        self.puzzle_solved_at = perf_counter()
        self.win_cells = self.board.winning_cells()
        self.confetti = ConfettiBurst(self.win_cells or [(row, col)])
        self.status = f"Puzzle {puzzle.id} solved! Next challenge in 2 s..."

    def _result_text(self, winner: int) -> str:
        if not winner:
            return "Draw Game!"
        if self.mode == MODE_HVA:
            return "Victory! You Win!" if winner == 1 else f"{self.agents[2].name} Wins!"
        return f"Player {winner} Wins!" if self.mode == MODE_HVH else f"{self.agents[winner].name} Wins!"

    def _adjust_difficulty(self, winner: int) -> None:
        """Two wins in a row move the opponent one level up (up to Gambler)."""
        self.win_streak = self.win_streak + 1 if winner == 1 else 0
        level = self.opponent.selected
        if self.win_streak >= 2 and level < 3:
            self.opponent.selected = level + 1
            self.agents[2] = self._agent(self.opponent.value)

    def _update_status(self) -> None:
        turn = self.board.current_player()
        if self.game_over:
            self.status = self.banner
        elif self.mode == MODE_PUZZLE:
            p = PUZZLES[self.puzzle_idx]
            self.status = f"Puzzle {p.id}/{len(PUZZLES)}: {p.title} ({p.difficulty})"
        elif self.mode == MODE_AVAI:
            self.status = f"P{turn} ({self.agents[turn].name}) computing..."
        elif self.mode == MODE_HVH:
            self.status = f"Player {turn} ({'Coral' if turn == 1 else 'Gold'}) — drop your disc"
        elif turn == 2:
            self.status = f"{self.agents[2].name} thinking..."
        else:
            book = book_lookup(self.board.move_history)
            self.status = f"Your turn — book suggests column {book + 1}" if book is not None else "Your turn (Coral)"

    def undo(self) -> None:
        """Take back one move (two against the computer, so it is your turn again)."""
        if self.mode == MODE_PUZZLE:
            self.start_puzzle(self.puzzle_idx)
        elif self.mode != MODE_AVAI and not self.busy():
            for _ in range(2 if self.mode == MODE_HVA else 1):
                if self.board.move_history:
                    self.board.undo()
            self._clear_hint()
            self._update_status()

    def request_hint(self) -> None:
        """Toggle the hint: start a search, or hide the hint already shown."""
        if self.mode not in (MODE_HVA, MODE_HVH) or self.busy() or self.hint_pending:
            return
        if self.hint_scores:
            self._clear_hint()
        else:
            self.hint_pending = True
            self.hint_results.run_in_background(analyze, self.board.copy(), 3)

    # ── per-frame update ────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        self.t += dt
        if self.drop and not self.drop.done:
            self.drop.update(dt)
            if self.drop.done and self.win_cells:
                self.pulse = WinPulse(self.win_cells)
        elif self.pulse:
            self.pulse.update(dt)
        if self.confetti and not self.confetti.done:
            self.confetti.update(dt)
        self.display_eval += (_norm_eval(self.board) - self.display_eval) * min(1.0, 8.0 * dt)

        hint = self.hint_results.take_current()
        if hint is not None:
            self.hint_pending = False
            self.hint_scores, self.hint_reason = hint
            self.sound.play_hint()

        if self.thinking and self.drop_finished():
            move = self.ai_results.take_current()
            if move is not None:
                self.thinking = False
                self.play(move)

        if self.puzzle_solved_at and perf_counter() - self.puzzle_solved_at >= 2.0:
            self.start_puzzle(self.puzzle_idx + 1)

        if self.is_ai_turn() and not self.busy() and perf_counter() >= self.move_ready_at:
            self.thinking = True
            self.ai_results.run_in_background(self.agents[self.board.current_player()].choose_move,
                                              self.board.copy())

    def drop_finished(self) -> bool:
        return self.drop is None or self.drop.done

    def hover_column(self, pos: tuple[int, int] | None = None) -> int | None:
        """Column under the mouse if the human may play there now, else None."""
        x, y = pos or pygame.mouse.get_pos()
        human = self.mode != MODE_AVAI and not self.is_ai_turn()
        if human and not self.busy() and not self.opponent.open and 55 <= y <= T.BOARD_TOP + BOARD_H + 20:
            return column_from_x(x)
        return None

    # ── input ────────────────────────────────────────────────────────────────

    def handle(self, event: pygame.event.Event) -> bool:
        """Process one event; return False when the app should quit."""
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            return self._key(event.key)

        b = self.buttons
        if is_left_click(event) and self.details_rect.collidepoint(event.pos) and not self.opponent.open:
            self.show_details = not self.show_details
            self.sound.play_click()
            return True
        if self.mode in (MODE_HVA, MODE_AVAI) and self.opponent.handle_event(event):
            self.sound.play_click()
            self.agents[2] = self._agent(self.opponent.value)
            self.reset()
            return True

        actions = {
            "menu": self._open_menu, "theme": T.toggle_theme, "results": self._open_results,
            "hva": lambda: self.reset(MODE_HVA), "hvh": lambda: self.reset(MODE_HVH),
            "avai": lambda: self.reset(MODE_AVAI), "hint": self.request_hint, "demo": self.start_demo,
            "puzzle": lambda: self.start_puzzle(self.puzzle_idx + 1 if self.mode == MODE_PUZZLE else 0),
            "new": self._restart, "undo": self.undo, "sound": self._toggle_sound,
        }
        for name, action in actions.items():
            if b[name].clicked(event):
                if name != "sound":
                    self.sound.play_click()
                return action() is not False

        if self.mode in (MODE_HVA, MODE_AVAI):
            self.delay.handle_event(event)
        if is_left_click(event):
            if self.mode == MODE_PUZZLE and self.game_over:
                self.start_puzzle(self.puzzle_idx + 1)
            elif (col := self.hover_column(event.pos)) is not None:
                self.play(col)
        return True

    def _key(self, key: int) -> bool:
        if key == pygame.K_ESCAPE:
            return False
        if key in (pygame.K_SPACE, pygame.K_RETURN) and self.mode == MODE_PUZZLE and self.game_over:
            self.start_puzzle(self.puzzle_idx + 1)
        else:
            action = {pygame.K_r: self._restart, pygame.K_h: self.request_hint, pygame.K_l: T.toggle_theme,
                      pygame.K_m: self._toggle_sound,
                      pygame.K_p: lambda: self.start_puzzle(self.puzzle_idx + 1 if self.mode == MODE_PUZZLE else 0),
                      }.get(key)
            if action:
                action()
        return True

    def _restart(self) -> None:
        self.start_puzzle(self.puzzle_idx) if self.mode == MODE_PUZZLE else self.reset()

    def _toggle_sound(self) -> None:
        self.buttons["sound"].muted = self.sound.toggle_mute()

    def _open_results(self) -> None:
        show_results_screen(self.screen, self.fonts, self.clock)

    def _open_menu(self) -> bool:
        self.ai_results.invalidate()
        choice = show_start_menu(self.screen, self.fonts, self.clock)
        if choice == "quit":
            return False
        self.reset(MENU_MODES[choice])
        return True

    # ── drawing ──────────────────────────────────────────────────────────────

    def draw(self) -> None:
        s, f = self.screen, self.fonts
        s.fill(T.BG)
        s.blit(f["lg"].render("Connect Four Lab", True, T.TEXT), (T.BOARD_LEFT, 8))
        s.blit(f["sm"].render("Strategy coach with a window into the AI's thinking", True, T.DIM_TEXT),
               (T.BOARD_LEFT, 40))
        self._draw_clocks()

        board = self.board
        falling = self.drop is not None and not self.drop.done
        hover = self.hover_column()
        draw_board(s, board, self.win_cells,
                   skip_cell=(self.drop.row, self.drop.col) if falling else None,
                   ghost_col=hover, ghost_player=board.current_player())
        if hover is not None:
            draw_hover_arrow(s, hover, player_color(board.current_player()), self.t)
        if falling:
            self.drop.draw(s)
        if self.pulse and not falling:
            self.pulse.draw(s)
        if self.confetti:
            self.confetti.draw(s)
        draw_hint_overlay(s, f, self.hint_scores, self.hint_reason)
        self.details_rect = draw_panel(s, f, self, self.t)

        b = self.buttons
        for name, button in b.items():
            active = {"hva": self.mode == MODE_HVA, "hvh": self.mode == MODE_HVH, "avai": self.mode == MODE_AVAI,
                      "puzzle": self.mode == MODE_PUZZLE, "hint": self.hint_pending}.get(name, False)
            if name == "theme":
                button.label = "Light" if T.THEME_NAME == "dark" else "Dark"
            button.draw(s, f, active)
        if self.mode in (MODE_HVA, MODE_AVAI):
            self.delay.draw(s, f)

        if self.mode == MODE_HVA and self.win_streak >= 2:
            text = f["sm"].render(f"Win streak {self.win_streak}! Opponent: {self.agents[2].name}", True, T.WIN_GLOW)
            s.blit(text, text.get_rect(centerx=T.BOARD_LEFT + BOARD_W // 2, top=T.BOARD_TOP - 90))
        if self.game_over and not falling:
            if self.mode == MODE_PUZZLE:
                draw_puzzle_banner(s, f, self.puzzle_idx + 1, len(PUZZLES))
            else:
                draw_banner(s, f, self.banner)
        if self.mode in (MODE_HVA, MODE_AVAI):  # drawn last so the open list covers everything
            s.blit(f["sm"].render("Opponent", True, T.DIM_TEXT), (self.opponent.rect.left - 70, 19))
            self.opponent.draw(s, f)

    def _draw_clocks(self) -> None:
        """Total thinking time per player, in a pill at the top right of the board."""
        pill = pygame.Rect(T.BOARD_LEFT + BOARD_W - 176, 10, 176, 32)
        pygame.draw.rect(self.screen, T.SURFACE, pill, border_radius=16)
        pygame.draw.rect(self.screen, T.BORDER, pill, width=1, border_radius=16)
        for i, player in enumerate((1, 2)):
            x = pill.left + 16 + i * 84
            pygame.draw.circle(self.screen, player_color(player), (x, pill.centery), 6)
            secs = int(self.clocks[player])
            self.screen.blit(self.fonts["sm"].render(f"{secs // 60:02d}:{secs % 60:02d}", True, T.TEXT),
                             (x + 14, pill.top + 7))


def run() -> None:
    pygame.init()
    # SCALED keeps the 1280x800 layout and maps the mouse when the window is resized.
    screen = pygame.display.set_mode((T.WIN_W, T.WIN_H), pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption("Connect Four Lab")
    fonts, clock = T.load_fonts(), pygame.time.Clock()
    choice = show_start_menu(screen, fonts, clock)
    if choice != "quit":
        game = Game(screen, fonts, clock, MENU_MODES[choice])
        running = True
        while running:
            dt = clock.tick(T.FPS) / 1000.0
            running = all([game.handle(event) for event in pygame.event.get()])
            game.update(dt)
            game.draw()
            pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    run()
