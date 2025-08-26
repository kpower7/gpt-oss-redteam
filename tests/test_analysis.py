import os

from gpt_oss_redteam.analysis import _wilson_ci, analyze_records, load_jsonl, render_markdown


def test_wilson_ci_edge_cases():
    # n == 0
    p, lo, hi = _wilson_ci(0, 0)
    assert p == 0.0 and lo == 0.0 and hi == 0.0

    # All failures (k=0)
    p, lo, hi = _wilson_ci(0, 10)
    assert p == 0.0
    assert lo == 0.0
    # Upper bound should be non-trivial but < ~0.35 for n=10 at 95% CI
    assert 0.20 < hi < 0.35

    # All successes (k=n)
    p, lo, hi = _wilson_ci(10, 10)
    assert p == 1.0
    # Lower bound should be > ~0.65 for n=10 at 95% CI
    assert 0.65 < lo < 0.85
    assert hi == 1.0


def test_wilson_ci_mid_sample():
    # k=50, n=100 (approximate)
    p, lo, hi = _wilson_ci(50, 100)
    assert abs(p - 0.5) < 1e-12
    # Bounds should fall roughly within 0.40..0.60 for 95% CI
    assert 0.39 < lo < 0.45
    assert 0.55 < hi < 0.61


def test_analyze_records_basic():
    records = [
        {"refusal_strict": True, "source": "A"},
        {"refusal_strict": False, "source": "A"},
        {"refusal_strict": True, "source": "B"},
    ]
    summary = analyze_records(records)

    assert summary["total_runs"] == 3
    assert summary["refusals"] == 2
    assert abs(summary["refusal_rate"] - (2 / 3)) < 1e-12
    assert isinstance(summary["ci95"], list) and len(summary["ci95"]) == 2

    per = summary["per_source"]
    assert set(per.keys()) == {"A", "B"}

    assert per["A"]["n"] == 2
    assert per["A"]["refusals"] == 1
    assert 0.0 <= per["A"]["refusal_rate"] <= 1.0
    assert isinstance(per["A"]["ci95"], list) and len(per["A"]["ci95"]) == 2

    assert per["B"]["n"] == 1
    assert per["B"]["refusals"] == 1
    assert 0.0 <= per["B"]["refusal_rate"] <= 1.0
    assert isinstance(per["B"]["ci95"], list) and len(per["B"]["ci95"]) == 2


def test_render_markdown_and_load_jsonl(tmp_path):
    # Render markdown from a computed summary
    records = [
        {"refusal_strict": True, "source": "A"},
        {"refusal_strict": False, "source": "A"},
        {"refusal_strict": True, "source": "B"},
    ]
    summary = analyze_records(records)
    md = render_markdown(summary)

    assert "# Results Summary" in md
    assert "Total runs: 3" in md
    assert "Strict refusals: 2" in md
    assert "Refusal rate:" in md
    assert "## Per high-level prompt" in md
    assert "Prompt: A" in md or "Prompt: B" in md

    # load_jsonl should yield only valid JSON objects
    p = tmp_path / "data.jsonl"
    p.write_text("{\"a\":1}\n\nINVALID\n{\"b\":2}\n", encoding="utf-8")
    items = list(load_jsonl(str(p)))
    assert items == [{"a": 1}, {"b": 2}]
