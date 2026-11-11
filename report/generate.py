"""Build report/PROJECT_REPORT.md and .html from the experiment CSVs in results/.

Usage:  python -m report.generate   (runs the test suite first and records its result)
"""

from __future__ import annotations

import csv
import datetime
import html
import math
import pathlib
import re
import subprocess
import sys

RESULTS_DIR = pathlib.Path("results")
REPORT_DIR = pathlib.Path("report")


def _read_csv(name: str) -> list[dict[str, str]]:
    path = RESULTS_DIR / name
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _extract_test_summary(output: str) -> str:
    """The last pytest line that reports passed tests, e.g. '200 passed in 62.17s'."""
    for line in reversed(output.splitlines()):
        if re.search(r"\b\d+ passed\b", line):
            return line.strip()
    raise RuntimeError("Pytest finished without a 'passed' summary line.")


def _run_test_suite() -> str:
    root = pathlib.Path(__file__).resolve().parent.parent
    done = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=root, capture_output=True, text=True)
    output = done.stdout + done.stderr
    if done.returncode != 0:
        raise RuntimeError(f"Not generating a report because the tests failed:\n{output}")
    return _extract_test_summary(output)


def _pct(row: dict, key: str) -> str:
    return f"{float(row.get(key, 0)) * 100:.0f}%"


def _ablation(rows: list[dict]) -> list[str]:
    lines = ["| Agent | Positions searched / move | Win rate | Wins / games | Draw rate | Match time |",
             "|:---|:---:|:---:|:---:|:---:|:---:|"]
    for r in rows:
        lines.append(f"| **{r['agent_a']}** | {int(float(r.get('avg_nodes_a', 0))):,} | {_pct(r, 'win_rate_a')} "
                     f"| {r['wins_a']}/{r['n_games']} | {_pct(r, 'draw_rate')} | {float(r['total_time_s']):.2f}s |")
    nodes = {r["agent_a"]: float(r.get("avg_nodes_a") or 0) for r in rows}
    if nodes.get("Minimax-d3") and nodes.get("AB-d3"):
        saved = 1 - nodes["AB-d3"] / nodes["Minimax-d3"]
        lines.append(f"\n> **Result**: at the same depth, Alpha-Beta searched {saved:.0%} fewer positions "
                     "per move than Minimax.")
    return lines


def _tournament(rows: list[dict]) -> list[str]:
    lines = ["| Match | Win % (first named) | Win % (second named) | Draw % | Match time |",
             "|:---|:---:|:---:|:---:|:---:|"]
    wins: dict[str, int] = {}
    for r in rows:
        lines.append(f"| **{r['agent_a']}** vs **{r['agent_b']}** | {_pct(r, 'win_rate_a')} | "
                     f"{_pct(r, 'win_rate_b')} | {_pct(r, 'draw_rate')} | {float(r['total_time_s']):.1f}s |")
        wins[r["agent_a"]] = wins.get(r["agent_a"], 0) + int(r["wins_a"])
        wins[r["agent_b"]] = wins.get(r["agent_b"], 0) + int(r["wins_b"])
    ranking = ", ".join(f"{name} ({n})" for name, n in sorted(wins.items(), key=lambda kv: -kv[1]))
    return lines + [f"\n> **Ranking by total wins**: {ranking}."]


def _depth(rows: list[dict]) -> list[str]:
    lines = ["| Depth | Positions searched | Time per move | Growth vs previous depth |",
             "|:---:|:---:|:---:|:---:|"]
    nodes = [int(r["avg_nodes"]) for r in rows]
    for i, r in enumerate(rows):
        growth = f"{nodes[i] / nodes[i - 1]:.2f}x" if i and nodes[i - 1] else "-"
        lines.append(f"| {r['depth']} | {nodes[i]:,} | {float(r['avg_time_s']):.4f}s | {growth} |")
    if len(nodes) > 1 and nodes[0]:
        factor = math.exp(math.log(nodes[-1] / nodes[0]) / (len(nodes) - 1))
        lines.append(f"\n> **Result**: each extra level of depth multiplied the work by about {factor:.1f} "
                     f"on average (a full tree would grow by 7 per level).")
    return lines


def _weights(rows: list[dict]) -> list[str]:
    lines = ["| Weight set | Win rate | Draw rate | Match time |", "|:---|:---:|:---:|:---:|"]
    for r in rows:
        lines.append(f"| **{r.get('weight_set', r['agent_a'])}** | {_pct(r, 'win_rate_a')} | "
                     f"{_pct(r, 'draw_rate')} | {float(r['total_time_s']):.1f}s |")
    return lines


def generate_report(test_summary: str | None = None) -> tuple[pathlib.Path, pathlib.Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md = [
        "# Four in a Row AI — Strategy Coach and Benchmark Report\n",
        f"**Date:** {datetime.date.today():%B %d, %Y}  |  **Course:** Artificial Intelligence Lab\n",
        "---\n",
        "## 1. System overview\n",
        "- **Board**: a 6×7 grid stored as a Python list-of-lists with a move history and an incremental "
        "Zobrist hash. A win is checked only along the four lines through the last move.",
        "- **Search**: Minimax, Alpha-Beta with centre-first move ordering, iterative deepening with a time "
        "limit, and a transposition table.",
        "- **MCTS**: Monte Carlo Tree Search with the UCB1 selection rule (c = 1.41).",
        "- **GUI**: a Pygame strategy coach with an evaluation bar, hints with a one-line reason, an opening "
        "book, per-player clocks, and puzzles.\n",
    ]
    studies = [
        ("2. Study 1 — Ablation", "Each row adds one feature; all play at depth 3 against Rookie (Alpha-Beta depth 2).",
         "latest_ablation.csv", _ablation, "Ablation Study", "ablation.png"),
        ("3. Study 2 — Tournament", "Every pair of agents plays. Each pair of games starts from a random 4-move "
         "opening, played once with each agent moving first.",
         "latest_tournament.csv", _tournament, "Tournament Results", "tournament.png"),
        ("4. Study 3 — Depth vs time", "Alpha-Beta from one fixed mid-game position at depths 1 to 7.",
         "latest_depth_vs_time.csv", _depth, "Depth vs Time", "depth_vs_time.png"),
        ("5. Study 4 — Evaluation weights", "Three weight sets at depth 3 against Tactician (depth 5).",
         "latest_weight_tuning.csv", _weights, "Weight Tuning", "weight_tuning.png"),
    ]
    for title, intro, csv_name, table, alt, image in studies:
        rows = _read_csv(csv_name)
        md += [f"## {title}\n", intro + "\n"]
        md += table(rows) if rows else [f"*No data yet: run `python -m experiments.run_all` to create {csv_name}.*"]
        md.append(f"\n![{alt}](../results/{image})\n")
    md += ["## 6. Tests\n", "```bash", "$ python -m pytest -q",
           test_summary or "(run the command above and paste the summary line here)", "```\n"]

    text = "\n".join(md)
    md_path, html_path = REPORT_DIR / "PROJECT_REPORT.md", REPORT_DIR / "PROJECT_REPORT.html"
    md_path.write_text(text, encoding="utf-8")
    html_path.write_text(_markdown_to_html(text), encoding="utf-8")
    return md_path, html_path


# ── A small Markdown-to-HTML converter for exactly the syntax used above ──────

def _inline(text: str) -> str:
    """Escape HTML, then turn `code`, ![alt](src), **bold** and *italic* into tags."""
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"!\[([^]]*)\]\(([^)\s]+)\)", r'<img src="\2" alt="\1">', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _render_markdown(text: str) -> str:
    lines, out, i = text.splitlines(), [], 0

    def take(predicate) -> list[str]:
        """Consume consecutive lines matching `predicate` and return them stripped."""
        nonlocal i
        block = []
        while i < len(lines) and predicate(lines[i].strip()):
            block.append(lines[i].strip())
            i += 1
        return block

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
        elif m := re.match(r"(#{1,6})\s+(.*)", line):
            out.append(f"<h{len(m[1])}>{_inline(m[2])}</h{len(m[1])}>")
            i += 1
        elif line == "---":
            out.append("<hr>")
            i += 1
        elif line.startswith("```"):
            i += 1
            code = take(lambda s: not s.startswith("```"))
            i += 1
            out.append(f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>")
        elif line.startswith("|") and i + 1 < len(lines) and re.fullmatch(r"[|:\- ]+", lines[i + 1].strip()):
            header = _cells(line)
            i += 2  # skip the header and the |:---| separator row
            rows = take(lambda s: s.startswith("|"))
            out.append("<table><thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in header) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in _cells(r)) + "</tr>" for r in rows)
                       + "</tbody></table>")
        elif line.startswith(">"):
            quote = " ".join(s[1:].strip() for s in take(lambda s: s.startswith(">")))
            out.append(f"<blockquote><p>{_inline(quote)}</p></blockquote>")
        elif line.startswith("- "):
            items = take(lambda s: s.startswith("- "))
            out.append("<ul>" + "".join(f"<li>{_inline(s[2:])}</li>" for s in items) + "</ul>")
        elif re.match(r"\d+\.\s", line):
            items = take(lambda s: re.match(r"\d+\.\s", s))
            out.append("<ol>" + "".join(f"<li>{_inline(s.split(' ', 1)[1])}</li>" for s in items) + "</ol>")
        elif re.fullmatch(r"!\[[^]]*\]\([^)\s]+\)", line):
            out.append(f"<figure>{_inline(line)}</figure>")
            i += 1
        else:
            out.append(f"<p>{_inline(line)}</p>")
            i += 1
    return "\n".join(out)


CSS = """
body { font-family: system-ui, sans-serif; line-height: 1.6; color: #1e293b; background: #f8fafc; padding: 40px 20px; }
main { max-width: 900px; margin: 0 auto; background: #fff; padding: 48px; border-radius: 12px; }
h1 { border-bottom: 2px solid #3b82f6; padding-bottom: 12px; }
h2 { color: #1e3a8a; margin-top: 36px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }
table { width: 100%; border-collapse: collapse; margin: 20px 0; }
th, td { padding: 10px 14px; border: 1px solid #e2e8f0; text-align: left; }
th { background: #f1f5f9; }
blockquote { background: #eff6ff; border-left: 4px solid #3b82f6; margin: 18px 0; padding: 12px 18px; }
img { max-width: 100%; border-radius: 8px; }
code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; }
pre { background: #0f172a; color: #e2e8f0; padding: 16px; border-radius: 8px; overflow-x: auto; }
pre code { background: none; }
"""


def _markdown_to_html(text: str) -> str:
    return (f'<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
            f"<title>Four in a Row AI — Lab Report</title>\n<style>{CSS}</style>\n</head>\n"
            f"<body>\n<main>\n{_render_markdown(text)}\n</main>\n</body>\n</html>\n")


def main() -> None:
    print("Running the test suite first...")
    summary = _run_test_suite()
    print(f"  {summary}")
    md_path, html_path = generate_report(summary)
    print(f"Wrote {md_path} and {html_path}")


if __name__ == "__main__":
    main()
