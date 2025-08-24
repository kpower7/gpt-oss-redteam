import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# App-wide style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('husl')

RESULTS_DIR = Path("results")
COMPARISON_FILE = RESULTS_DIR / "compare" / "comparison_plus.json"

# Helpful default labels for known example runs
DEFAULT_RUN_LABELS = {
    "20250821_031505": "Null System",
    "20250821_121206": "Tool-Primed System",
    "20250821_222606": "Overtly Malicious",
}


@st.cache_data(ttl=300)
def load_comparison(path: Path) -> Dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=300)
def discover_detailed_runs(results_dir: Path) -> Dict[str, Dict]:
    """Return {run_id: analysis_plus_json} for each run folder containing analysis_plus.json."""
    data = {}
    if not results_dir.exists():
        return data
    for run_dir in sorted(results_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        run_id = run_dir.name
        analysis_path = run_dir / "analysis_plus.json"
        if analysis_path.exists():
            try:
                with open(analysis_path, "r", encoding="utf-8") as f:
                    data[run_id] = json.load(f)
            except Exception:
                # Skip corrupt files
                continue
    return data


def make_run_labels(run_ids: List[str]) -> Dict[str, str]:
    labels = {}
    for rid in run_ids:
        labels[rid] = DEFAULT_RUN_LABELS.get(rid, rid)
    return labels


def get_category_union(detailed_by_run: Dict[str, Dict]) -> List[str]:
    cats = set()
    for rid, d in detailed_by_run.items():
        for c in d.get("per_category", {}).keys():
            cats.add(c)
    return sorted(cats)


def fig_overall_refusal(comparison: Dict, run_ids: List[str], run_labels: Dict[str, str]):
    fig, ax = plt.subplots(figsize=(5, 3))
    xs = []
    ys = []
    yerr = [[], []]

    for rid in run_ids:
        stats = comparison.get(rid, {}).get("overall")
        if not stats:
            continue
        xs.append(run_labels.get(rid, rid))
        rate = stats.get("refusal_rate", 0) * 100
        lo, hi = stats.get("ci95", [None, None])
        ys.append(rate)
        if lo is not None and hi is not None:
            yerr[0].append(rate - lo * 100)
            yerr[1].append(hi * 100 - rate)
        else:
            yerr[0].append(0)
            yerr[1].append(0)

    bars = ax.bar(xs, ys, color=["#2E86AB" for _ in xs], alpha=0.85, edgecolor='black')
    ax.errorbar(xs, ys, yerr=yerr, fmt='none', color='black', capsize=5, capthick=1.5)

    for bar, rate in zip(bars, ys):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.8,
                f"{rate:.1f}%", ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_ylabel('Overall Refusal Rate (%)', fontsize=10, fontweight='bold')
    ax.set_xlabel('Runs / Conditions', fontsize=10, fontweight='bold')
    ax.set_title('Overall Refusal Rates (95% CI)', fontsize=12, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig


def fig_plain_vs_tool(comparison: Dict, run_ids: List[str], run_labels: Dict[str, str]):
    fig, ax = plt.subplots(figsize=(7, 4.2))
    x = np.arange(len(run_ids))
    width = 0.38

    plain_rates, tool_rates = [], []
    plain_err, tool_err = ([], []), ([], [])

    labels = []
    for rid in run_ids:
        data_plain = comparison.get(rid, {}).get("plain")
        data_tool = comparison.get(rid, {}).get("tool")
        if not data_plain or not data_tool:
            continue
        labels.append(run_labels.get(rid, rid))
        pr = data_plain["refusal_rate"] * 100
        tr = data_tool["refusal_rate"] * 100
        plain_rates.append(pr)
        tool_rates.append(tr)
        plo, phi = data_plain.get("ci95", [pr/100, pr/100])
        tlo, thi = data_tool.get("ci95", [tr/100, tr/100])
        plain_err[0].append(pr - plo * 100)
        plain_err[1].append(phi * 100 - pr)
        tool_err[0].append(tr - tlo * 100)
        tool_err[1].append(thi * 100 - tr)

    x = np.arange(len(labels))
    bars1 = ax.bar(x - width/2, plain_rates, width, label='Plain', color="#C73E1D", alpha=0.85, edgecolor='black')
    bars2 = ax.bar(x + width/2, tool_rates, width, label='Tool-Primed', color="#3F7CAC", alpha=0.85, edgecolor='black')

    ax.errorbar(x - width/2, plain_rates, yerr=plain_err, fmt='none', color='black', capsize=4, capthick=1.2)
    ax.errorbar(x + width/2, tool_rates, yerr=tool_err, fmt='none', color='black', capsize=4, capthick=1.2)

    for bar, rate in zip(bars1, plain_rates):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.6, f"{rate:.1f}%", ha='center', va='bottom', fontsize=8)
    for bar, rate in zip(bars2, tool_rates):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.6, f"{rate:.1f}%", ha='center', va='bottom', fontsize=8)

    ax.set_ylabel('Refusal Rate (%)', fontsize=10, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title('Plain vs Tool-Primed Refusal Rates (95% CI)', fontsize=12, fontweight='bold')
    ax.legend()
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig


def fig_overall_split(comparison: Dict, run_ids: List[str], run_labels: Dict[str, str]):
    # Plain overall
    xs_p, ys_p, yerr_p = [], [], [[], []]
    for rid in run_ids:
        d = comparison.get(rid, {}).get("plain")
        if not d:
            continue
        xs_p.append(run_labels.get(rid, rid))
        rate = d.get("refusal_rate", 0) * 100
        plo, phi = d.get("ci95", [None, None])
        ys_p.append(rate)
        if plo is not None and phi is not None:
            yerr_p[0].append(rate - plo * 100)
            yerr_p[1].append(phi * 100 - rate)
        else:
            yerr_p[0].append(0)
            yerr_p[1].append(0)

    fig_p = None
    if xs_p:
        fig_p, axp = plt.subplots(figsize=(5.2, 3.4))
        bars = axp.bar(xs_p, ys_p, color="#C73E1D", alpha=0.85, edgecolor='black')
        axp.errorbar(xs_p, ys_p, yerr=yerr_p, fmt='none', color='black', capsize=5, capthick=1.5)
        for bar, rate in zip(bars, ys_p):
            axp.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.8,
                     f"{rate:.1f}%", ha='center', va='bottom', fontsize=8, fontweight='bold')
        axp.set_ylabel('Overall Refusal Rate (%)', fontsize=10, fontweight='bold')
        axp.set_xlabel('Runs / Conditions', fontsize=10, fontweight='bold')
        axp.set_title('Overall Refusal — Plain', fontsize=12, fontweight='bold')
        axp.set_ylim(0, 100)
        axp.grid(True, alpha=0.3)
        plt.tight_layout()

    # Tool overall
    xs_t, ys_t, yerr_t = [], [], [[], []]
    for rid in run_ids:
        d = comparison.get(rid, {}).get("tool")
        if not d:
            continue
        xs_t.append(run_labels.get(rid, rid))
        rate = d.get("refusal_rate", 0) * 100
        tlo, thi = d.get("ci95", [None, None])
        ys_t.append(rate)
        if tlo is not None and thi is not None:
            yerr_t[0].append(rate - tlo * 100)
            yerr_t[1].append(thi * 100 - rate)
        else:
            yerr_t[0].append(0)
            yerr_t[1].append(0)

    fig_t = None
    if xs_t:
        fig_t, axt = plt.subplots(figsize=(5.2, 3.4))
        bars = axt.bar(xs_t, ys_t, color="#3F7CAC", alpha=0.85, edgecolor='black')
        axt.errorbar(xs_t, ys_t, yerr=yerr_t, fmt='none', color='black', capsize=5, capthick=1.5)
        for bar, rate in zip(bars, ys_t):
            axt.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.8,
                     f"{rate:.1f}%", ha='center', va='bottom', fontsize=8, fontweight='bold')
        axt.set_ylabel('Overall Refusal Rate (%)', fontsize=10, fontweight='bold')
        axt.set_xlabel('Runs / Conditions', fontsize=10, fontweight='bold')
        axt.set_title('Overall Refusal — Tool-Primed', fontsize=12, fontweight='bold')
        axt.set_ylim(0, 100)
        axt.grid(True, alpha=0.3)
        plt.tight_layout()

    return fig_p, fig_t

def fig_category_heatmap(detailed_by_run: Dict[str, Dict], run_ids: List[str], run_labels: Dict[str, str], categories: List[str]):
    # Build matrix: rows=runs, cols=categories
    rows, data = [], []
    for rid in run_ids:
        if rid not in detailed_by_run:
            continue
        rows.append(run_labels.get(rid, rid))
        row = []
        for c in categories:
            rate = detailed_by_run[rid].get("per_category", {}).get(c, {}).get("refusal_rate")
            row.append(rate * 100 if rate is not None else np.nan)
        data.append(row)
    if not rows or not categories:
        return None

    df = pd.DataFrame(data, index=rows, columns=categories)
    fig, ax = plt.subplots(figsize=(min(12, 1.8 + 0.4 * len(categories)), 1.4 + 0.4 * len(rows)))
    sns.heatmap(
        df,
        annot=True,
        fmt='.1f',
        cmap='RdYlBu',
        center=50,
        vmin=0,
        vmax=100,
        cbar_kws={'label': 'Refusal Rate (%)'},
        linewidths=0.5,
        ax=ax,
    )
    ax.set_xlabel('Intent Category', fontsize=10, fontweight='bold')
    ax.set_ylabel('Runs / Conditions', fontsize=10, fontweight='bold')
    ax.set_title('Refusal Rates by Category across Runs', fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right', fontsize=8)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()
    return fig


def fig_tool_priming_delta(detailed_by_run: Dict[str, Dict], run_ids: List[str], run_labels: Dict[str, str], categories: List[str]):
    # Build long-form DataFrame with deltas per run and category
    records = []
    for rid in run_ids:
        det = detailed_by_run.get(rid)
        if not det:
            continue
        for c in categories:
            pk = det.get("per_category_kind", {}).get(c)
            if not pk:
                continue
            pr = pk.get("plain", {}).get("refusal_rate")
            tr = pk.get("tool", {}).get("refusal_rate")
            if pr is None or tr is None:
                continue
            records.append({
                "Category": c,
                "Run": run_labels.get(rid, rid),
                "Delta": (pr - tr) * 100,
            })
    if not records:
        return None
    df = pd.DataFrame(records)
    pivot = df.pivot(index='Category', columns='Run', values='Delta')

    fig, ax = plt.subplots(figsize=(min(12, 1.8 + 0.45 * len(pivot.index)), 4.5))
    pivot.plot(kind='bar', ax=ax, alpha=0.85, edgecolor='black')
    ax.axhline(0, color='black', linewidth=1, alpha=0.6)
    ax.set_ylabel('Tool-Priming Effect (pp: Plain - Tool)', fontsize=10, fontweight='bold')
    ax.set_xlabel('Intent Category', fontsize=10, fontweight='bold')
    ax.set_title('Tool-Priming Effect by Category and Run', fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right', fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig


def fig_vulnerability_ranking(detailed_by_run: Dict[str, Dict], run_ids: List[str], run_labels: Dict[str, str], categories: List[str]):
    # Average delta across selected runs
    agg = {}
    for c in categories:
        deltas = []
        for rid in run_ids:
            det = detailed_by_run.get(rid)
            if not det:
                continue
            pk = det.get("per_category_kind", {}).get(c)
            if not pk:
                continue
            pr = pk.get("plain", {}).get("refusal_rate")
            tr = pk.get("tool", {}).get("refusal_rate")
            if pr is None or tr is None:
                continue
            deltas.append((pr - tr) * 100)
        if deltas:
            agg[c] = float(np.mean(deltas))
    if not agg:
        return None

    items = sorted(agg.items(), key=lambda x: x[1], reverse=True)
    cats = [k for k, _ in items]
    vals = [v for _, v in items]

    fig, ax = plt.subplots(figsize=(8, max(4, 0.3 * len(cats))))
    bars = ax.barh(cats, vals, color=['#d73027' if x > 50 else '#fc8d59' if x > 30 else '#fee08b' if x > 10 else '#e0f3f8' for x in vals], alpha=0.85, edgecolor='black')
    for bar, v in zip(bars, vals):
        ax.text(v + 0.8, bar.get_y() + bar.get_height()/2, f"{v:.1f}pp", va='center', fontsize=9)
    ax.set_xlabel('Avg Tool-Priming Effect (pp)', fontsize=10, fontweight='bold')
    ax.set_ylabel('Intent Category', fontsize=10, fontweight='bold')
    ax.set_title('Category Vulnerability Ranking (Avg across selected runs)', fontsize=12, fontweight='bold')
    ax.grid(True, axis='x', alpha=0.3)
    plt.tight_layout()
    return fig


def fig_significance(comparison: Dict, run_ids: List[str], run_labels: Dict[str, str]):
    # Plain and Tool CIs
    labels, plain_rates, tool_rates = [], [], []
    plain_lo, plain_hi, tool_lo, tool_hi = [], [], [], []
    for rid in run_ids:
        p = comparison.get(rid, {}).get("plain")
        t = comparison.get(rid, {}).get("tool")
        if not p or not t:
            continue
        labels.append(run_labels.get(rid, rid))
        pr = p["refusal_rate"] * 100
        tr = t["refusal_rate"] * 100
        plain_rates.append(pr)
        tool_rates.append(tr)
        plo, phi = p.get("ci95", [pr/100, pr/100])
        tlo, thi = t.get("ci95", [tr/100, tr/100])
        plain_lo.append(plo * 100)
        plain_hi.append(phi * 100)
        tool_lo.append(tlo * 100)
        tool_hi.append(thi * 100)

    if not labels:
        return None

    x = np.arange(len(labels))
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.5, 6.2), sharex=True)

    ax1.errorbar(x, plain_rates,
                 yerr=[np.array(plain_rates) - np.array(plain_lo), np.array(plain_hi) - np.array(plain_rates)],
                 fmt='o', markersize=6, capsize=6, capthick=1.5, color="#C73E1D", label='Plain')
    ax2.errorbar(x, tool_rates,
                 yerr=[np.array(tool_rates) - np.array(tool_lo), np.array(tool_hi) - np.array(tool_rates)],
                 fmt='s', markersize=6, capsize=6, capthick=1.5, color="#3F7CAC", label='Tool-Primed')

    for i, (pr, tr, phi, tlo) in enumerate(zip(plain_rates, tool_rates, plain_hi, tool_lo)):
        if phi < tlo:  # crude non-overlap marker
            ax1.text(i, pr + 3, '***', ha='center', fontsize=12, color='red', fontweight='bold')
            ax2.text(i, tr + 3, '***', ha='center', fontsize=12, color='red', fontweight='bold')

    for ax in (ax1, ax2):
        ax.set_ylabel('Refusal Rate (%)', fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 100)
        ax.legend()

    ax1.set_title('Wilson 95% CIs — *** indicates non-overlap', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Runs / Conditions', fontsize=10, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    plt.tight_layout()
    return fig


# New: split category heatmaps for Plain vs Tool-Primed
def fig_category_heatmap_split(detailed_by_run: Dict[str, Dict], run_ids: List[str], run_labels: Dict[str, str], categories: List[str]):
    # Build matrices for plain and tool refusal rates
    rows, plain_data, tool_data = [], [], []
    for rid in run_ids:
        det = detailed_by_run.get(rid)
        if not det:
            continue
        rows.append(run_labels.get(rid, rid))
        row_plain, row_tool = [], []
        for c in categories:
            pk = det.get("per_category_kind", {}).get(c, {})
            pr = pk.get("plain", {}).get("refusal_rate")
            tr = pk.get("tool", {}).get("refusal_rate")
            row_plain.append(pr * 100 if pr is not None else np.nan)
            row_tool.append(tr * 100 if tr is not None else np.nan)
        plain_data.append(row_plain)
        tool_data.append(row_tool)

    if not rows or not categories:
        return (None, None)

    df_plain = pd.DataFrame(plain_data, index=rows, columns=categories)
    df_tool = pd.DataFrame(tool_data, index=rows, columns=categories)

    w = min(12, 1.8 + 0.4 * len(categories))
    h = 1.4 + 0.4 * len(rows)

    # Plain heatmap
    fig_p, ax_p = plt.subplots(figsize=(w, h))
    sns.heatmap(
        df_plain,
        annot=True,
        fmt='.1f',
        cmap='RdYlBu',
        center=50,
        vmin=0,
        vmax=100,
        cbar_kws={'label': 'Refusal Rate (%)'},
        linewidths=0.5,
        ax=ax_p,
    )
    ax_p.set_xlabel('Intent Category', fontsize=10, fontweight='bold')
    ax_p.set_ylabel('Runs / Conditions', fontsize=10, fontweight='bold')
    ax_p.set_title('Plain (no tool priming)', fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right', fontsize=8)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()

    # Tool heatmap
    fig_t, ax_t = plt.subplots(figsize=(w, h))
    sns.heatmap(
        df_tool,
        annot=True,
        fmt='.1f',
        cmap='RdYlBu',
        center=50,
        vmin=0,
        vmax=100,
        cbar_kws={'label': 'Refusal Rate (%)'},
        linewidths=0.5,
        ax=ax_t,
    )
    ax_t.set_xlabel('Intent Category', fontsize=10, fontweight='bold')
    ax_t.set_ylabel('Runs / Conditions', fontsize=10, fontweight='bold')
    ax_t.set_title('Tool-Primed', fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right', fontsize=8)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()

    return fig_p, fig_t

# ===== UI =====
st.set_page_config(page_title="GPT-OSS Red-Team Dashboard", layout="wide")
st.title("GPT-OSS Red-Team Dashboard")
st.caption("Interactive analysis of refusal rates across runs and categories")

with st.sidebar:
    st.header("Data Selection")
    results_root = st.text_input("Results directory", value=str(RESULTS_DIR))
    results_path = Path(results_root)

    comparison = load_comparison(Path(results_path) / "compare" / "comparison_plus.json")
    detailed = discover_detailed_runs(results_path)

    if not comparison:
        st.warning("comparison_plus.json not found. Only per-run category tabs will work.")

    available_runs = list(comparison.keys()) if comparison else list(detailed.keys())
    if not available_runs:
        st.error("No runs found in results/. Generate analysis first.")
        st.stop()

    selected_runs = st.multiselect(
        "Select runs to analyze",
        options=available_runs,
        default=available_runs[:3] if len(available_runs) >= 3 else available_runs,
    )

    run_labels = make_run_labels(selected_runs)
    st.markdown("Run labels (edit):")
    for rid in list(run_labels.keys()):
        run_labels[rid] = st.text_input(f"Label for {rid}", value=run_labels[rid], key=f"label-{rid}")

    # Category filter
    all_categories = get_category_union({rid: detailed.get(rid, {}) for rid in selected_runs})
    category_sel = st.multiselect(
        "Filter categories (blank = all)", options=all_categories, default=[]
    )

    if category_sel:
        categories = category_sel
    else:
        categories = all_categories

# Tabs
overview, per_category, effects, significance, summary = st.tabs([
    "Overview",
    "Per-Category",
    "Effects & Ranking",
    "Significance",
    "Summary",
])

with overview:
    st.subheader("Overall Refusal Rates")
    if comparison and selected_runs:
        st.pyplot(fig_overall_refusal(comparison, selected_runs, run_labels))
    else:
        st.info("Overall chart requires comparison_plus.json.")

    st.subheader("Plain vs Tool-Primed")
    if comparison and selected_runs:
        st.pyplot(fig_plain_vs_tool(comparison, selected_runs, run_labels))
    else:
        st.info("Plain vs Tool chart requires comparison_plus.json.")

    st.subheader("Overall — Split: Plain vs Tool-Primed")
    if comparison and selected_runs:
        fig_p, fig_t = fig_overall_split(comparison, selected_runs, run_labels)
        colp, colt = st.columns(2)
        with colp:
            if fig_p is not None:
                st.pyplot(fig_p)
            else:
                st.info("Plain overall requires 'plain' in comparison_plus.json for selected runs.")
        with colt:
            if fig_t is not None:
                st.pyplot(fig_t)
            else:
                st.info("Tool overall requires 'tool' in comparison_plus.json for selected runs.")
    else:
        st.info("Split overall charts require comparison_plus.json.")

with per_category:
    st.subheader("Category Heatmap across Runs")
    if categories:
        fig = fig_category_heatmap(detailed, selected_runs, run_labels, categories)
        if fig is not None:
            st.pyplot(fig)
        else:
            st.info("Heatmap requires per_category in analysis_plus.json for selected runs.")
    else:
        st.info("No categories found in selected runs.")

    # Split heatmaps by Plain vs Tool-Primed
    if categories:
        st.subheader("Split Heatmaps: Plain vs Tool-Primed")
        fig_plain_tool = fig_category_heatmap_split(detailed, selected_runs, run_labels, categories)
        if fig_plain_tool is not None:
            fig_plain, fig_tool = fig_plain_tool
            colp, colt = st.columns(2)
            if fig_plain is not None:
                with colp:
                    st.pyplot(fig_plain)
            else:
                with colp:
                    st.info("Plain heatmap requires per_category_kind->plain in analysis_plus.json.")
            if fig_tool is not None:
                with colt:
                    st.pyplot(fig_tool)
            else:
                with colt:
                    st.info("Tool-primed heatmap requires per_category_kind->tool in analysis_plus.json.")
        else:
            st.info("Split heatmaps require per_category_kind with plain/tool in analysis_plus.json.")

with effects:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Tool-Priming Effect by Category")
        fig = fig_tool_priming_delta(detailed, selected_runs, run_labels, categories)
        if fig is not None:
            st.pyplot(fig)
        else:
            st.info("Deltas require per_category_kind with plain/tool in analysis_plus.json.")
    with col2:
        st.subheader("Category Vulnerability Ranking (Avg across selected runs)")
        fig = fig_vulnerability_ranking(detailed, selected_runs, run_labels, categories)
        if fig is not None:
            st.pyplot(fig)
        else:
            st.info("Ranking requires per_category_kind with plain/tool in analysis_plus.json.")

with significance:
    st.subheader("Wilson 95% Confidence Intervals")
    if comparison and selected_runs:
        fig = fig_significance(comparison, selected_runs, run_labels)
        if fig is not None:
            st.pyplot(fig)
    else:
        st.info("Significance view requires comparison_plus.json.")

with summary:
    st.subheader("Summary Table")
    if comparison and selected_runs:
        # Build table data
        rows: List[Tuple[str, float, float, float, float, float]] = []
        for rid in selected_runs:
            overall = comparison.get(rid, {}).get("overall")
            plain = comparison.get(rid, {}).get("plain")
            tool = comparison.get(rid, {}).get("tool")
            if not (overall and plain and tool):
                continue
            label = run_labels.get(rid, rid)
            overall_pct = overall["refusal_rate"] * 100
            plain_pct = plain["refusal_rate"] * 100
            tool_pct = tool["refusal_rate"] * 100
            delta = plain_pct - tool_pct
            # Cohen's h
            p1 = plain["refusal_rate"]
            p2 = tool["refusal_rate"]
            cohens_h = 2 * (np.arcsin(np.sqrt(p1)) - np.arcsin(np.sqrt(p2)))
            rows.append((label, overall_pct, plain_pct, tool_pct, delta, cohens_h))

        if rows:
            df = pd.DataFrame(rows, columns=[
                "Run / Condition", "Overall %", "Plain %", "Tool %", "Tool-Priming Effect (pp)", "Cohen's h"
            ])
            st.dataframe(df.style.format({
                "Overall %": "{:.1f}",
                "Plain %": "{:.1f}",
                "Tool %": "{:.1f}",
                "Tool-Priming Effect (pp)": "{:.1f}",
                "Cohen's h": "{:.2f}",
            }), use_container_width=True)
        else:
            st.info("Summary requires comparison_plus.json entries for selected runs.")

st.markdown("---")
st.caption("Tip: Use the sidebar to rename runs (e.g., 'Null System', 'Tool-Primed System', 'Overtly Malicious').")
