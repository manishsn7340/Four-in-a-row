# Four in a Row AI

A Connect Four strategy coach built for the Artificial Intelligence Lab. It
implements and compares classic game-playing algorithms (Minimax, Alpha-Beta
pruning with its standard optimisations, and Monte Carlo Tree Search) and puts
them inside a playable Pygame application that explains its reasoning.

## Features

**Search algorithms** (`agents/`)

| Agent | Technique |
|:---|:---|
| Minimax | Fixed-depth game-tree search with a heuristic evaluation |
| Alpha-Beta | Minimax with pruning; returns the same move as Minimax at equal depth |
| + Move ordering | Centre columns searched first, so more branches are pruned |
| + Iterative deepening | Searches depth 1, 2, 3, ... until a time limit runs out |
| + Transposition table | Zobrist hashing so repeated positions are not searched twice |
| MCTS | Monte Carlo Tree Search with the UCB1 (UCT) selection rule |

Every agent shares one interface, `choose_move(board) -> column`, so any agent
can play against any other. All randomness uses an explicit seed, so results
are reproducible.

**Strategy coach** (`gui/`)

- Three modes: you vs the computer, two players on one screen, and AI vs AI.
- Four opponents: Rookie (Alpha-Beta, depth 2), Tactician (depth 5),
  Grandmaster (depth 7 with iterative deepening) and Gambler (MCTS).
- An evaluation bar that shows who is ahead, in plain words.
- Hints that score every column and give a one-line reason ("Blocks the
  opponent's threat").
- Five tactics puzzles, an opening book, and per-player clocks.
- An engine panel showing positions searched, pruning rate and search depth.
- A demo mode with varied openings, adaptive difficulty after two wins in a row,
  light and dark themes, and sound effects.

**Experiments** (`experiments/`, `report/`)

Four reproducible studies, saved as CSV files and graphs in `results/` and
compiled into a lab report in `report/`:

1. **Ablation**: how much each Alpha-Beta optimisation reduces the search.
2. **Tournament**: every agent plays every other agent.
3. **Depth vs time**: how search cost grows with depth.
4. **Weight tuning**: three evaluation weight sets compared.

## Key results

From the latest full run (20 games per match):

- At depth 3, Alpha-Beta searched **52% fewer positions** than Minimax, and
  **67% fewer** with move ordering and the transposition table.
- Each extra level of depth multiplied the work by about **4.7**, compared with
  7 for a search without pruning.
- Tournament ranking by total wins: Grandmaster, Tactician, Gambler, Rookie.

See `report/PROJECT_REPORT.html` for the full tables and graphs.

## Getting started

Requires Python 3.10 or later.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m gui.app
```

## Controls

| Action | Mouse | Key |
|:---|:---|:---|
| Drop a disc | Click a column | |
| Show a hint | Hint | H |
| Start or skip a puzzle | Puzzles | P |
| Next puzzle after solving | | Space / Enter |
| New game | New Game | R |
| Take back a move | Undo | |
| Watch a demo game | Demo | |
| View experiment graphs | Results | |
| Switch light / dark theme | Theme button | L |
| Sound on / off | Speaker button | M |
| Back to the start menu | Menu | |
| Quit | | Esc |

## Tests and experiments

```bash
python -m pytest                          # 208 tests, about 25 seconds
python -m experiments.run_all             # all four studies (about 8 minutes)
python -m experiments.run_all --quick     # 10 games per match instead of 20
python -m experiments.plot_results        # draw the graphs
python -m report.generate                 # runs the tests, then writes the report
```

## Project structure

```
game/         Board, rules, win detection, undo
agents/       Minimax, Alpha-Beta, transposition table, MCTS, evaluation
gui/          Pygame strategy coach
experiments/  Match runner, the four studies, graphs
report/       Lab report generator
tests/        Unit tests for every layer
results/      Experiment CSV files and graphs
config.py     Board size, search and display constants
```

## Design notes

- The board is a 6×7 grid (row 0 at the bottom) with a move history. A win is
  checked only along the four lines through the last move.
- Search agents play moves on the real board and undo them, so the board is
  always restored exactly before an agent returns its move.
- Alpha-Beta agents always pick the same move in the same position, so every
  pair of experiment games starts from a different seeded random opening,
  played once with each agent moving first.
