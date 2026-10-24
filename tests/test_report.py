"""Tests for report generation and its HTML renderer."""

from __future__ import annotations

from report import generate as report_generator


def test_markdown_renderer_creates_semantic_report_elements() -> None:
    """Render report Markdown as HTML instead of displaying it literally."""
    page = report_generator._markdown_to_html(
        """# Example Report

| Agent | Score |
|:---|:---:|
| **Rookie** | 42 |

![Example graph](../results/example.png)

> **Insight**: This is a quote.

- First point
- Second point

```bash
python -m pytest -q
```
""",
    )

    assert "<h1>Example Report</h1>" in page
    assert "<table>" in page
    assert "<th>Agent</th>" in page
    assert "<strong>Rookie</strong>" in page
    assert '<img src="../results/example.png" alt="Example graph">' in page
    assert "<blockquote><p><strong>Insight</strong>: This is a quote.</p></blockquote>" in page
    assert "<ul><li>First point</li><li>Second point</li></ul>" in page
    assert "<pre><code>python -m pytest -q</code></pre>" in page
    assert "| Agent | Score |" not in page


def test_generate_report_uses_current_facts_and_writes_to_requested_directory(
    tmp_path, monkeypatch
) -> None:
    """Generate an accurate report without modifying repository report files."""
    results_dir = tmp_path / "results"
    report_dir = tmp_path / "report"
    results_dir.mkdir()
    (results_dir / "latest_ablation.csv").write_text(
        "agent_a,n_games,wins_a,win_rate_a,draw_rate,total_time_s\n"
        "AB-d3,3,2,0.6667,0.0,1.25\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(report_generator, "RESULTS_DIR", results_dir)
    monkeypatch.setattr(report_generator, "REPORT_DIR", report_dir)

    md_path, html_path = report_generator.generate_report("7 passed in 0.01s")

    assert md_path.exists()
    assert html_path.exists()
    markdown = md_path.read_text(encoding="utf-8")
    page = html_path.read_text(encoding="utf-8")

    assert md_path.stat().st_size > 500
    assert html_path.stat().st_size > 500
    assert "Python list-of-lists" in markdown
    assert "bitboards" not in markdown
    assert "7 passed in 0.01s" in markdown
    assert "<table>" in page
    assert '<img src="../results/ablation.png" alt="Ablation Study">' in page


def test_extract_test_summary_uses_pytest_result_line() -> None:
    """Keep the report's verification line tied to real pytest-style output."""
    output = "...\n200 passed in 62.17s (0:01:02)\n"

    assert report_generator._extract_test_summary(output) == "200 passed in 62.17s (0:01:02)"
