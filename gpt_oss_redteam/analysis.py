import json
import math
from typing import Dict, Iterable, Tuple


def _wilson_ci(k: int, n: int, z: float = 1.96) -> Tuple[float, float, float]:
    """Wilson score interval for a binomial proportion.

    Returns (p_hat, lower, upper).
    """
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return p, max(0.0, center - margin), min(1.0, center + margin)


def analyze_records(records: Iterable[Dict]) -> Dict:
    total = 0
    refusals = 0

    per_source = {}

    for rec in records:
        total += 1
        if rec.get("refusal_strict"):
            refusals += 1
        src = rec.get("source", "")
        d = per_source.setdefault(src, {"n": 0, "refusals": 0})
        d["n"] += 1
        d["refusals"] += 1 if rec.get("refusal_strict") else 0

    p, lo, hi = _wilson_ci(refusals, total)

    per_source_stats = {}
    for src, d in per_source.items():
        pp, l, h = _wilson_ci(d["refusals"], d["n"])
        per_source_stats[src] = {
            "n": d["n"],
            "refusals": d["refusals"],
            "refusal_rate": pp,
            "ci95": [l, h],
        }

    return {
        "total_runs": total,
        "refusals": refusals,
        "refusal_rate": p,
        "ci95": [lo, hi],
        "per_source": per_source_stats,
    }


def load_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def render_markdown(summary: Dict) -> str:
    p = summary["refusal_rate"]
    lo, hi = summary["ci95"]
    lines = []
    lines.append("# Results Summary")
    lines.append("")
    lines.append(f"- Total runs: {summary['total_runs']}")
    lines.append(f"- Strict refusals: {summary['refusals']}")
    lines.append(f"- Refusal rate: {p:.3f} (95% CI: [{lo:.3f}, {hi:.3f}])")
    lines.append("")
    lines.append("## Per high-level prompt")
    for src, d in summary.get("per_source", {}).items():
        lines.append(
            f"- n={d['n']}, refusals={d['refusals']}, rate={d['refusal_rate']:.3f} "
            f"(95% CI: [{d['ci95'][0]:.3f}, {d['ci95'][1]:.3f}])\n  Prompt: {src}"
        )
    return "\n".join(lines)
