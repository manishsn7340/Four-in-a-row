# Four in a Row AI — Strategy Coach and Benchmark Report

**Date:** October 24, 2026  |  **Course:** Artificial Intelligence Lab

---

## 1. System overview

- **Board**: a 6×7 grid stored as a Python list-of-lists with a move history and an incremental Zobrist hash. A win is checked only along the four lines through the last move.
- **Search**: Minimax, Alpha-Beta with centre-first move ordering, iterative deepening with a time limit, and a transposition table.
- **MCTS**: Monte Carlo Tree Search with the UCB1 selection rule (c = 1.41).
- **GUI**: a Pygame strategy coach with an evaluation bar, hints with a one-line reason, an opening book, per-player clocks, puzzles and a replay slider.

## 2. Study 1 — Ablation

Each row adds one feature; all play at depth 3 against Rookie (Alpha-Beta depth 2).

| Agent | Positions searched / move | Win rate | Wins / games | Draw rate | Match time |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Minimax-d3** | 233 | 50% | 10/20 | 0% | 4.10s |
| **AB-d3** | 113 | 50% | 10/20 | 0% | 2.04s |
| **AB-d3+ord** | 85 | 45% | 9/20 | 0% | 1.60s |
| **AB-d3+ID** | 96 | 55% | 11/20 | 0% | 1.81s |
| **AB-d3+TT** | 78 | 45% | 9/20 | 0% | 1.36s |

> **Result**: at the same depth, Alpha-Beta searched 52% fewer positions per move than Minimax.

![Ablation Study](../results/ablation.png)

## 3. Study 2 — Tournament

Every pair of agents plays. Each pair of games starts from a random 4-move opening, played once with each agent moving first.

| Match | Win % (first named) | Win % (second named) | Draw % | Match time |
|:---|:---:|:---:|:---:|:---:|
| **Rookie** vs **Tactician** | 15% | 85% | 0% | 10.8s |
| **Rookie** vs **Grandmaster** | 20% | 80% | 0% | 107.0s |
| **Rookie** vs **Gambler** | 45% | 50% | 5% | 9.7s |
| **Tactician** vs **Grandmaster** | 15% | 80% | 5% | 119.4s |
| **Tactician** vs **Gambler** | 85% | 15% | 0% | 19.7s |
| **Grandmaster** vs **Gambler** | 70% | 30% | 0% | 112.2s |

> **Ranking by total wins**: Grandmaster (46), Tactician (37), Gambler (19), Rookie (16).

![Tournament Results](../results/tournament.png)

## 4. Study 3 — Depth vs time

Alpha-Beta from one fixed mid-game position at depths 1 to 7.

| Depth | Positions searched | Time per move | Growth vs previous depth |
|:---:|:---:|:---:|:---:|
| 1 | 7 | 0.0005s | - |
| 2 | 27 | 0.0017s | 3.86x |
| 3 | 237 | 0.0146s | 8.78x |
| 4 | 642 | 0.0352s | 2.71x |
| 5 | 4,745 | 0.2863s | 7.39x |
| 6 | 11,207 | 0.5706s | 2.36x |
| 7 | 77,311 | 4.5508s | 6.90x |

> **Result**: each extra level of depth multiplied the work by about 4.7 on average (a full tree would grow by 7 per level).

![Depth vs Time](../results/depth_vs_time.png)

## 5. Study 4 — Evaluation weights

Three weight sets at depth 3 against Tactician (depth 5).

| Weight set | Win rate | Draw rate | Match time |
|:---|:---:|:---:|:---:|
| **default** | 22% | 5% | 22.2s |
| **aggressive** | 20% | 5% | 22.9s |
| **defensive** | 23% | 3% | 21.2s |

![Weight Tuning](../results/weight_tuning.png)

## 6. Tests

```bash
$ python -m pytest -q
202 passed in 14.22s
```
