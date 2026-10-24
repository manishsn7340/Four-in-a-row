"""experiments/plot_results.py — Read CSVs from results/ and save PNG graphs.

Produces one PNG per study (4 total) in results/.
Uses matplotlib only (already in the project dependencies).

Usage
-----
    python -m experiments.plot_results
"""

from __future__ import annotations

import csv
import pathlib

RESULTS_DIR = pathlib.Path(__file__).parent.parent / "results"


def _read(name: str) -> list[dict]:
    path = RESULTS_DIR / f"latest_{name}.csv"
    if not path.exists():
        print(f"  [skip] {path.name} not found — run run_all.py first")
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _save(fig, name: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    path = RESULTS_DIR / f"{name}.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    print(f"  Saved → {path.name}")


def plot_ablation() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = _read("ablation")
    if not rows:
        return

    names     = [r["agent_a"] for r in rows]
    win_rates = [float(r["win_rate_a"]) for r in rows]
    times     = [float(r["total_time_s"]) for r in rows]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    fig.suptitle("Ablation Study — Adding features one at a time", fontsize=13, fontweight="bold")

    colors = ["#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974"]
    ax1.bar(names, win_rates, color=colors[:len(names)])
    ax1.set_ylim(0, 1.05)
    ax1.set_ylabel("Win rate vs Rookie (AB d=2)")
    ax1.set_title("Win Rate")
    ax1.tick_params(axis="x", rotation=20)
    for i, v in enumerate(win_rates):
        ax1.text(i, v + 0.02, f"{v:.0%}", ha="center", fontsize=9)

    ax2.bar(names, times, color=colors[:len(names)])
    ax2.set_ylabel("Total time for match (s)")
    ax2.set_title("Match Duration")
    ax2.tick_params(axis="x", rotation=20)

    fig.tight_layout()
    _save(fig, "ablation")
    plt.close(fig)


def plot_tournament() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = _read("tournament")
    if not rows:
        return

    # Build a win-rate matrix
    agents: list[str] = []
    for r in rows:
        for key in ("agent_a", "agent_b"):
            if r[key] not in agents:
                agents.append(r[key])

    import numpy as np
    n = len(agents)
    matrix = np.full((n, n), float("nan"))
    for r in rows:
        i = agents.index(r["agent_a"])
        j = agents.index(r["agent_b"])
        matrix[i, j] = float(r["win_rate_a"])
        matrix[j, i] = float(r["win_rate_b"])

    fig, ax = plt.subplots(figsize=(6, 5))
    fig.suptitle("Tournament — Win Rate Matrix", fontsize=13, fontweight="bold")
    im = ax.imshow(matrix, vmin=0, vmax=1, cmap="RdYlGn")
    fig.colorbar(im, ax=ax, label="Win rate (row vs col)")
    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels(agents, rotation=25, ha="right")
    ax.set_yticklabels(agents)
    for i in range(n):
        for j in range(n):
            v = matrix[i, j]
            if not (v != v):   # not NaN
                ax.text(j, i, f"{v:.0%}", ha="center", va="center",
                        color="black", fontsize=9)
    fig.tight_layout()
    _save(fig, "tournament")
    plt.close(fig)


def plot_depth_vs_time() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = _read("depth_vs_time")
    if not rows:
        return

    depths = [int(r["depth"]) for r in rows]
    times  = [float(r["avg_time_s"]) for r in rows]
    nodes  = [int(r["avg_nodes"]) for r in rows]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    fig.suptitle("AlphaBeta: Depth vs Time / Nodes", fontsize=13, fontweight="bold")

    ax1.plot(depths, times, marker="o", color="#4C72B0", linewidth=2)
    ax1.set_xlabel("Search depth"); ax1.set_ylabel("Avg time per move (s)")
    ax1.set_title("Time per Move"); ax1.set_yscale("log"); ax1.grid(True, alpha=0.3)

    ax2.plot(depths, nodes, marker="s", color="#C44E52", linewidth=2)
    ax2.set_xlabel("Search depth"); ax2.set_ylabel("Avg nodes expanded")
    ax2.set_title("Nodes Expanded"); ax2.set_yscale("log"); ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    _save(fig, "depth_vs_time")
    plt.close(fig)


def plot_weight_tuning() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = _read("weight_tuning")
    if not rows:
        return

    labels    = [r["weight_set"] for r in rows]
    win_rates = [float(r["win_rate_a"]) for r in rows]

    fig, ax = plt.subplots(figsize=(6, 4))
    fig.suptitle("Evaluation Weight Tuning vs Tactician", fontsize=13, fontweight="bold")
    colors = ["#4C72B0", "#55A868", "#C44E52"]
    bars = ax.bar(labels, win_rates, color=colors[:len(labels)])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Win rate vs Tactician (AB d=5)")
    ax.set_title("Weight Set Comparison")
    for bar, v in zip(bars, win_rates):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.02, f"{v:.0%}",
                ha="center", fontsize=10)
    fig.tight_layout()
    _save(fig, "weight_tuning")
    plt.close(fig)


def main() -> None:
    print(f"Plotting results from {RESULTS_DIR}/")
    plot_ablation()
    plot_tournament()
    plot_depth_vs_time()
    plot_weight_tuning()
    print("\nDone. Open the app and click 📊 Results to view the graphs.")


if __name__ == "__main__":
    main()
