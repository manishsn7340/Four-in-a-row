# Four in a Row AI

A university AI project that develops a Connect Four strategy coach in small,
tested layers. It will include Minimax, Alpha-Beta search, MCTS, a Pygame
interface, and reproducible experiments.

## Current status

- **Game Engine & Rules**: Bitboard/array-based board representation, victory detection, and move undo/redo.
- **Search Agents**:
  - Minimax with depth cutoff and heuristic evaluation
  - Alpha-Beta Pruning with move ordering
  - Iterative Deepening with time budgets
  - Zobrist Hashing & Transposition Table
  - Monte Carlo Tree Search (MCTS / UCT)
- **Frontend / Strategy Coach (`gui/app.py`)**:
  - **Modes**: Human vs AI (`Human vs AI`), Pass & Play 2-Player (`2-Player`), and AI vs AI (`AI vs AI`).
  - **Strategy Coach**: Real-time evaluation bar, one-click tactical hints with plain-language explanations.
  - **Visuals & Avatars**: Procedural geometric avatars (Rookie, Tactician, Grandmaster, Gambler), deep-space nebula gradient, twinkling starfield, physical drop bounce, laser win pulse, and confetti celebration.
  - **Replay System**: Post-game timeline slider and Left/Right arrow scrubbing to replay any move.
  - **Game Exporter**: One-click export to timestamped text record in `results/`.
  - **Chess Clock**: Per-player thinking clocks in top HUD.
  - **Opening Book**: Connect Four game-theoretic opening lines (Allis 1988) with instant opening book moves.
  - **Adaptive Difficulty**: Auto-ramps AI level upon consecutive player win streaks.
  - **Procedural Audio**: Gentle physical disc drop sounds, hint chimes, and win fanfares (toggle with 'M' or mute button).
- **Experiments**: Arena benchmark runner and automated figure generation in `experiments/`.

## Requirements

- Python 3.10 or later
- Pygame, NumPy, Matplotlib, Pandas, Pytest

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Launch the Game

```bash
python -m gui.app
```

### In-Game Controls
- **Click column**: Drop disc (when it's your turn)
- **H / Click '💡 Hint'**: Reveal tactical move scores and engine reasoning
- **P / Click '🧩 Puzzles'**: Cycle through 5 interactive tactical challenges
- **R / Click '▶ New Game'**: Rematch / reset board
- **M / Click '🔊'**: Toggle procedural sound effects
- **Click '↩ Undo'**: Take back move (1 move in 2-player, 2 moves in vs AI)
- **Click '🎬 Demo'**: Launch presentation demo mode with pre-set midgame
- **Click '📊 Results'**: Browse experiment graphs directly inside the app
- **Click '💾 Export'**: Export finished game record to `results/`
- **Left / Right Arrows & Bottom Slider**: Scrub through replay moves after game ends

## Run Experiments & Tests

```bash
# Run all unit tests
python -m pytest

# Run fast smoke benchmark experiments
python -m experiments.run_all --quick

# Compile comprehensive lab report (Markdown + HTML)
python -m report.generate
```


