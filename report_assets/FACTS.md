# Key facts by report section

Every value below is read from the listed file; regenerate with `python -m src.report_assets` from `analysis/`.

## Summary

| Fact | Value | Source |
| --- | --- | --- |
| Browser recommendation latency p95 | 0.088 ms over 1000 runs | `docs/data/bench.json` |
| Best breach classifier CV AUC | decision_tree 0.826 | `analysis/outputs/classifier_comparison.csv` |
| Coverage hit rate vs baseline | 0.2087 vs 0.2087 | `analysis/outputs/cards/coverage-hit-rate.json` |
| Greedy vs exhaustive gap | 0.00% | `analysis/outputs/cards/budget-optimiser.json` |
| Model cards | 18 | `web/public/model/cards.json` |

## Problem

| Fact | Value | Source |
| --- | --- | --- |
| annual_incident_prob | 0.468 share of small businesses per year (CPA Australia, 2026) | `analysis/data/sources/values.csv` |
| breach_total_cost_inr | 255000000 INR per breach (average total organisational cost) (IBM, 2026) | `analysis/data/sources/values.csv` |
| breach_avg_records | 39500 records compromised per breach (India average) (IBM, 2026) | `analysis/data/sources/values.csv` |
| usd_inr | 95.2477 INR per USD (Reserve Bank of India (rate source FBIL), 2026) | `analysis/data/sources/values.csv` |
| gbp_inr | 125.9222 INR per GBP (Reserve Bank of India (rate source FBIL), 2026) | `analysis/data/sources/values.csv` |
| smb_breach_cost_small_gbp | 14440 GBP per most disruptive breach (95th percentile) (UK Department for Science, Innovation and Technology, 2026) | `analysis/data/sources/values.csv` |
| smb_breach_cost_medium_gbp | 83600 GBP per most disruptive breach (90th percentile) (UK Department for Science, Innovation and Technology, 2026) | `analysis/data/sources/values.csv` |
| NCRB cyber crime cases 2024, all states and UTs | 101928 | `analysis/data/processed/ncrb_state.csv` |

## Objectives

| Fact | Value | Source |
| --- | --- | --- |
| Syllabus techniques covered by a model card | 16 | `analysis/src/audit.py SYLLABUS and docs/audit.md` |

## Data exploration

| Fact | Value | Source |
| --- | --- | --- |
| data-preparation: raw_files | 10596 | `analysis/outputs/cards/data-preparation.json results.key_numbers.raw_files` |
| data-preparation: flattened_rows | 10596 | `analysis/outputs/cards/data-preparation.json results.key_numbers.flattened_rows` |
| data-preparation: columns | 55 | `analysis/outputs/cards/data-preparation.json results.key_numbers.columns` |
| data-preparation: classifier_rows | 8267 | `analysis/outputs/cards/data-preparation.json results.key_numbers.classifier_rows` |
| data-preparation: breach_yes | 7492 | `analysis/outputs/cards/data-preparation.json results.key_numbers.breach_yes` |
| data-preparation: breach_no | 775 | `analysis/outputs/cards/data-preparation.json results.key_numbers.breach_no` |
| data-preparation: regression_rows | 5398 | `analysis/outputs/cards/data-preparation.json results.key_numbers.regression_rows` |
| data-preparation: skew_raw | 50.57 | `analysis/outputs/cards/data-preparation.json results.key_numbers.skew_raw` |
| data-preparation: mean_records_lost | 2.277e+07 | `analysis/outputs/cards/data-preparation.json results.key_numbers.mean_records_lost` |
| data-preparation: median_records_lost | 1364 | `analysis/outputs/cards/data-preparation.json results.key_numbers.median_records_lost` |
| data-preparation: skew_log | 0.3601 | `analysis/outputs/cards/data-preparation.json results.key_numbers.skew_log` |
| descriptive: incidents | 10596 | `analysis/outputs/cards/descriptive.json results.key_numbers.incidents` |
| descriptive: median_records_lost | 1364 | `analysis/outputs/cards/descriptive.json results.key_numbers.median_records_lost` |
| descriptive: median_discovery_days | 91.31 | `analysis/outputs/cards/descriptive.json results.key_numbers.median_discovery_days` |
| descriptive: spearman_discovery_records | -0.03517 | `analysis/outputs/cards/descriptive.json results.key_numbers.spearman_discovery_records` |
| distribution-fit: n | 5398 | `analysis/outputs/cards/distribution-fit.json results.key_numbers.n` |
| distribution-fit: skew_records_lost | 50.57 | `analysis/outputs/cards/distribution-fit.json results.key_numbers.skew_records_lost` |
| distribution-fit: ks_d_normal | 0.4858 | `analysis/outputs/cards/distribution-fit.json results.key_numbers.ks_d_normal` |
| distribution-fit: ks_d_lognormal | 0.0914 | `analysis/outputs/cards/distribution-fit.json results.key_numbers.ks_d_lognormal` |
| distribution-fit: lognormal_sigma | 5.032 | `analysis/outputs/cards/distribution-fit.json results.key_numbers.lognormal_sigma` |
| distribution-fit: lognormal_scale | 1329 | `analysis/outputs/cards/distribution-fit.json results.key_numbers.lognormal_scale` |
| conditional-probability: n_Health Care and Social Assistance | 2564 | `analysis/outputs/cards/conditional-probability.json results.key_numbers.n_Health Care and Social Assistance` |
| conditional-probability: n_Public Administration | 2403 | `analysis/outputs/cards/conditional-probability.json results.key_numbers.n_Public Administration` |
| conditional-probability: n_Educational Services | 1155 | `analysis/outputs/cards/conditional-probability.json results.key_numbers.n_Educational Services` |
| conditional-probability: n_Finance and Insurance | 980 | `analysis/outputs/cards/conditional-probability.json results.key_numbers.n_Finance and Insurance` |
| conditional-probability: n_Information | 876 | `analysis/outputs/cards/conditional-probability.json results.key_numbers.n_Information` |
| conditional-probability: n_Retail Trade | 529 | `analysis/outputs/cards/conditional-probability.json results.key_numbers.n_Retail Trade` |
| conditional-probability: n_Professional, Scientific, and Technical Services | 488 | `analysis/outputs/cards/conditional-probability.json results.key_numbers.n_Professional, Scientific, and Technical Services` |
| conditional-probability: n_Manufacturing | 271 | `analysis/outputs/cards/conditional-probability.json results.key_numbers.n_Manufacturing` |
| hypothesis-tests: tests | 9 | `analysis/outputs/cards/hypothesis-tests.json results.key_numbers.tests` |
| hypothesis-tests: rejected_holm | 7 | `analysis/outputs/cards/hypothesis-tests.json results.key_numbers.rejected_holm` |
| hypothesis-tests: ransomware_share_2020_on | 0.5517 | `analysis/outputs/cards/hypothesis-tests.json results.key_numbers.ransomware_share_2020_on` |
| hypothesis-tests: ransomware_share_before_2020 | 0.02438 | `analysis/outputs/cards/hypothesis-tests.json results.key_numbers.ransomware_share_before_2020` |
| slr: intercept | 4.906 | `analysis/outputs/cards/slr.json results.key_numbers.intercept` |
| slr: skew_log_records | 0.3601 | `analysis/outputs/cards/slr.json results.key_numbers.skew_log_records` |
| slr: slope | -0.528 | `analysis/outputs/cards/slr.json results.key_numbers.slope` |
| slr: r2 | 0.1172 | `analysis/outputs/cards/slr.json results.key_numbers.r2` |
| slr: p_value | 0 | `analysis/outputs/cards/slr.json results.key_numbers.p_value` |
| slr: n | 3693 | `analysis/outputs/cards/slr.json results.key_numbers.n` |

## Methodology

| Fact | Value | Source |
| --- | --- | --- |
| attack-likelihood: Best category AUC (physical) | 0.8922 | `analysis/outputs/cards/attack-likelihood.json data_properties` |
| attack-likelihood: Weakest category AUC (misuse) | 0.6899 | `analysis/outputs/cards/attack-likelihood.json data_properties` |
| attack-likelihood: Profile features | 15 | `analysis/outputs/cards/attack-likelihood.json data_properties` |
| breach-classifiers: Share of No in training | 0.09367 | `analysis/outputs/cards/breach-classifiers.json data_properties` |
| breach-classifiers: No cases in test set | 233 | `analysis/outputs/cards/breach-classifiers.json data_properties` |
| breach-classifiers: Best model by CV AUC | decision_tree (0.826 +/- 0.019) | `analysis/outputs/cards/breach-classifiers.json data_properties` |
| breach-classifiers: Youden threshold for best model | 0.4425 | `analysis/outputs/cards/breach-classifiers.json data_properties` |
| factor-analysis: Bartlett chi-square p | 0 | `analysis/outputs/cards/factor-analysis.json data_properties` |
| factor-analysis: KMO | 0.7331 | `analysis/outputs/cards/factor-analysis.json data_properties` |
| factor-analysis: Factors with eigenvalue above 1 | 2 | `analysis/outputs/cards/factor-analysis.json data_properties` |
| factor-analysis: Cases per variable | 4.5 | `analysis/outputs/cards/factor-analysis.json data_properties` |
| hierarchical: Adjusted Rand index vs K-means | 0.4392 | `analysis/outputs/cards/hierarchical.json data_properties` |
| mlr-impact: Skewness of records lost | 50.57 | `analysis/outputs/cards/mlr-impact.json data_properties` |
| mlr-impact: Breusch-Pagan p | 0 | `analysis/outputs/cards/mlr-impact.json data_properties` |
| mlr-impact: Jarque-Bera p | 0 | `analysis/outputs/cards/mlr-impact.json data_properties` |
| mlr-impact: Durbin-Watson | 1.984 | `analysis/outputs/cards/mlr-impact.json data_properties` |
| mlr-impact: Maximum VIF | 9.4 | `analysis/outputs/cards/mlr-impact.json data_properties` |
| mlr-impact: Test RMSE gap, business vs best model | 0.09245 | `analysis/outputs/cards/mlr-impact.json data_properties` |
| pca: Components with eigenvalue above 1 | 12 | `analysis/outputs/cards/pca.json data_properties` |
| pca: Components for 80% variance | 14 | `analysis/outputs/cards/pca.json data_properties` |
| pca: Variance explained by PC1 | 0.1788 | `analysis/outputs/cards/pca.json data_properties` |
| pca: Variance explained by PC2 | 0.1075 | `analysis/outputs/cards/pca.json data_properties` |
| personas-kmeans: Chosen k | 8 | `analysis/outputs/cards/personas-kmeans.json data_properties` |
| personas-kmeans: Best mean silhouette | 0.2915 | `analysis/outputs/cards/personas-kmeans.json data_properties` |
| personas-kmeans: Largest persona | Mixed sector, small, server (2003 incidents) | `analysis/outputs/cards/personas-kmeans.json data_properties` |

## Interpretation

| Fact | Value | Source |
| --- | --- | --- |
| mlr-impact: r2_business | 0.3543 | `analysis/outputs/cards/mlr-impact.json results.key_numbers.r2_business` |
| mlr-impact: skew_records_lost | 50.57 | `analysis/outputs/cards/mlr-impact.json results.key_numbers.skew_records_lost` |
| mlr-impact: ks_d_lognormal | 0.0914 | `analysis/outputs/cards/mlr-impact.json results.key_numbers.ks_d_lognormal` |
| mlr-impact: ks_d_normal | 0.4858 | `analysis/outputs/cards/mlr-impact.json results.key_numbers.ks_d_normal` |
| mlr-impact: adj_r2_business | 0.3514 | `analysis/outputs/cards/mlr-impact.json results.key_numbers.adj_r2_business` |
| mlr-impact: test_rmse_business | 1.657 | `analysis/outputs/cards/mlr-impact.json results.key_numbers.test_rmse_business` |
| mlr-impact: test_rmse_full | 1.564 | `analysis/outputs/cards/mlr-impact.json results.key_numbers.test_rmse_full` |
| mlr-impact: per_record_cost_inr | 6456 | `analysis/outputs/cards/mlr-impact.json results.key_numbers.per_record_cost_inr` |
| breach-classifiers: best_model | decision_tree | `analysis/outputs/cards/breach-classifiers.json results.key_numbers.best_model` |
| breach-classifiers: youden_j | 0.5549 | `analysis/outputs/cards/breach-classifiers.json results.key_numbers.youden_j` |
| breach-classifiers: best_cv_auc | 0.8263 | `analysis/outputs/cards/breach-classifiers.json results.key_numbers.best_cv_auc` |
| breach-classifiers: youden_threshold | 0.4425 | `analysis/outputs/cards/breach-classifiers.json results.key_numbers.youden_threshold` |
| breach-classifiers: k_knn | 2 | `analysis/outputs/cards/breach-classifiers.json results.key_numbers.k_knn` |
| breach-classifiers: tree_depth | 10 | `analysis/outputs/cards/breach-classifiers.json results.key_numbers.tree_depth` |
| breach-classifiers: tree_min_leaf | 20 | `analysis/outputs/cards/breach-classifiers.json results.key_numbers.tree_min_leaf` |
| attack-likelihood: auc_hacking | 0.8652 | `analysis/outputs/cards/attack-likelihood.json results.key_numbers.auc_hacking` |
| attack-likelihood: auc_malware | 0.84 | `analysis/outputs/cards/attack-likelihood.json results.key_numbers.auc_malware` |
| attack-likelihood: auc_social | 0.738 | `analysis/outputs/cards/attack-likelihood.json results.key_numbers.auc_social` |
| attack-likelihood: auc_error | 0.741 | `analysis/outputs/cards/attack-likelihood.json results.key_numbers.auc_error` |
| attack-likelihood: auc_misuse | 0.6899 | `analysis/outputs/cards/attack-likelihood.json results.key_numbers.auc_misuse` |
| attack-likelihood: auc_physical | 0.8922 | `analysis/outputs/cards/attack-likelihood.json results.key_numbers.auc_physical` |
| pca: features | 37 | `analysis/outputs/cards/pca.json results.key_numbers.features` |
| pca: kaiser | 12 | `analysis/outputs/cards/pca.json results.key_numbers.kaiser` |
| pca: n80 | 14 | `analysis/outputs/cards/pca.json results.key_numbers.n80` |
| pca: pc1_var | 0.1788 | `analysis/outputs/cards/pca.json results.key_numbers.pc1_var` |
| pca: pc2_var | 0.1075 | `analysis/outputs/cards/pca.json results.key_numbers.pc2_var` |
| personas-kmeans: k | 8 | `analysis/outputs/cards/personas-kmeans.json results.key_numbers.k` |
| personas-kmeans: silhouette | 0.2915 | `analysis/outputs/cards/personas-kmeans.json results.key_numbers.silhouette` |
| personas-kmeans: n_persona_0 | 861 | `analysis/outputs/cards/personas-kmeans.json results.key_numbers.n_persona_0` |
| personas-kmeans: n_persona_1 | 1734 | `analysis/outputs/cards/personas-kmeans.json results.key_numbers.n_persona_1` |
| personas-kmeans: n_persona_2 | 645 | `analysis/outputs/cards/personas-kmeans.json results.key_numbers.n_persona_2` |
| personas-kmeans: n_persona_3 | 2003 | `analysis/outputs/cards/personas-kmeans.json results.key_numbers.n_persona_3` |
| personas-kmeans: n_persona_4 | 1798 | `analysis/outputs/cards/personas-kmeans.json results.key_numbers.n_persona_4` |
| personas-kmeans: n_persona_5 | 1267 | `analysis/outputs/cards/personas-kmeans.json results.key_numbers.n_persona_5` |
| personas-kmeans: n_persona_6 | 1149 | `analysis/outputs/cards/personas-kmeans.json results.key_numbers.n_persona_6` |
| personas-kmeans: n_persona_7 | 1139 | `analysis/outputs/cards/personas-kmeans.json results.key_numbers.n_persona_7` |
| hierarchical: ari | 0.4392 | `analysis/outputs/cards/hierarchical.json results.key_numbers.ari` |
| hierarchical: k | 8 | `analysis/outputs/cards/hierarchical.json results.key_numbers.k` |
| hierarchical: sample | 500 | `analysis/outputs/cards/hierarchical.json results.key_numbers.sample` |
| factor-analysis: kmo | 0.7331 | `analysis/outputs/cards/factor-analysis.json results.key_numbers.kmo` |
| factor-analysis: bartlett_p | 0 | `analysis/outputs/cards/factor-analysis.json results.key_numbers.bartlett_p` |
| factor-analysis: factors | 2 | `analysis/outputs/cards/factor-analysis.json results.key_numbers.factors` |
| factor-analysis: states | 36 | `analysis/outputs/cards/factor-analysis.json results.key_numbers.states` |

## Findings

| Fact | Value | Source |
| --- | --- | --- |
| expected-loss: annual_incident_prob | 0.468 | `analysis/outputs/cards/expected-loss.json results.key_numbers.annual_incident_prob` |
| expected-loss: per_record_cost_inr | 6456 | `analysis/outputs/cards/expected-loss.json results.key_numbers.per_record_cost_inr` |
| expected-loss: ref_total_0 | 1.495e+06 | `analysis/outputs/cards/expected-loss.json results.key_numbers.ref_total_0` |
| expected-loss: ref_total_1 | 3.35e+06 | `analysis/outputs/cards/expected-loss.json results.key_numbers.ref_total_1` |
| expected-loss: ref_total_2 | 1.066e+06 | `analysis/outputs/cards/expected-loss.json results.key_numbers.ref_total_2` |
| expected-loss: ref_total_3 | 3.858e+08 | `analysis/outputs/cards/expected-loss.json results.key_numbers.ref_total_3` |
| expected-loss: ref_total_4 | 1.254e+07 | `analysis/outputs/cards/expected-loss.json results.key_numbers.ref_total_4` |
| budget-optimiser: controls_scored | 4 | `analysis/outputs/cards/budget-optimiser.json results.key_numbers.controls_scored` |
| budget-optimiser: reference_budget_inr | 50000 | `analysis/outputs/cards/budget-optimiser.json results.key_numbers.reference_budget_inr` |
| budget-optimiser: max_gap_pct | 0 | `analysis/outputs/cards/budget-optimiser.json results.key_numbers.max_gap_pct` |

## Conclusions

| Fact | Value | Source |
| --- | --- | --- |
| coverage-hit-rate: n_test | 3105 | `analysis/outputs/cards/coverage-hit-rate.json results.key_numbers.n_test` |
| coverage-hit-rate: hit_rate | 0.2087 | `analysis/outputs/cards/coverage-hit-rate.json results.key_numbers.hit_rate` |
| coverage-hit-rate: baseline_hit_rate | 0.2087 | `analysis/outputs/cards/coverage-hit-rate.json results.key_numbers.baseline_hit_rate` |
| coverage-hit-rate: z | 0 | `analysis/outputs/cards/coverage-hit-rate.json results.key_numbers.z` |
| coverage-hit-rate: p_value | 1 | `analysis/outputs/cards/coverage-hit-rate.json results.key_numbers.p_value` |
| coverage-hit-rate: cohens_h | 0 | `analysis/outputs/cards/coverage-hit-rate.json results.key_numbers.cohens_h` |
| case-replay: cases | 4 | `analysis/outputs/cards/case-replay.json results.key_numbers.cases` |
| case-replay: assessable | 3 | `analysis/outputs/cards/case-replay.json results.key_numbers.assessable` |
| case-replay: covered | 3 | `analysis/outputs/cards/case-replay.json results.key_numbers.covered` |
| case-replay: budget_inr | 50000 | `analysis/outputs/cards/case-replay.json results.key_numbers.budget_inr` |
| sensitivity: scenarios | 24 | `analysis/outputs/cards/sensitivity.json results.key_numbers.scenarios` |
| sensitivity: order_changes | 0 | `analysis/outputs/cards/sensitivity.json results.key_numbers.order_changes` |
| sensitivity: set_changes | 0 | `analysis/outputs/cards/sensitivity.json results.key_numbers.set_changes` |
