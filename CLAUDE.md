# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
source .venv/bin/activate                      # venv already exists in repo
python -m pytest                               # all tests (pytest.ini: testpaths=tests, pythonpath=.)
python -m pytest tests/test_alphabeta.py -k name   # single file / test
python -m gui.app                              # launch the Pygame game
python -m experiments.run_all --quick          # smoke benchmarks -> results/*.csv (+ latest_*.csv)
python -m experiments.plot_results             # figures from results/ CSVs
python -m report.generate                      # build report/PROJECT_REPORT.{md,html}
```

No linter or build step is configured. Not a git repository yet.

## Project rules (from AGENTS.md — follow these)

- Work on one requested layer only; give a 3–6 line plan before coding; finish with a handoff (changed files, test command + real output, plain-language explanation, limitations, suggested commit message), then wait.
- Every agent must stay interchangeable via `choose_move(board) -> column`, and a search agent must restore the supplied board exactly before returning.
- Randomness only through an explicit `random.Random(seed)`. Constants live in `config.py`; avoid global mutable state.
- Python 3.10+, stdlib + pygame, numpy, matplotlib, pandas, pytest only. No new dependencies without approval. Never weaken tests to make them pass.
- The detailed specs referenced by AGENTS.md are in `.agents/AGENTS/{rules,rules2,rules3}` (note the leading dot — AGENTS.md says `AGENTS/`), plus `docs/overall-plan` and `docs/frontend`. Read the relevant one before changing a layer.

## Architecture

Layered build (board → Minimax → Alpha-Beta → ordering/iterative deepening → transposition table → evaluation → MCTS → GUI → experiments → report); each layer depends only on earlier ones.

- `game/board.py` — `Board`: `grid[row][col]` with **row 0 at the bottom**, 6×7 from `config.py`. Player is derived from `len(move_history)` (1 moves first). `drop`/`undo` mutate in place and incrementally maintain a Zobrist `hash` (`agents/zobrist.py`, seeded by `ZOBRIST_SEED`) — note `game` imports from `agents`.
- `agents/base.py` — `Agent` base class and `SearchStats` (nodes, cutoffs, tt_hits, depth, `column_scores`, ...). Agents fill `last_stats` and may call `on_progress(dict)`; the GUI uses these for the stats panel and hints.
- `agents/minimax.py`, `alphabeta.py` (ordering via `MOVE_ORDER`, iterative deepening with time budget raising `_SearchTimeout`, transposition table bounded by `TT_MAX_ENTRIES`), `mcts.py` (UCT, `MCTS_C`), `simple.py` (baseline/random-style opponents), `evaluation.py` (heuristic with a single `WEIGHTS` dict that experiments tune). Alpha-Beta must pick the same move as Minimax at equal depth.
- `gui/app.py` — main loop; AI move search and hint computation run in background threads (guarded by a lock and a generation counter so stale results are dropped). Other `gui/` modules are focused pieces: `board_view`, `panel`, `hint` (plain-language move explanations), `opening_book`, `puzzles`, `replay`, `animation`, `sound` (procedural), `screens`, `widgets`, `theme`. Personas (Rookie/Tactician/Grandmaster/Gambler) are configured agents.
- `experiments/` — `arena.py` plays matches between agents; `run_all.py` runs the four studies (ablation, tournament, depth-vs-time, weight tuning) and writes timestamped + `latest_*` CSVs to `results/`; `plot_results.py` renders PNGs. `report/generate.py` compiles the lab report from those results.
- `tests/` — one file per layer (`test_board`, `test_alphabeta`, `test_mcts`, `test_gui`, `test_report`, ...), including tactical `test_puzzles.py`.
