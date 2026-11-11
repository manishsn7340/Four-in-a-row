"""Draw one PNG per experiment from the CSVs in results/.

Usage:  python -m experiments.plot_results
"""

from __future__ import annotations

import csv
import pathlib

import matplotlib

matplotlib.use("Agg")  # draw to files, no window
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

RESULTS_DIR = pathlib.Path(__file__).parent.parent / "results"
COLORS = ["#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974"]


def read(name: str) -> list[dict]:
    path = RESULTS_DIR / f"latest_{name}.csv"
    if not path.exists():
        print(f"  skipping {name}: {path.name} not found (run experiments.run_all first)")
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / f"{name}.png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved results/{name}.png")


def bars(ax, labels: list[str], values: list[float], title: str, ylabel: str, percent: bool = False) -> None:
    ax.bar(labels, values, color=COLORS[:len(labels)])
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=20)
    if percent:
        ax.set_ylim(0, 1.05)
        for i, v in enumerate(values):
            ax.text(i, v + 0.02, f"{v:.0%}", ha="center", fontsize=9)


def plot_ablation() -> None:
    rows = read("ablation")
    if not rows:
        return
    names = [r["agent_a"] for r in rows]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle("Ablation study: adding one feature at a time (depth 3)", fontsize=13, fontweight="bold")
    bars(axes[0], names, [float(r.get("avg_nodes_a", 0)) for r in rows], "Positions searched per move", "nodes")
    bars(axes[1], names, [float(r["total_time_s"]) for r in rows], "Total match time", "seconds")
    bars(axes[2], names, [float(r["win_rate_a"]) for r in rows], "Win rate vs Rookie (AB d=2)", "win rate", True)
    save(fig, "ablation")


def plot_tournament() -> None:
    rows = read("tournament")
    if not rows:
        return
    agents = list(dict.fromkeys(name for r in rows for name in (r["agent_a"], r["agent_b"])))
    matrix = np.full((len(agents), len(agents)), np.nan)
    for r in rows:
        i, j = agents.index(r["agent_a"]), agents.index(r["agent_b"])
        matrix[i, j], matrix[j, i] = float(r["win_rate_a"]), float(r["win_rate_b"])
    fig, ax = plt.subplots(figsize=(6, 5))
    fig.suptitle("Tournament: win rate of row against column", fontsize=13, fontweight="bold")
    fig.colorbar(ax.imshow(matrix, vmin=0, vmax=1, cmap="RdYlGn"), ax=ax, label="win rate")
    ax.set_xticks(range(len(agents)), agents, rotation=25, ha="right")
    ax.set_yticks(range(len(agents)), agents)
    for (i, j), v in np.ndenumerate(matrix):
        if not np.isnan(v):
            ax.text(j, i, f"{v:.0%}", ha="center", va="center", fontsize=9)
    save(fig, "tournament")


def plot_depth_vs_time() -> None:
    rows = read("depth_vs_time")
    if not rows:
        return
    depths = [int(r["depth"]) for r in rows]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    fig.suptitle("Alpha-Beta: cost of searching deeper", fontsize=13, fontweight="bold")
    for ax, key, title, color in ((ax1, "avg_time_s", "Seconds per move", "#4C72B0"),
                                  (ax2, "avg_nodes", "Positions searched", "#C44E52")):
        ax.plot(depths, [float(r[key]) for r in rows], marker="o", color=color, linewidth=2)
        ax.set(xlabel="search depth", title=title, yscale="log")
        ax.grid(True, alpha=0.3)
    save(fig, "depth_vs_time")


def plot_weight_tuning() -> None:
    rows = read("weight_tuning")
    if not rows:
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    fig.suptitle("Evaluation weights vs Tactician", fontsize=13, fontweight="bold")
    bars(ax, [r["weight_set"] for r in rows], [float(r["win_rate_a"]) for r in rows],
         "Win rate by weight set", "win rate vs Tactician (AB d=5)", True)
    save(fig, "weight_tuning")


def main() -> None:
    print(f"Plotting results from {RESULTS_DIR}/")
    for plot in (plot_ablation, plot_tournament, plot_depth_vs_time, plot_weight_tuning):
        plot()


if __name__ == "__main__":
    main()
