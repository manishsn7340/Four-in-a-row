"""gui/app.py — Connect Four Strategy Coach & AI Reasoning Engine.

Master GUI application orchestrating game loop, event dispatch, AI background
threading, tactical puzzles, and analysis panels.
"""

from __future__ import annotations

import math
import sys
import threading
from time import perf_counter

import pygame

from agents.alphabeta import AlphaBetaAgent
from agents.base import Agent
from agents.evaluation import WIN_SCORE
from agents.mcts import MCTSAgent
from agents.simple import RandomAgent
from game.board import Board
from gui.animation import ConfettiBurst, DiscDrop, WinPulse
from gui.banner import draw_banner, draw_puzzle_banner, wrap_text
from gui.board_view import (
    P1_COLOR,
    P2_COLOR,
    board_pixel,
    column_from_x,
    darken,
    draw_background,
    draw_board,
    draw_column_scores,
    draw_hint_overlay,
    draw_hover_arrow,
)
from gui.hint import analyze as hint_analyze
from gui.icons import (
    make_bulb_icon,
    make_chart_icon,
    make_clock_icon,
    make_demo_icon,
    make_export_icon,
    make_human_icon,
    make_puzzle_icon,
    make_robot_icon,
    make_sound_icon,
)
from gui.opening_book import lookup as book_lookup
from gui.panel import (
    MODE_AVAI,
    MODE_HVA,
    MODE_HVH,
    MODE_PUZZLE,
    _norm_eval,
    draw_eval_bar,
    draw_panel,
)
from gui.puzzles import PUZZLES
from gui.replay import ReplayManager
from gui.screens import demo_board, show_results_screen, show_start_menu
from gui.sound import SoundManager
import gui.theme as T
from gui.widgets import Button, Dropdown, Slider

# ── Public interface re-exports ───────────────────────────────────────────────
__all__ = [
    "run",
    "MODE_HVA",
    "MODE_HVH",
    "MODE_AVAI",
    "MODE_PUZZLE",
    "_make_agent",
    "_norm_eval",
    "column_from_x",
    "draw_puzzle_banner",
    "wrap_text",
    "Button",
]

# ── Agent catalogue ───────────────────────────────────────────────────────────
_AGENT_NAMES: list[str] = [
    "Rookie (AB d=2)",
    "Tactician (AB d=5)",
    "Grandmaster (AB d=7)",
    "Gambler (MCTS)",
    "Random",
]


def _make_agent(name: str) -> Agent:
    """Instantiate an agent from its UI label."""
    if "Rookie" in name:
        return AlphaBetaAgent(depth=2, name="Rookie")
    if "Tactician" in name:
        return AlphaBetaAgent(depth=5, name="Tactician")
    if "Grandmaster" in name:
        return AlphaBetaAgent(depth=7, use_iterative_deepening=True, time_limit=1.5, name="Grandmaster")
    if "Gambler" in name:
        return MCTSAgent(simulations=1000, name="Gambler")
    return RandomAgent(name="Random", seed=42)


class _SearchResultGate:
    """Keep completed AI moves tied to the game session that requested them."""

    def __init__(self) -> None:
        self._generation = 0
        self._pending: list[tuple[int, int]] = []
        self._lock = threading.Lock()

    @property
    def generation(self) -> int:
        """Return the identifier for the current game session."""
        with self._lock:
            return self._generation

    def invalidate(self) -> None:
        """Start a fresh session and discard any completed move waiting to apply."""
        with self._lock:
            self._generation += 1
            self._pending.clear()

    def submit(self, generation: int, move: int) -> None:
        """Store a completed move together with its originating session identifier."""
        with self._lock:
            self._pending.append((generation, move))

    def take_current(self) -> int | None:
        """Return one current-session move and discard completed stale moves."""
        with self._lock:
            while self._pending:
                generation, move = self._pending.pop(0)
                if generation == self._generation:
                    return move
        return None


# ── Main Loop ─────────────────────────────────────────────────────────────────

def run() -> None:
    """Main application loop."""
    pygame.init()
    # SCALED keeps the 1280x800 layout and maps the mouse when the window is resized
    screen = pygame.display.set_mode((T.WIN_W, T.WIN_H), pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption("Connect Four Lab  ✦  Strategy Coach & AI Reasoning")
    clock = pygame.time.Clock()
    fonts = T.load_fonts()

    show_details = False                 # engine-details section of the coach panel
    details_rect = pygame.Rect(0, 0, 0, 0)
    sound_mgr = SoundManager()
    t_anim = 0.0

    progress: dict = {}
    replay = ReplayManager()
    ai_results = _SearchResultGate()

    # Per-player clocks (seconds elapsed this game)
    player_clocks: list[float] = [0.0, 0.0, 0.0]  # index 1 and 2
    clock_turn_start: float = 0.0

    # Difficulty ramp: track consecutive P1 wins in HvA mode
    p1_win_streak: int = 0
    _difficulty_levels = ["Rookie (AB d=2)", "Tactician (AB d=5)", "Grandmaster (AB d=7)", "Gambler (MCTS)"]
    _diff_idx: int = 1   # start at Tactician

    export_msg: str = ""  # brief toast message after export
    export_msg_until: float = 0.0

    def _on_progress(data: dict) -> None:
        progress.update(data)

    def _init_agent(name: str) -> Agent:
        agent = _make_agent(name)
        agent.on_progress = _on_progress
        return agent

    p2_agent: Agent = _init_agent(_AGENT_NAMES[1])
    p1_agent: Agent = _init_agent(_AGENT_NAMES[0])
    start_choice = show_start_menu(screen, fonts, clock)
    if start_choice == "quit":
        pygame.quit()
        sys.exit()
    mode = {"hvh": MODE_HVH, "avai": MODE_AVAI}.get(start_choice, MODE_HVA)

    board: Board
    win_cells: list[tuple[int, int]]
    game_over: bool
    banner_msg: str
    status: str
    ai_thinking = False
    anim: DiscDrop | None
    pulse: WinPulse | None
    confetti: ConfettiBurst | None
    display_eval: float
    move_ready_at: float
    hint_scores: dict[int, int]
    hint_reason: str
    hint_thinking: bool
    hint_result: list

    def _cancel_ai_search() -> None:
        """Invalidate the active search before replacing its board or mode."""
        nonlocal ai_thinking
        ai_thinking = False
        ai_results.invalidate()

    def reset() -> None:
        nonlocal board, win_cells, game_over, banner_msg, status
        nonlocal anim, pulse, confetti, display_eval, move_ready_at
        nonlocal hint_scores, hint_reason, hint_thinking, clock_turn_start
        board = Board()
        win_cells = []
        game_over = False
        banner_msg = ""
        _cancel_ai_search()
        anim = None
        pulse = None
        confetti = None
        display_eval = 0.0
        move_ready_at = 0.0
        hint_scores = {}
        hint_reason = ""
        hint_thinking = False
        progress.clear()
        hint_result.clear()
        replay.clear()
        player_clocks[1] = 0.0
        player_clocks[2] = 0.0
        clock_turn_start = perf_counter()

        if mode == MODE_AVAI:
            status = "✦ AI vs AI — watching engine clash"
        elif mode == MODE_HVH:
            status = "✦ Player 1 (Coral) — drop your disc"
        else:
            status = "✦ Your turn (Coral)"

    hint_result = []
    reset()

    def _agent_for(player: int) -> Agent:
        return p2_agent if player == 2 else p1_agent

    def ai_thread_fn(agent: Agent, b_copy: Board, generation: int) -> None:
        """Submit a completed AI move only through its labelled result gate."""
        ai_results.submit(generation, agent.choose_move(b_copy))

    def hint_thread_fn(b_copy: Board) -> None:
        scores, reason = hint_analyze(b_copy, depth=3)
        hint_result.append((scores, reason))

    def finish_move(col: int) -> None:
        nonlocal board, game_over, banner_msg, win_cells, status, anim, pulse, confetti
        nonlocal move_ready_at, hint_scores, hint_reason, clock_turn_start
        nonlocal p1_win_streak, _diff_idx, puzzle_solved_at, p2_agent
        if col not in board.legal_moves():
            return
        hint_scores = {}
        hint_reason = ""

        # Tick clock for the player who just moved
        moved_player = board.current_player()
        player_clocks[moved_player] += perf_counter() - clock_turn_start

        row = board.drop(col)
        replay.record(col)
        dropped_player = 3 - board.current_player()
        disc_color = P1_COLOR if dropped_player == 1 else P2_COLOR

        anim = DiscDrop(col, row, disc_color)
        pulse = None
        confetti = None
        progress.clear()
        move_ready_at = perf_counter() + speed_slider.value
        clock_turn_start = perf_counter()   # restart clock for next player
        sound_mgr.play_drop()

        if mode == MODE_PUZZLE:
            cur_p = PUZZLES[puzzle_idx]
            if col == cur_p.solution_col:
                sound_mgr.play_win()
                game_over = True
                puzzle_solved_at = perf_counter()
                if board.is_terminal():
                    win_cells = board.winning_cells() or []
                    pulse = WinPulse(win_cells)
                    confetti = ConfettiBurst(win_cells)
                else:
                    confetti = ConfettiBurst([(row, col)])
                banner_msg = f"Puzzle {cur_p.id} Solved!"
                status = f"✓ Puzzle {cur_p.id} Solved! Next challenge in 2s..."
            else:
                sound_mgr.play_click()
                status = f"✗ Column {col + 1} is not correct. Try again!"
                banner_msg = "Try again!"
                board = cur_p.create_board()
            return

        w = board.winner()
        if w == 1:
            win_cells = board.winning_cells()
            if mode == MODE_HVH:
                banner_msg = "Player 1 Wins!"
            elif mode == MODE_HVA:
                banner_msg = "Victory! You Win!"
                p1_win_streak += 1
                # Auto-ramp difficulty
                if p1_win_streak >= 2 and _diff_idx < len(_difficulty_levels) - 1:
                    _diff_idx += 1
                    p2_agent_name = _difficulty_levels[_diff_idx]
                    agent_drop.set_value(p2_agent_name)
                    p2_agent = _init_agent(p2_agent_name)
            else:
                banner_msg = "Player 1 Wins!"
            game_over = True
            replay.activate()
            confetti = ConfettiBurst(win_cells)
            sound_mgr.play_win()
        elif w == 2:
            win_cells = board.winning_cells()
            if mode == MODE_HVH:
                banner_msg = "Player 2 Wins!"
            elif mode == MODE_HVA:
                banner_msg = f"{p2_agent.name} Wins!"
                p1_win_streak = 0   # reset on loss
            else:
                banner_msg = f"{p2_agent.name} Wins!"
            game_over = True
            replay.activate()
            confetti = ConfettiBurst(win_cells)
            sound_mgr.play_win()
        elif board.is_full():
            banner_msg = "Draw Game!"
            game_over = True
            replay.activate()
        else:
            nxt = board.current_player()
            if mode == MODE_AVAI:
                status = f"P{nxt} ({_agent_for(nxt).name}) computing..."
            elif mode == MODE_HVH:
                pname = "Coral" if nxt == 1 else "Gold"
                status = f"Player {nxt} ({pname}) — drop your disc"
            elif nxt == 2:
                status = f"{p2_agent.name} thinking..."
            else:
                # Check opening book
                book_col = book_lookup(board.move_history)
                if book_col is not None:
                    status = f"Your turn — Book recommends col {book_col + 1}"
                else:
                    status = "Your turn (Coral)"

    # ── UI layout geometry (1280x760) ─────────────────────────────────────────
    bw = T.BOARD_COLS * T.CELL_SIZE
    btn_y = T.WIN_H - 56
    puzzle_idx: int = 0
    puzzle_solved_at: float | None = None

    def start_puzzle(idx: int) -> None:
        nonlocal mode, board, win_cells, game_over, banner_msg, status, puzzle_idx
        nonlocal anim, pulse, confetti, hint_scores, replay, clock_turn_start, puzzle_solved_at
        _cancel_ai_search()
        mode = MODE_PUZZLE
        puzzle_idx = idx % len(PUZZLES)
        cur_p = PUZZLES[puzzle_idx]
        board = cur_p.create_board()
        win_cells = []
        game_over = False
        puzzle_solved_at = None
        banner_msg = f"Puzzle {cur_p.id}: {cur_p.title}"
        status = f"Puzzle {cur_p.id}/5: {cur_p.title} ({cur_p.difficulty}) — {cur_p.description}"
        anim = None
        pulse = None
        confetti = None
        hint_scores.clear()
        replay.clear()
        clock_turn_start = perf_counter()

    # Bottom bar: mode switch | helpers | AI delay + sound ... file actions | undo, new game
    bh_ = 40
    hva_btn  = Button((20,  btn_y, 108, bh_), label="You vs AI",  variant="segment")
    hvh_btn  = Button((132, btn_y, 108, bh_), label="2 Players",  variant="segment")
    avai_btn = Button((244, btn_y, 108, bh_), label="AI vs AI",   variant="segment")

    hint_btn   = Button((376, btn_y, 88,  bh_), label="Hint",    icon_type="bulb")
    puzzle_btn = Button((470, btn_y, 106, bh_), label="Puzzles", icon_type="puzzle")
    demo_btn   = Button((582, btn_y, 92,  bh_), label="Demo",    icon_type="demo")

    speed_slider = Slider((690, btn_y + 22, 92, 10), 0.0, 2.0, 0.5, label="AI delay")
    sound_btn    = Button((798, btn_y, 44, bh_), icon_type="sound")

    results_btn = Button((T.WIN_W - 424, btn_y, 106, bh_), label="Results", icon_type="chart")
    export_btn  = Button((T.WIN_W - 312, btn_y, 98, bh_), label="Export",  icon_type="export")
    undo_btn    = Button((T.WIN_W - 208, btn_y, 82,  bh_), label="Undo")
    new_btn     = Button((T.WIN_W - 122, btn_y, 102, bh_), label="New Game", variant="primary")

    menu_btn  = Button((T.WIN_W - 20 - 250 - 70 - 92 - 8 - 92 - 8, 10, 92, 34), label="Menu")
    theme_btn = Button((T.WIN_W - 20 - 250 - 70 - 92 - 8, 10, 92, 34), label="")
    agent_drop = Dropdown((T.WIN_W - 20 - 250, 10, 250, 34), _AGENT_NAMES, initial=1)

    # Replay scrub slider (shown only after game ends)
    replay_slider = Slider((T.BOARD_LEFT, T.WIN_H - 98, T.BOARD_COLS * T.CELL_SIZE, 12),
                           0, 1, 1.0, label="")

    demo_seed = 0                        # each Demo click uses the next seed (reproducible)
    running = True
    while running:
        dt = clock.tick(T.FPS) / 1000.0
        t_anim += dt
        mx, my = pygame.mouse.get_pos()
        anim_active = anim is not None and not anim.done


        # Update animations
        if anim_active:
            anim.update(dt)
            if anim.done and game_over and win_cells:
                pulse = WinPulse(win_cells)
        elif pulse:
            pulse.update(dt)

        if confetti and not confetti.done:
            confetti.update(dt)

        # Smooth position eval interpolation
        target_eval = _norm_eval(board)
        display_eval += (target_eval - display_eval) * min(1.0, 8.0 * dt)

        # Consume completed hint
        if hint_thinking and hint_result:
            hint_thinking = False
            hint_scores, hint_reason = hint_result.pop()
            sound_mgr.play_hint()

        # Consume only a move calculated for this exact game session.
        if ai_thinking and not anim_active:
            ai_move = ai_results.take_current()
            if ai_move is not None:
                ai_thinking = False
                finish_move(ai_move)

        # Auto-advance solved puzzle after 2.0s celebration
        if mode == MODE_PUZZLE and game_over and puzzle_solved_at is not None:
            if perf_counter() - puzzle_solved_at >= 2.0:
                puzzle_solved_at = None
                nxt_idx = (puzzle_idx + 1) % len(PUZZLES)
                start_puzzle(nxt_idx)

        # Launch AI thread if needed
        current = board.current_player()
        ai_should_move = (
            (mode == MODE_AVAI and (current == 1 or current == 2)) or
            (mode == MODE_HVA  and current == 2)
        )
        if (not game_over and not ai_thinking and not anim_active
                and ai_should_move and perf_counter() >= move_ready_at):
            ai_thinking = True
            b_snap = board.copy()
            generation = ai_results.generation
            threading.Thread(target=ai_thread_fn,
                             args=(_agent_for(current), b_snap, generation), daemon=True).start()

        # Hover column (human turns only, within board y bounds)
        is_human_turn = (
            (mode == MODE_HVA and current == 1) or
            (mode == MODE_HVH) or
            (mode == MODE_PUZZLE)
        )
        is_in_board_y = (55 <= my <= T.BOARD_TOP + T.BOARD_ROWS * T.CELL_SIZE + 20)
        hover_col = (
            column_from_x(mx)
            if not game_over and not anim_active and is_human_turn
               and is_in_board_y and not agent_drop.open
            else None
        )

        opponent_visible = mode in (MODE_HVA, MODE_AVAI)
        delay_visible = mode in (MODE_HVA, MODE_AVAI)
        if not opponent_visible:
            agent_drop.open = False

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                    and details_rect.collidepoint(event.pos) and not agent_drop.open):
                show_details = not show_details
                sound_mgr.play_click()
                continue

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    sound_mgr.play_click()
                    if mode == MODE_PUZZLE:
                        start_puzzle(puzzle_idx)
                    else:
                        reset()
                elif event.key in (pygame.K_SPACE, pygame.K_RETURN) and mode == MODE_PUZZLE and game_over:
                    sound_mgr.play_click()
                    puzzle_solved_at = None
                    start_puzzle((puzzle_idx + 1) % len(PUZZLES))
                elif event.key == pygame.K_p:
                    sound_mgr.play_click()
                    nxt_idx = 0 if mode != MODE_PUZZLE else (puzzle_idx + 1) % len(PUZZLES)
                    start_puzzle(nxt_idx)
                elif event.key == pygame.K_h and mode in (MODE_HVA, MODE_HVH) and not game_over \
                        and not ai_thinking and not hint_thinking:
                    sound_mgr.play_click()
                    hint_thinking = True
                    hint_result.clear()
                    threading.Thread(target=hint_thread_fn,
                                     args=(board.copy(),), daemon=True).start()
                elif event.key == pygame.K_l:
                    T.set_theme("light" if T.THEME_NAME == "dark" else "dark")
                elif event.key == pygame.K_m:
                    muted = sound_mgr.toggle_mute()
                    sound_btn.muted = muted

            elif menu_btn.clicked(event):
                sound_mgr.play_click()
                _cancel_ai_search()
                choice = show_start_menu(screen, fonts, clock)
                if choice == "quit":
                    running = False
                else:
                    mode = {"hvh": MODE_HVH, "avai": MODE_AVAI}.get(choice, MODE_HVA)
                    reset()

            elif theme_btn.clicked(event):
                sound_mgr.play_click()
                T.set_theme("light" if T.THEME_NAME == "dark" else "dark")

            elif opponent_visible and agent_drop.handle_event(event):
                sound_mgr.play_click()
                p2_agent = _init_agent(agent_drop.value)
                reset()

            # Mode toggles
            elif hva_btn.clicked(event):
                sound_mgr.play_click()
                mode = MODE_HVA
                reset()

            elif hvh_btn.clicked(event):
                sound_mgr.play_click()
                mode = MODE_HVH
                reset()

            elif avai_btn.clicked(event):
                sound_mgr.play_click()
                mode = MODE_AVAI
                reset()

            elif puzzle_btn.clicked(event):
                sound_mgr.play_click()
                nxt_idx = 0 if mode != MODE_PUZZLE else (puzzle_idx + 1) % len(PUZZLES)
                start_puzzle(nxt_idx)

            elif sound_btn.clicked(event):
                muted = sound_mgr.toggle_mute()
                sound_btn.muted = muted

            elif demo_btn.clicked(event):
                sound_mgr.play_click()
                p2_agent = _init_agent("Rookie (AB d=2)")
                p1_agent = _init_agent("Rookie (AB d=2)")
                mode = MODE_AVAI
                reset()
                demo_seed += 1
                board = demo_board(demo_seed)
                speed_slider.value = 0.8
                status = f"Demo #{demo_seed}: click Demo again for a new opening"

            elif results_btn.clicked(event):
                sound_mgr.play_click()
                show_results_screen(screen, fonts, clock)

            elif hint_btn.clicked(event):
                sound_mgr.play_click()
                if mode in (MODE_HVA, MODE_HVH) and not game_over and not ai_thinking and not anim_active:
                    if hint_thinking:
                        pass
                    elif hint_scores:
                        hint_scores = {}
                        hint_reason = ""
                    else:
                        hint_thinking = True
                        hint_result.clear()
                        threading.Thread(target=hint_thread_fn,
                                         args=(board.copy(),), daemon=True).start()

            elif new_btn.clicked(event):
                sound_mgr.play_click()
                if mode == MODE_PUZZLE:
                    start_puzzle(puzzle_idx)
                else:
                    reset()

            elif export_btn.clicked(event) and replay.active:
                sound_mgr.play_click()
                path = replay.export()
                export_msg = f"Saved: {path}"
                export_msg_until = perf_counter() + 3.5

            elif undo_btn.clicked(event):
                sound_mgr.play_click()
                if mode == MODE_PUZZLE:
                    start_puzzle(puzzle_idx)
                elif not game_over and not ai_thinking and not anim_active and mode != MODE_AVAI:
                    undo_count = 2 if mode == MODE_HVA else 1
                    for _ in range(undo_count):
                        if board.move_history:
                            board.undo()
                    hint_scores = {}
                    hint_reason = ""
                    cur = board.current_player()
                    if mode == MODE_HVH:
                        pname = "Coral" if cur == 1 else "Gold"
                        status = f"Player {cur} ({pname}) — drop your disc"
                    else:
                        status = "Your turn (Coral)"

            else:
                if delay_visible:
                    speed_slider.handle_event(event)
                # Replay slider drag
                if replay.active:
                    if replay_slider.handle_event(event):
                        replay.step = int(replay_slider.value * replay.total_moves)

                # Advance solved puzzle immediately on click anywhere
                if (event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1
                        and mode == MODE_PUZZLE
                        and game_over):
                    sound_mgr.play_click()
                    puzzle_solved_at = None
                    start_puzzle((puzzle_idx + 1) % len(PUZZLES))

                # Disc drop click
                elif (event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1
                        and not game_over and not ai_thinking and not anim_active
                        and not agent_drop.open
                        and is_human_turn
                        and is_in_board_y):
                    col = column_from_x(event.pos[0])
                    if col is not None and col in board.legal_moves():
                        finish_move(col)

        # ── Rendering ─────────────────────────────────────────────────────────
        draw_background(screen, t_anim)

        # Top bar: title on the left, per-player clocks on the right of the board column
        screen.blit(fonts["lg"].render("Connect Four Lab", True, T.TEXT), (T.BOARD_LEFT, 8))
        screen.blit(fonts["sm"].render("Strategy coach with a window into the AI's thinking",
                                       True, T.DIM_TEXT), (T.BOARD_LEFT, 40))

        hud_w, hud_h = 176, 32
        hud_x = T.BOARD_LEFT + bw - hud_w
        hud_y = 10
        pygame.draw.rect(screen, T.SURFACE, (hud_x, hud_y, hud_w, hud_h), border_radius=16)
        pygame.draw.rect(screen, T.BORDER, (hud_x, hud_y, hud_w, hud_h), width=1, border_radius=16)
        for i, (pcolor, secs) in enumerate(((P1_COLOR, player_clocks[1]), (P2_COLOR, player_clocks[2]))):
            cx0 = hud_x + 16 + i * 84
            pygame.draw.circle(screen, pcolor, (cx0, hud_y + hud_h // 2), 6)
            screen.blit(fonts["sm"].render(f"{int(secs) // 60:02d}:{int(secs) % 60:02d}", True, T.TEXT),
                        (cx0 + 14, hud_y + 7))

        # Board drawing (with ghost drop preview on human turns)
        skip = (anim.col, anim.row) if (anim_active and anim is not None) else None
        draw_board(screen, board, win_cells, skip_cell=skip,
                   ghost_col=hover_col, ghost_player=current, t_anim=t_anim)

        # Hover guide arrow above hovered column
        if hover_col is not None:
            arrow_color = P1_COLOR if current == 1 else P2_COLOR
            draw_hover_arrow(screen, hover_col, arrow_color, t_anim)

        # Drop animation
        if anim_active and anim is not None:
            anim.draw(screen)

        # Win pulse effect
        if pulse and not anim_active:
            pulse.draw(screen)

        # Confetti celebration
        if confetti:
            confetti.draw(screen)

        # Replay scrub bar
        if replay.active:
            replay_slider.draw(screen, fonts)
            replay_lbl = fonts["sm"].render(
                f"Replay Step: {replay.step}/{replay.total_moves} (drag to inspect)",
                True, T.WIN_GLOW
            )
            screen.blit(replay_lbl, (T.BOARD_LEFT, T.WIN_H - 124))

        # Hint overlay (tactical heat numbers + best move halo)
        if hint_scores:
            draw_hint_overlay(screen, fonts, hint_scores, hint_reason)

        # Strategy coach panel (right column)
        details_rect = draw_panel(
            screen, fonts, p1_agent, p2_agent, status,
            display_eval, ai_thinking, progress, mode, board, t_anim,
            puzzle_idx=puzzle_idx, show_details=show_details,
        )

        # Bottom control bar
        hva_btn.draw(screen, fonts, active=(mode == MODE_HVA))
        hvh_btn.draw(screen, fonts, active=(mode == MODE_HVH))
        avai_btn.draw(screen, fonts, active=(mode == MODE_AVAI))
        hint_btn.draw(screen, fonts, active=hint_thinking)
        demo_btn.draw(screen, fonts)
        puzzle_btn.draw(screen, fonts, active=(mode == MODE_PUZZLE))
        if delay_visible:
            speed_slider.draw(screen, fonts)
        sound_btn.draw(screen, fonts)
        results_btn.draw(screen, fonts)
        export_btn.draw(screen, fonts, active=replay.active)
        undo_btn.draw(screen, fonts)
        new_btn.draw(screen, fonts)

        # Difficulty auto-ramp notification toast
        if mode == MODE_HVA and p1_win_streak >= 1:
            ramp_name = _difficulty_levels[min(_diff_idx, len(_difficulty_levels) - 1)]
            if p1_win_streak >= 2:
                ramp_txt = fonts["sm"].render(
                    f"Win streak {p1_win_streak}! Next: {ramp_name}", True, T.WIN_GLOW
                )
                screen.blit(ramp_txt, ramp_txt.get_rect(centerx=T.BOARD_LEFT + bw // 2,
                                                         top=T.BOARD_TOP - 90))

        # Export toast
        if export_msg and perf_counter() < export_msg_until:
            toast_surf = fonts["md"].render(export_msg, True, T.WIN_GLOW)
            screen.blit(toast_surf, toast_surf.get_rect(
                centerx=T.WIN_W // 2, bottom=btn_y - 8
            ))

        # Victory banner overlay
        if game_over and not anim_active:
            if mode == MODE_PUZZLE:
                draw_puzzle_banner(screen, fonts, puzzle_idx + 1, len(PUZZLES), t_anim)
            elif not replay.active or replay.step == replay.total_moves:
                draw_banner(screen, fonts, banner_msg, t_anim)

        # Agent selector dropdown (always on top)
        menu_btn.draw(screen, fonts)
        theme_btn.label = "Light" if T.THEME_NAME == "dark" else "Dark"
        theme_btn.draw(screen, fonts)
        if opponent_visible:
            screen.blit(fonts["sm"].render("Opponent", True, T.DIM_TEXT),
                        (agent_drop.rect.left - 70, agent_drop.rect.centery - 8))
            agent_drop.draw(screen, fonts)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run()
