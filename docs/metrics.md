# CyCRS metrics

Measured on 2026-10-14 on a Windows laptop (local build, Chromium 153). Regenerate with `python -m src.report_assets` from `analysis/`.

## Recommendation latency in the browser engine

| Runs | Mean | p50 | p95 | p99 |
| --- | --- | --- | --- | --- |
| 1000 | 0.063 ms | 0.059 ms | 0.088 ms | 0.125 ms |

Full `recommend()` with trace over the 5 reference profiles (tinybench in vitest, `web/tests/bench/recommend.bench.test.ts`).

## JavaScript referenced by each page (static export)

| Route | Chunks | Raw | Gzip |
| --- | --- | --- | --- |
| `/` | 8 | 563 KB | 173 KB |
| `/assess/` | 10 | 643 KB | 197 KB |
| `/results/` | 10 | 658 KB | 202 KB |
| `/models/mlr-impact/` | 9 | 570 KB | 176 KB |
| `/data/` | 9 | 567 KB | 175 KB |

Sum of the script chunks listed in each page's HTML. Recharts loads lazily after first paint and is not included.

## Lighthouse (local, mobile preset, gzip test server)

| Page | Performance (runs) | Accessibility | LCP (median) | TBT (median) | CLS |
| --- | --- | --- | --- | --- | --- |
| `/` | 97, 96 | 100, 100 | 2.6 s | 90 ms | 0 |
| `/results/` | 84, 81 | 100, 100 | 3.6 s | 325 ms | 0 |
| `/models/mlr-impact/` | 87, 87 | 100, 100 | 3.3 s | 240 ms | 0 |

Not yet measured on Vercel; local Windows runs vary by up to 9 points between identical runs.

## Models

| Metric | Value | Source |
| --- | --- | --- |
| Best breach classifier (by 5-fold CV AUC) | decision_tree, CV AUC 0.826 +/- 0.019, test AUC 0.850 | `analysis/outputs/classifier_comparison.csv` |
| Attack-type model AUC, hacking | 0.865 (CV 0.865) | `analysis/outputs/04_attack_auc.csv` |
| Attack-type model AUC, malware | 0.840 (CV 0.855) | `analysis/outputs/04_attack_auc.csv` |
| Attack-type model AUC, social | 0.738 (CV 0.703) | `analysis/outputs/04_attack_auc.csv` |
| Attack-type model AUC, error | 0.741 (CV 0.760) | `analysis/outputs/04_attack_auc.csv` |
| Attack-type model AUC, misuse | 0.690 (CV 0.702) | `analysis/outputs/04_attack_auc.csv` |
| Attack-type model AUC, physical | 0.892 (CV 0.902) | `analysis/outputs/04_attack_auc.csv` |
| Coverage hit rate, held-out incidents | 20.9% vs baseline 20.9% (n 3105, p 1) | `analysis/outputs/cards/coverage-hit-rate.json` |
| Greedy vs exhaustive gap, 5 reference profiles | 0.00% | `analysis/outputs/cards/budget-optimiser.json` |
