# Report asset map

| File | Report section | What it shows | Generated from |
| --- | --- | --- | --- |
| `figures/demo_assess_to_model_page.gif` | summary | Demo: assessment to results to model page | `docs/demo.gif` |
| `figures/screenshot_results_page.png` | summary | Results page for a small retail shop | `docs/screenshot-results.png` |
| `tables/tab_problem_ncrb_region_crime_mix.csv` | problem | problem ncrb region crime mix | `analysis/outputs/02_ncrb_region_crime_mix.csv` |
| `figures/fig_data_missing_values_heatmap.png` | data exploration | Missing or Unknown values across key variables | `analysis/figures/01_missing_heatmap.png` |
| `figures/fig_data_records_lost_skew_before_after_log.png` | data exploration | Records lost before and after log10(1 + x) | `analysis/figures/01_records_skewness.png` |
| `figures/fig_explore_action_categories.png` | data exploration | Incidents by action category | `analysis/figures/02_bar_action_categories.png` |
| `figures/fig_explore_actions_by_year.png` | data exploration | Action categories by incident year | `analysis/figures/02_line_actions_by_year.png` |
| `figures/fig_explore_actor_type_share.png` | data exploration | Share of incidents by actor type | `analysis/figures/02_pie_actor_type.png` |
| `figures/fig_explore_discovery_vs_records.png` | data exploration | Discovery time against records lost | `analysis/figures/02_scatter_discovery_records.png` |
| `figures/fig_explore_records_by_sector_box.png` | data exploration | Records lost by sector, top 8 | `analysis/figures/02_box_log_records_by_sector.png` |
| `figures/fig_explore_records_lost_histogram.png` | data exploration | Histogram of log records lost | `analysis/figures/02_hist_log_records.png` |
| `figures/fig_explore_sector_action_treemap.png` | data exploration | Sector by action category treemap | `analysis/figures/02_treemap_sector_action.png` |
| `figures/fig_explore_spearman_heatmap.png` | data exploration | Spearman correlation heatmap | `analysis/figures/02_spearman_heatmap.png` |
| `tables/tab_data_lineage_row_counts.csv` | data exploration | data lineage row counts | `analysis/outputs/01_lineage.csv` |
| `tables/tab_data_missing_values.csv` | data exploration | data missing values | `analysis/outputs/01_missing_values.csv` |
| `tables/tab_data_variable_types.csv` | data exploration | data variable types | `analysis/outputs/01_variable_types.csv` |
| `tables/tab_explore_summary_statistics.csv` | data exploration | explore summary statistics | `analysis/outputs/02_summary_stats.csv` |
| `figures/fig_classify_knn_elbow.png` | methodology | KNN cross-validated error by k | `analysis/figures/04_knn_elbow.png` |
| `figures/fig_explore_normal_vs_lognormal_qq.png` | methodology | QQ plots for normal and lognormal fits | `analysis/figures/02_qq_records.png` |
| `figures/fig_regression_residual_checks.png` | methodology | Residuals against fitted values and residual QQ plot | `analysis/figures/03_residual_checks.png` |
| `figures/fig_regression_residual_order.png` | methodology | Residuals in row order (Durbin-Watson) | `analysis/figures/03_residual_order.png` |
| `figures/fig_regression_vif.png` | methodology | Variance inflation factors | `analysis/figures/03_vif.png` |
| `figures/fig_segment_factor_analysis.png` | methodology | Factor analysis scree and loadings | `analysis/figures/05_fa.png` |
| `figures/fig_segment_kmeans_elbow_silhouette.png` | methodology | K-means elbow and silhouette | `analysis/figures/05_kmeans_scan.png` |
| `figures/fig_segment_pca_loadings.png` | methodology | PCA loadings heatmap | `analysis/figures/05_pca_loadings.png` |
| `figures/fig_segment_pca_scree.png` | methodology | PCA scree plot | `analysis/figures/05_pca_scree.png` |
| `figures/fig_segment_ward_dendrogram.png` | methodology | Ward dendrogram on 500 incidents | `analysis/figures/05_dendrogram.png` |
| `figures/screenshot_how_it_works.png` | methodology | How it works: model pipeline | `docs/screenshot-models.png` |
| `tables/tab_explore_distribution_fit.csv` | methodology | explore distribution fit | `analysis/outputs/02_distribution_fit.csv` |
| `tables/tab_regression_model_comparison.csv` | methodology | regression model comparison | `analysis/outputs/03_model_comparison.csv` |
| `tables/tab_regression_vif.csv` | methodology | regression vif | `analysis/outputs/03_vif.csv` |
| `figures/fig_classify_attack_type_roc.png` | interpretation | ROC curves for the attack-type models | `analysis/figures/04_roc_attack.png` |
| `figures/fig_classify_breach_confusion.png` | interpretation | Confusion matrices for the breach classifiers | `analysis/figures/04_confusion_breach.png` |
| `figures/fig_classify_breach_roc.png` | interpretation | ROC curves for the five breach classifiers | `analysis/figures/04_roc_breach.png` |
| `figures/fig_classify_decision_tree.png` | interpretation | Decision tree to depth 4 | `analysis/figures/04_tree.png` |
| `figures/fig_explore_conditional_probability.png` | interpretation | P(action category given sector) | `analysis/figures/02_conditional_probability.png` |
| `figures/fig_regression_slr_size.png` | interpretation | Simple regression of records lost on organisation size | `analysis/figures/03_slr.png` |
| `figures/fig_segment_factor_state_scores.png` | interpretation | State scores on the first factor | `analysis/figures/05_fa_state_scores.png` |
| `figures/fig_segment_pca_biplot.png` | interpretation | PCA biplot | `analysis/figures/05_pca_biplot.png` |
| `figures/fig_segment_persona_attack_mix.png` | interpretation | Attack mix of each persona | `analysis/figures/05_persona_attack_mix.png` |
| `tables/tab_classify_attack_type_odds_ratios.csv` | interpretation | classify attack type odds ratios | `analysis/outputs/04_attack_odds.csv` |
| `tables/tab_explore_conditional_probability.csv` | interpretation | explore conditional probability | `analysis/outputs/02_conditional_probability.csv` |
| `tables/tab_regression_coefficients_multipliers.csv` | interpretation | regression coefficients multipliers | `analysis/outputs/mlr_coefficients.csv` |
| `tables/tab_segment_factor_loadings.csv` | interpretation | segment factor loadings | `analysis/outputs/05_fa_loadings.csv` |
| `tables/tab_segment_personas.csv` | interpretation | segment personas | `analysis/outputs/05_personas.csv` |
| `figures/fig_decide_expected_loss_reference.png` | findings | Expected loss by attack type, reference profile | `analysis/figures/06_expected_loss_reference.png` |
| `figures/fig_evaluate_coverage_hit_rate.png` | findings | Coverage hit rate against baseline | `analysis/figures/06_hit_rate.png` |
| `tables/tab_classify_attack_type_auc.csv` | findings | classify attack type auc | `analysis/outputs/04_attack_auc.csv` |
| `tables/tab_classify_breach_comparison.csv` | findings | classify breach comparison | `analysis/outputs/classifier_comparison.csv` |
| `tables/tab_decide_greedy_vs_exhaustive.csv` | findings | decide greedy vs exhaustive | `analysis/outputs/06_greedy_vs_exhaustive.csv` |
| `tables/tab_evaluate_hit_rate_by_size.csv` | findings | evaluate hit rate by size | `analysis/outputs/06_hit_rate_by_size.csv` |
| `tables/tab_explore_hypothesis_tests.csv` | findings | explore hypothesis tests | `analysis/outputs/hypothesis_tests.csv` |
| `figures/fig_evaluate_sensitivity_tornado.png` | conclusions | Tornado chart for the three largest personas | `analysis/figures/07_tornado.png` |
| `tables/tab_evaluate_case_replay.csv` | conclusions | evaluate case replay | `analysis/outputs/07_case_replay.csv` |
| `tables/tab_evaluate_stable_controls.csv` | conclusions | evaluate stable controls | `analysis/outputs/07_stable_controls.csv` |
| `tables/tab_evaluate_tornado.csv` | conclusions | evaluate tornado | `analysis/outputs/07_tornado.csv` |
