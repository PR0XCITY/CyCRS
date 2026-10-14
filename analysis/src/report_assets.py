import csv
import gzip
import json
import re
import shutil
import statistics
from pathlib import Path

from src.audit import SYLLABUS
from src.cards import load_cards
from src.nbutil import FIG, OUT, ROOT

REPO = ROOT.parent
WEB = REPO / "web"
DOCS = REPO / "docs"
RA = REPO / "report_assets"
SECTIONS = (
    "summary",
    "problem",
    "objectives",
    "data exploration",
    "methodology",
    "interpretation",
    "findings",
    "conclusions",
)
STAGE_SECTION = {
    "prepare": "data exploration",
    "explore": "data exploration",
    "impact": "interpretation",
    "likelihood": "interpretation",
    "segment": "interpretation",
    "decide": "findings",
    "evaluate": "conclusions",
}
FIGURES = {
    "01_missing_heatmap.png": (
        "fig_data_missing_values_heatmap.png",
        "data exploration",
        "Missing or Unknown values across key variables",
    ),
    "01_records_skewness.png": (
        "fig_data_records_lost_skew_before_after_log.png",
        "data exploration",
        "Records lost before and after log10(1 + x)",
    ),
    "02_hist_log_records.png": (
        "fig_explore_records_lost_histogram.png",
        "data exploration",
        "Histogram of log records lost",
    ),
    "02_bar_action_categories.png": (
        "fig_explore_action_categories.png",
        "data exploration",
        "Incidents by action category",
    ),
    "02_pie_actor_type.png": (
        "fig_explore_actor_type_share.png",
        "data exploration",
        "Share of incidents by actor type",
    ),
    "02_box_log_records_by_sector.png": (
        "fig_explore_records_by_sector_box.png",
        "data exploration",
        "Records lost by sector, top 8",
    ),
    "02_scatter_discovery_records.png": (
        "fig_explore_discovery_vs_records.png",
        "data exploration",
        "Discovery time against records lost",
    ),
    "02_treemap_sector_action.png": (
        "fig_explore_sector_action_treemap.png",
        "data exploration",
        "Sector by action category treemap",
    ),
    "02_line_actions_by_year.png": (
        "fig_explore_actions_by_year.png",
        "data exploration",
        "Action categories by incident year",
    ),
    "02_qq_records.png": (
        "fig_explore_normal_vs_lognormal_qq.png",
        "methodology",
        "QQ plots for normal and lognormal fits",
    ),
    "02_conditional_probability.png": (
        "fig_explore_conditional_probability.png",
        "interpretation",
        "P(action category given sector)",
    ),
    "02_spearman_heatmap.png": (
        "fig_explore_spearman_heatmap.png",
        "data exploration",
        "Spearman correlation heatmap",
    ),
    "03_slr.png": (
        "fig_regression_slr_size.png",
        "interpretation",
        "Simple regression of records lost on organisation size",
    ),
    "03_vif.png": ("fig_regression_vif.png", "methodology", "Variance inflation factors"),
    "03_residual_checks.png": (
        "fig_regression_residual_checks.png",
        "methodology",
        "Residuals against fitted values and residual QQ plot",
    ),
    "03_residual_order.png": (
        "fig_regression_residual_order.png",
        "methodology",
        "Residuals in row order (Durbin-Watson)",
    ),
    "04_knn_elbow.png": ("fig_classify_knn_elbow.png", "methodology", "KNN cross-validated error by k"),
    "04_roc_breach.png": (
        "fig_classify_breach_roc.png",
        "interpretation",
        "ROC curves for the five breach classifiers",
    ),
    "04_confusion_breach.png": (
        "fig_classify_breach_confusion.png",
        "interpretation",
        "Confusion matrices for the breach classifiers",
    ),
    "04_tree.png": ("fig_classify_decision_tree.png", "interpretation", "Decision tree to depth 4"),
    "04_roc_attack.png": (
        "fig_classify_attack_type_roc.png",
        "interpretation",
        "ROC curves for the attack-type models",
    ),
    "05_pca_scree.png": ("fig_segment_pca_scree.png", "methodology", "PCA scree plot"),
    "05_pca_loadings.png": ("fig_segment_pca_loadings.png", "methodology", "PCA loadings heatmap"),
    "05_pca_biplot.png": ("fig_segment_pca_biplot.png", "interpretation", "PCA biplot"),
    "05_kmeans_scan.png": (
        "fig_segment_kmeans_elbow_silhouette.png",
        "methodology",
        "K-means elbow and silhouette",
    ),
    "05_persona_attack_mix.png": (
        "fig_segment_persona_attack_mix.png",
        "interpretation",
        "Attack mix of each persona",
    ),
    "05_dendrogram.png": (
        "fig_segment_ward_dendrogram.png",
        "methodology",
        "Ward dendrogram on 500 incidents",
    ),
    "05_fa.png": ("fig_segment_factor_analysis.png", "methodology", "Factor analysis scree and loadings"),
    "05_fa_state_scores.png": (
        "fig_segment_factor_state_scores.png",
        "interpretation",
        "State scores on the first factor",
    ),
    "06_expected_loss_reference.png": (
        "fig_decide_expected_loss_reference.png",
        "findings",
        "Expected loss by attack type, reference profile",
    ),
    "06_hit_rate.png": (
        "fig_evaluate_coverage_hit_rate.png",
        "findings",
        "Coverage hit rate against baseline",
    ),
    "07_tornado.png": (
        "fig_evaluate_sensitivity_tornado.png",
        "conclusions",
        "Tornado chart for the three largest personas",
    ),
}
TABLES = {
    "01_lineage.csv": ("tab_data_lineage_row_counts.csv", "data exploration"),
    "01_variable_types.csv": ("tab_data_variable_types.csv", "data exploration"),
    "01_missing_values.csv": ("tab_data_missing_values.csv", "data exploration"),
    "02_summary_stats.csv": ("tab_explore_summary_statistics.csv", "data exploration"),
    "02_distribution_fit.csv": ("tab_explore_distribution_fit.csv", "methodology"),
    "02_conditional_probability.csv": ("tab_explore_conditional_probability.csv", "interpretation"),
    "hypothesis_tests.csv": ("tab_explore_hypothesis_tests.csv", "findings"),
    "02_ncrb_region_crime_mix.csv": ("tab_problem_ncrb_region_crime_mix.csv", "problem"),
    "03_model_comparison.csv": ("tab_regression_model_comparison.csv", "methodology"),
    "mlr_coefficients.csv": ("tab_regression_coefficients_multipliers.csv", "interpretation"),
    "03_vif.csv": ("tab_regression_vif.csv", "methodology"),
    "classifier_comparison.csv": ("tab_classify_breach_comparison.csv", "findings"),
    "04_attack_auc.csv": ("tab_classify_attack_type_auc.csv", "findings"),
    "04_attack_odds.csv": ("tab_classify_attack_type_odds_ratios.csv", "interpretation"),
    "05_personas.csv": ("tab_segment_personas.csv", "interpretation"),
    "05_fa_loadings.csv": ("tab_segment_factor_loadings.csv", "interpretation"),
    "06_greedy_vs_exhaustive.csv": ("tab_decide_greedy_vs_exhaustive.csv", "findings"),
    "06_hit_rate_by_size.csv": ("tab_evaluate_hit_rate_by_size.csv", "findings"),
    "07_case_replay.csv": ("tab_evaluate_case_replay.csv", "conclusions"),
    "07_stable_controls.csv": ("tab_evaluate_stable_controls.csv", "conclusions"),
    "07_tornado.csv": ("tab_evaluate_tornado.csv", "conclusions"),
}
ROUTES = ("", "assess/", "results/", "models/mlr-impact/", "data/")


def read_csv(p):
    with Path(p).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def card_map():
    return {c["id"]: c for c in load_cards()}


def route_js(r):
    h = (WEB / "out" / r / "index.html").read_text(encoding="utf-8")
    fs = sorted(set(re.findall(r"/_next/static/chunks/[A-Za-z0-9_.~-]+\.js", h)))
    raw = sum((WEB / "out" / f.lstrip("/")).stat().st_size for f in fs)
    gz = sum(len(gzip.compress((WEB / "out" / f.lstrip("/")).read_bytes(), 9)) for f in fs)
    return {"route": "/" + r, "files": len(fs), "raw_kb": raw / 1024, "gzip_kb": gz / 1024}


def lighthouse(p=DOCS / "data" / "lighthouse_runs.txt"):
    rs = {}
    for ln in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"(\S+) perf (\d+) a11y (\d+) .* LCP ([\d.]+)\s+s TBT ([\d,]+)\s+ms CLS (\S+)", ln)
        if m:
            rs.setdefault(m.group(1), []).append(
                (
                    int(m.group(2)),
                    int(m.group(3)),
                    float(m.group(4)),
                    int(m.group(5).replace(",", "")),
                    m.group(6),
                )
            )
    return {
        k: {
            "runs": len(v),
            "perf": [x[0] for x in v],
            "a11y": [x[1] for x in v],
            "lcp_s": statistics.median(x[2] for x in v),
            "tbt_ms": statistics.median(x[3] for x in v),
            "cls": v[0][4],
        }
        for k, v in rs.items()
    }


def best_classifier():
    rs = read_csv(OUT / "classifier_comparison.csv")
    return max(rs, key=cv_mean)


def cv_mean(r):
    return float(r["cv_auc_mean"])


def metrics_md():
    cm = card_map()
    b = json.loads((DOCS / "data" / "bench.json").read_text(encoding="utf-8"))
    lh = lighthouse()
    js = [route_js(r) for r in ROUTES]
    bc = best_classifier()
    att = read_csv(OUT / "04_attack_auc.csv")
    hk = cm["coverage-hit-rate"]["results"]["key_numbers"]
    gk = cm["budget-optimiser"]["results"]["key_numbers"]
    ls = [
        "# CyCRS metrics",
        "",
        "Measured on 2026-10-14 on a Windows laptop (local build, Chromium 153). Regenerate with `python -m src.report_assets` from `analysis/`.",
        "",
        "## Recommendation latency in the browser engine",
        "",
        "| Runs | Mean | p50 | p95 | p99 |",
        "| --- | --- | --- | --- | --- |",
        f"| {b['runs']} | {b['mean_ms']:.3f} ms | {b['p50_ms']:.3f} ms | {b['p95_ms']:.3f} ms | {b['p99_ms']:.3f} ms |",
        "",
        "Full `recommend()` with trace over the 5 reference profiles (tinybench in vitest, `web/tests/bench/recommend.bench.test.ts`).",
        "",
        "## JavaScript referenced by each page (static export)",
        "",
        "| Route | Chunks | Raw | Gzip |",
        "| --- | --- | --- | --- |",
        *[f"| `{j['route']}` | {j['files']} | {j['raw_kb']:.0f} KB | {j['gzip_kb']:.0f} KB |" for j in js],
        "",
        "Sum of the script chunks listed in each page's HTML. Recharts loads lazily after first paint and is not included.",
        "",
        "## Lighthouse (local, mobile preset, gzip test server)",
        "",
        "| Page | Performance (runs) | Accessibility | LCP (median) | TBT (median) | CLS |",
        "| --- | --- | --- | --- | --- | --- |",
        *[
            f"| `{k}` | {', '.join(map(str, v['perf']))} | {', '.join(map(str, v['a11y']))} | {v['lcp_s']:.1f} s | {v['tbt_ms']:.0f} ms | {v['cls']} |"
            for k, v in lh.items()
        ],
        "",
        "Not yet measured on Vercel; local Windows runs vary by up to 9 points between identical runs.",
        "",
        "## Models",
        "",
        "| Metric | Value | Source |",
        "| --- | --- | --- |",
        f"| Best breach classifier (by 5-fold CV AUC) | {bc['model']}, CV AUC {float(bc['cv_auc_mean']):.3f} +/- {float(bc['cv_auc_sd']):.3f}, test AUC {float(bc['auc']):.3f} | `analysis/outputs/classifier_comparison.csv` |",
        *[
            f"| Attack-type model AUC, {r['category']} | {float(r['test_auc']):.3f} (CV {float(r['cv_auc_mean']):.3f}) | `analysis/outputs/04_attack_auc.csv` |"
            for r in att
        ],
        f"| Coverage hit rate, held-out incidents | {100 * hk['hit_rate']:.1f}% vs baseline {100 * hk['baseline_hit_rate']:.1f}% (n {hk['n_test']}, p {hk['p_value']:.2g}) | `analysis/outputs/cards/coverage-hit-rate.json` |",
        f"| Greedy vs exhaustive gap, 5 reference profiles | {gk['max_gap_pct']:.2f}% | `analysis/outputs/cards/budget-optimiser.json` |",
        "",
    ]
    DOCS.mkdir(exist_ok=True)
    (DOCS / "metrics.md").write_text("\n".join(ls), encoding="utf-8")
    return {"bench": b, "lighthouse": lh, "js": js, "best": bc, "attack": att, "hit": hk, "gap": gk}


def copy_assets():
    if RA.exists():
        shutil.rmtree(RA)
    (RA / "figures").mkdir(parents=True)
    (RA / "tables").mkdir()
    rows = []
    for s, (n, sec, cap) in FIGURES.items():
        shutil.copy(FIG / s, RA / "figures" / n)
        rows.append((f"figures/{n}", sec, cap, f"analysis/figures/{s}"))
    for s, (n, sec) in TABLES.items():
        shutil.copy(OUT / s, RA / "tables" / n)
        rows.append(
            (
                f"tables/{n}",
                sec,
                n.removeprefix("tab_").removesuffix(".csv").replace("_", " "),
                f"analysis/outputs/{s}",
            )
        )
    for s, n, sec, cap in (
        (
            "docs/demo.gif",
            "figures/demo_assess_to_model_page.gif",
            "summary",
            "Demo: assessment to results to model page",
        ),
        (
            "docs/screenshot-results.png",
            "figures/screenshot_results_page.png",
            "summary",
            "Results page for a small retail shop",
        ),
        (
            "docs/screenshot-models.png",
            "figures/screenshot_how_it_works.png",
            "methodology",
            "How it works: model pipeline",
        ),
    ):
        shutil.copy(REPO / s, RA / n)
        rows.append((n, sec, cap, s))
    shutil.copy(ROOT / "data" / "sources" / "SOURCES.md", RA / "SOURCES.md")
    rows.sort(key=section_key)
    ls = [
        "# Report asset map",
        "",
        "| File | Report section | What it shows | Generated from |",
        "| --- | --- | --- | --- |",
    ]
    ls += [f"| `{f}` | {sec} | {cap} | `{src}` |" for f, sec, cap, src in rows]
    (RA / "MAP.md").write_text("\n".join(ls) + "\n", encoding="utf-8")
    return rows


def section_key(r):
    return (SECTIONS.index(r[1]), r[0])


def show(v):
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)


def facts_md(m):
    cm = card_map()
    vs = {r["key"]: r for r in read_csv(ROOT / "data" / "sources" / "values.csv") if r["value"].strip()}
    out = {s: [] for s in SECTIONS}
    b = m["bench"]
    out["summary"] += [
        (
            "Browser recommendation latency p95",
            f"{b['p95_ms']:.3f} ms over {b['runs']} runs",
            "docs/data/bench.json",
        ),
        (
            "Best breach classifier CV AUC",
            f"{m['best']['model']} {float(m['best']['cv_auc_mean']):.3f}",
            "analysis/outputs/classifier_comparison.csv",
        ),
        (
            "Coverage hit rate vs baseline",
            f"{m['hit']['hit_rate']:.4f} vs {m['hit']['baseline_hit_rate']:.4f}",
            "analysis/outputs/cards/coverage-hit-rate.json",
        ),
        (
            "Greedy vs exhaustive gap",
            f"{m['gap']['max_gap_pct']:.2f}%",
            "analysis/outputs/cards/budget-optimiser.json",
        ),
        ("Model cards", str(len(cm)), "web/public/model/cards.json"),
    ]
    for k in (
        "annual_incident_prob",
        "breach_total_cost_inr",
        "breach_avg_records",
        "usd_inr",
        "gbp_inr",
        "smb_breach_cost_small_gbp",
        "smb_breach_cost_medium_gbp",
    ):
        if k in vs:
            out["problem"].append(
                (
                    k,
                    f"{vs[k]['value']} {vs[k]['unit']} ({vs[k]['publisher']}, {vs[k]['year']})",
                    "analysis/data/sources/values.csv",
                )
            )
    nc = read_csv(ROOT / "data" / "processed" / "ncrb_state.csv")
    out["problem"].append(
        (
            "NCRB cyber crime cases 2024, all states and UTs",
            str(sum(int(float(r["cases_2024"])) for r in nc)),
            "analysis/data/processed/ncrb_state.csv",
        )
    )
    out["objectives"].append(
        (
            "Syllabus techniques covered by a model card",
            str(len(SYLLABUS)),
            "analysis/src/audit.py SYLLABUS and docs/audit.md",
        )
    )
    for c in sorted(cm.values(), key=order_of):
        sec = STAGE_SECTION.get(c["stage"], "findings")
        for k, v in c["results"]["key_numbers"].items():
            out[sec].append(
                (f"{c['id']}: {k}", show(v), f"analysis/outputs/cards/{c['id']}.json results.key_numbers.{k}")
            )
    out["methodology"] += [
        (
            f"{c['id']}: {d['name']}",
            show(d["value"]),
            f"analysis/outputs/cards/{c['id']}.json data_properties",
        )
        for c in cm.values()
        if c["stage"] in ("impact", "likelihood", "segment")
        for d in c["data_properties"]
    ]
    ls = [
        "# Key facts by report section",
        "",
        "Every value below is read from the listed file; regenerate with `python -m src.report_assets` from `analysis/`.",
    ]
    for s in SECTIONS:
        ls += ["", f"## {s.capitalize()}", "", "| Fact | Value | Source |", "| --- | --- | --- |"]
        ls += [f"| {a} | {b_} | `{c}` |" for a, b_, c in out[s]] or ["| none | | |"]
    (RA / "FACTS.md").write_text("\n".join(ls) + "\n", encoding="utf-8")


def order_of(c):
    return c["order"]


def result_lines(c):
    kn = c["results"]["key_numbers"]
    return [f"- {k.replace('_', ' ')}: {show(v)}" for k, v in list(kn.items())[:8]]


def models_md():
    ls = [
        "# Models in plain text",
        "",
        "One section per model card, in pipeline order. Text is generated from `analysis/outputs/cards/*.json`.",
    ]
    for c in sorted(card_map().values(), key=order_of):
        ls += [
            "",
            f"## {c['order']}. {c['title']} (`{c['id']}`)",
            "",
            f"Module: {c['module']}. Stage: {c['stage']}. Runs live on the user's business: {'yes' if c['used_live'] else 'no'}.",
            "",
            f"**Question.** {c['question']}",
            "",
            f"**Why this model.** {c['why']}",
            "",
            "**Result.**",
            "",
            *result_lines(c),
            "",
            f"**What it yields.** {c['yields']}",
            "",
            "**Limitations.** " + " ".join(c["limitations"]),
        ]
    (RA / "MODELS.md").write_text("\n".join(ls) + "\n", encoding="utf-8")


def main():
    m = metrics_md()
    copy_assets()
    facts_md(m)
    models_md()
    return m


if __name__ == "__main__":
    main()
