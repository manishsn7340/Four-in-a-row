# Project notes

Running notes for each build layer: what it does, what we measured, and the
problems we found. Every number below comes from a real run of the code in this
repository (October 2026, Linux, CPU only).

## Summary

| Layer | What it adds | Tests |
|:---|:---|:---:|
| v1 Board | 6×7 grid, gravity, win check, undo | 19 |
| v2 Minimax | Fixed-depth search, Random and Greedy baselines | 9 |
| v3 Alpha-Beta | Pruning, same move as Minimax | 2 |
| v4 Ordering + iterative deepening | Centre-first order, time-limited search | 4 |
| v5 Transposition table | Zobrist hashing, cached scores | 7 |
| v6 Evaluation | Threat-based heuristic with one weights dictionary | 110 |
| v7 MCTS | Monte Carlo Tree Search (UCT) | 7 |
| v8 GUI | Pygame strategy coach, hints, puzzles | 31 |
| v9 Experiments | Match runner and four studies | 7 |
| v10 Report | Report generator and setup checks | 6 |
| **Total** | | **208 passed in about 25 s** |

The v6 count is high because the symmetry check runs once per position (100
seeded positions). The v8 count combines the GUI, hint and puzzle tests.

---

## v1 — Board and rules (`game/board.py`)

- The board is a list of 6 rows × 7 columns with row 0 at the bottom, plus a
  list of the moves played. The player to move comes from the number of moves.
- `drop` and `undo` change the board in place, which lets search agents explore
  without copying the board.
- A win is checked only along the four lines through the last disc, not over
  the whole board.
- **Measured:** 1,000 seeded random games gave the same winner as a slow
  full-board scan at every move.
- Boards can be saved to and loaded from text. Loading rejects "floating"
  discs that have an empty cell below them.

## v2 — Minimax (`agents/minimax.py`, `agents/simple.py`)

- A recursive search to a fixed depth. It scores positions with the evaluation
  function and counts every position it visits.
- Baselines: `RandomAgent` (seeded random column) and `GreedyAgent` (win if
  possible, else block, else take the centre).
- **Measured:** Minimax at depth 3 beat the random player in at least 18 of 20
  seeded games and finds a forced win three moves ahead.

## v3 — Alpha-Beta (`agents/alphabeta.py`)

- The same search, but it stops exploring a branch once it is clearly worse
  than an option already found.
- **Measured:** on 50 seeded positions at depths 1 to 4, Alpha-Beta chose the
  same move and score as Minimax every time. At depth 5 it visited fewer
  positions and recorded cut-offs.

## v4 — Move ordering and iterative deepening

- **Move ordering:** columns are tried centre first (3, 2, 4, 1, 5, 0, 6), and
  the best move from the previous depth is tried first. Good moves found early
  cause more cut-offs.
- **Iterative deepening:** searches depth 1, 2, 3, ... and keeps the best move
  of the last depth it finished before the time limit. The time is checked every
  1,024 positions.
- **Measured:** on 30 positions at depth 5, ordering kept every score the same
  and lowered the total positions searched. With a 0.2 s limit the agent always
  answered within 0.3 s.

## v5 — Transposition table (`agents/zobrist.py`)

- Each (cell, player) pair gets a fixed random 64-bit number (seed 42). The
  board's hash is the XOR of the numbers for its discs and is updated on every
  `drop` and `undo`.
- The table stores score, depth, best move and bound type (exact, lower or
  upper) for up to 1,000,000 positions, and is cleared when the root player
  changes.
- **Measured:** on 30 positions at depth 5, the root score with the table equals
  the score without it, with no more positions searched. From the empty board at
  depth 8 the table had hits and searched fewer positions.

## v6 — Evaluation (`agents/evaluation.py`)

- All 69 possible lines of four cells are listed once in advance. Each line is
  scored for twos, threes, playable threes (the empty cell can be filled now),
  double threats and centre control. All weights are in one dictionary,
  `WEIGHTS`. The centre-only `BASIC_WEIGHTS` are kept for comparison.
- **Measured:** `evaluate(board, 1) == -evaluate(board, 2)` on 100 seeded
  positions. In a 40-game match (20 random 4-move openings, each played with
  both colours, depth 4) the full evaluation beat the basic one
  **26 wins to 11, with 3 draws**.
- **Problem found:** the weights dictionary contains `opp_two` and `opp_three`,
  but `evaluate` never reads them, because the opponent is already scored by the
  same rules with the sign flipped. The keys are left in, and this is noted in
  the weight-tuning study.

## v7 — MCTS (`agents/mcts.py`)

- Four steps repeated for each simulation: select a child with UCB1 (c = 1.41),
  expand one new move, play a random game to the end, and pass the result back
  up the tree. Rollouts are either fully random or "light" (win, else block,
  else random).
- **Measured:** with 800 simulations MCTS beat the random player in at least 19
  of 20 seeded games. It takes an immediate win and, with 1,500 light-rollout
  simulations, blocks an immediate loss. The same seed always gives the same
  move.

## v8 — GUI (`gui/`)

- Pygame window of 1280×800 that can be resized. The AI and the hints run in
  background threads, so the window never freezes. Each result is tagged with a
  game number, so a result from an old game is ignored.
- Features: three modes, four opponents, evaluation bar, hints with a reason,
  five puzzles, opening book, clocks, engine details panel, demo mode, adaptive difficulty, light and dark themes, sound.
- Opponents in the app: Rookie (Alpha-Beta depth 2), Tactician (depth 5),
  Grandmaster (depth 7, iterative deepening, 1.5 s limit), Gambler (MCTS, 1,000
  simulations).
- **Problems found and fixed during the rewrite:**
  - The game crashed after two wins in a row, because adaptive difficulty called
    a dropdown method that did not exist.
  - The status line and panel kept old text after a game ended.
  - Hint text used 0-based column numbers ("column 0").
  - A hint for an old position could appear after a new move.

## v9 — Experiments (`experiments/`)

### Settings used

| Setting | Value |
|:---|:---|
| Games per match | 20 (`--quick`: 10); weight tuning was rerun with 60 |
| Openings | Each pair of games starts from a seeded random 4-move opening (seed 42), played once with each agent moving first |
| Evaluation | Full `WEIGHTS` for every agent |
| Ablation | Five depth-3 agents vs Rookie (Alpha-Beta depth 2); the ID agent has a 1.0 s limit |
| Tournament | Rookie (depth 2), Tactician (depth 5), Grandmaster (depth 7, iterative deepening, 2.0 s), Gambler (MCTS, 500 simulations, seed 42) |
| Depth study | Alpha-Beta at depths 1–7, 5 runs each, from the position after moves 3 3 2 4 3 2 4 2 1 5 |
| Weight tuning | Default, aggressive and defensive weights at depth 3 vs Tactician (depth 5) |
| Full run time | About 8 minutes; the tournament takes most of it |

### Results

**Ablation** (positions searched per move, depth 3):

| Agent | Positions / move | Fewer than Minimax |
|:---|:---:|:---:|
| Minimax | 233 | – |
| Alpha-Beta | 113 | 52% |
| + move ordering | 85 | 64% |
| + iterative deepening | 96 | 59% |
| + transposition table | 78 | 67% |

Win rates were 45–55% for every row, as expected, because every row searches to
the same depth and only the speed changes. Iterative deepening costs a little
more at a fixed depth because it repeats depths 1 and 2 first.

**Tournament** (total wins over 60 games each): Grandmaster 46, Tactician 37,
Gambler 19, Rookie 16. Deeper search wins. Gambler with 500 simulations is only
about as strong as Rookie.

**Depth vs time:**

| Depth | Positions | Time per move |
|:---:|:---:|:---:|
| 1 | 7 | 0.0005 s |
| 3 | 237 | 0.015 s |
| 5 | 4,745 | 0.29 s |
| 7 | 77,311 | 4.55 s |

Each extra level multiplied the work by about 4.7 on average (a tree without
pruning grows by 7). Going from an odd depth to the next even depth costs much
less than going from even to odd, a known Alpha-Beta effect.

**Weight tuning** (wins out of 60 vs Tactician): defensive 14, default 13,
aggressive 12, with 2–3 draws each. The three weight sets play equally well.
An earlier 20-game run had defensive ahead (6, 4, 3), but with 60 games the gap
disappeared, so that lead was chance. At this depth the weights matter far less
than how deep the agent searches.

### Problem found

- Search agents always choose the same move in the same position. Matches
  started from an empty board were therefore the same two games repeated, and
  the win rates meant nothing. Fixed with the seeded random openings described
  above.
- The first version of the ablation used the basic evaluation for Minimax and
  the full one for Alpha-Beta, which made the comparison unfair. All agents now
  use the same `WEIGHTS`.

## v10 — Report and presentation

- `python -m report.generate` runs the test suite first and only writes
  `report/PROJECT_REPORT.md` and `.html` if every test passes. Tables and
  summary sentences are built from the CSV files, so the report always matches
  the latest run.
- Talk and demo scripts are in `scripts/`.
- Demo safety: the in-app **Demo** button starts AI vs AI from a seeded opening
  with fast agents, so no separate command-line demo option is needed.
