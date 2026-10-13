# PROGRESS

## Phase 1 (2026-10-13)
- Files: repo scaffolding, CI (analysis job), pre-commit (gitleaks, ruff), dependabot; src/log.py, src/cards.py, src/fetch/{common,vcdb,naics}.py, src/load_vcdb.py, notebooks/01_data_preparation.py, tests (26 pass).
- Env: conda Python 3.11 at .venv (no system 3.11); jq installed into it.
- VCDB commit f6f98c0, 10596 validated files (549 use .JSON suffix, so loader matches suffix case-insensitively).
- NAICS 2-digit sector names fetched from Census 2022 code file (data/sources/naics_sectors.csv), not typed; codes 00, 43, 93, 99 map to Unknown.
- vcdb_clean.parquet: 10596 rows x 54 cols. Classifier set 7579 (Yes 7492, No 87). Regression set 5398.
- Records lost skewness 50.57 raw, 0.36 after log10(1 + x); IQR outliers 1144 raw, 9 log.
- Decisions: Unknown kept as a category; no imputation; VERIS "Small" (up to 1000) mapped to small; data_disclosure absent ("Not coded", 675) dropped from target like Potentially and Unknown.
- TODO: only 87 negatives (1.15%), so the breach classifier needs class weights and AUC, or a rethink of the target (e.g. treat Not coded integrity/availability-only incidents as 0). Decide before modelling.
- TODO: discovery_days known for only 1436 incidents.

## Phase 1B (2026-10-13)
- Files: src/fetch/ncrb.py, src/sources.py, config.yaml, data/sources/{values.csv,SOURCES.md}, data/raw/{controls.csv,cases.csv,ncrb/,sources/}, tests/test_{ncrb,sources}.py (60 pass).
- NCRB Crime in India 2024 (latest; only listed in the English site view), tables 9A.1-9A.3 downloaded by script. ncrb_state.csv 36 x 86 (28 states + 8 UTs). All checks pass: 240 column totals, 396 row/hierarchy/rate checks, cross-table totals, 3/3 spot checks. All-India 2024: 101928 cases, rate 7.3 per lakh.
- values.csv: IBM 2026 India INR 255M per breach, 39500 records (per-record INR 6456 derived in config); annual_incident_prob 0.468 (CPA Australia, India small business 2025, level 1); usd_inr 95.2477 (RBI/FBIL 2026-10-13).
- Effectiveness sourced: MFA 0.9922, endpoint 0.99, email filtering 0.999 (vendor), backups 0.60 (US proxy). Phishing training MISSING by design: 2025 RCT p=0.450 vs KnowBe4 vendor 86% drop; needs a decision.
- Controls: 8 of 12 costed (MFA, patching, endpoint, training, encryption free with page; backups 1560, email 32400, password manager 45719 INR/yr at 10 staff). Cases: 4 (Star Health 2024, AIIMS 2022, C-Edge 2024, Tata Technologies 2025).
- MISSING: effectiveness for patching, password manager, router, access reviews, encryption, UPI, IR plan; costs for router, access reviews, UPI, IR plan (staff-time controls, no price page). ASD Essential Eight site unreachable. 47 of 60 fetches used (user allowed +30).
- Pre-commit: gitleaks Go build fails (Go module proxy EOF) and GitHub release CDN blocked; hook switched to gitleaks-system, which needs gitleaks on PATH.

## Phase 2 (2026-10-13)
- Files: notebooks/02_descriptive_and_hypothesis.py, src/stats_tests.py, tests/test_stats_tests.py (71 pass total), 10 figures 02_*.png, outputs/hypothesis_tests.csv + 02_*.csv, cards descriptive, distribution-fit, conditional-probability, hypothesis-tests.
- Records lost: median 1364, mean 22.8M, skew 50.6, kurtosis 2936; log scale skew 0.36. Discovery days median 91 (n 1436). Spearman log discovery vs log records -0.04.
- Fit: KS D normal 0.486 vs lognormal 0.091 (sigma 5.03, scale 1329), so log scale downstream.
- Tests (Holm): reject for action vs size (V 0.18), action vs sector (V 0.25), internal vs external records (Mann-Whitney, r 0.52), ransomware share 2.4% before 2020 vs 55.2% from 2020 (h 1.36), NCRB crime mix by region (V 0.27), ANOVA discovery by sector (comparison only). Not rejected: Kruskal discovery by sector (p_holm 0.063), NCRB crime rate by region (ANOVA p 0.066, n 36).
- Decisions: primary action = single category or "multiple"; five regions are a CyCRS grouping (Chhattisgarh East, Madhya Pradesh West); employee count summarised on band codes 1 to 8.
- Caveat: 857 incidents dated 2023, 91% ransomware, so the ransomware rise may be a VCDB collection effect.
- Card ids referenced for later phases: attack-likelihood, breach-impact.
- Pre-commit: gitleaks 8.30.1 via system install; gitleaks-system hook needs pass_filenames: false.

## Phase 3 (2026-10-13)
- Files: notebooks/03_regression.py, src/regression.py, src/nbutil.py (shared notebook helpers), tests/test_regression.py + fixtures/regression/linear.csv (78 pass), figures 03_*.png, outputs/{03_vif,03_model_comparison,mlr_coefficients}.csv, outputs/models/mlr_impact.json, cards slr, mlr-impact.
- SLR log records ~ log10 employees (band geometric midpoint): slope -0.52 (x10 staff -> 30% records), R2 0.117, n 3693.
- MLR target log10(1+records), n 5398, split 3778/1620 stratified on target quintiles. Max VIF 9.4 (actor_internal), none dropped. Breusch-Pagan p 8.6e-48 -> HC3 for all models; JB p 9e-31; DW 1.98.
- Comparison (test RMSE / adj R2 / BIC): full 1.564 / 0.420 / 14515, backward (15 vars) 1.566 / 0.420 / 14424, business (sector, size, action) 1.657 / 0.351 / 14862.
- Decision: business model is used live because only it needs pre-attack inputs; costs 0.093 RMSE vs best. Missing discovery handled with log days = 0 plus disc_known flag in the full model only.
- Business multipliers: malware x5.92, hacking x3.08, misuse x0.04; Information sector x13.6, Public Administration x0.02; medium size x2.46.
- Card id referenced for later phases: decision.

## Phase 4 (2026-10-13)
- Files: notebooks/04_classification.py, src/classify.py, tests/test_classify.py (84 pass), figures 04_*.png, outputs/{classifier_comparison,04_attack_auc,04_attack_odds,04_breach_logit_odds}.csv, 04_tree_rules.txt, models/{attack_models,attack_test_ids}.json, cards breach-classifiers, attack-likelihood.
- Breach split train 5244 Yes / 61 No, test 2248 / 26. Dropped on train rows: action_environmental (0 cases), asset_network, sector_manufacturing (one class only).
- Leakage: asset_person dropped everywhere (VERIS codes a person asset in every social attack; social AUC was 0.999 with it, 0.738 without).
- CV AUC: tree 0.766 (depth 10, leaf 50), NB 0.743, logistic 0.730, LDA 0.723, KNN 0.563 (k 2). KNN, NB, LDA predict all Yes at 0.5 (specificity 0-0.08). Best = tree; Youden t 0.552, J 0.498 (spec 0.69 -> 0.81, recall 0.74 -> 0.69).
- Logit significant ORs: health care 5.35, large size 3.14, social 10.1; max |coef| 2.31 after fixes.
- Attack models (test AUC): physical 0.892, hacking 0.865, malware 0.840, error 0.741, social 0.738, misuse 0.690. Shared split 7252/3108 (stratified on first action); test incident ids saved for Phase 6.

## Phase 5 (2026-10-14)
- Files: notebooks/05_clustering_pca_fa.py, src/segment.py, tests/test_segment.py (90 pass), figures 05_*.png, outputs/05_*.csv, models/personas.json, cards pca, personas-kmeans, hierarchical, factor-analysis.
- PCA on 37 binary incident flags (standardised): Kaiser 12, 80% needs 14; PC1 17.9% (+hacking/+external), PC2 10.7%. Flags overlap but are not low-dimensional.
- K-means on the 13 profile features (unscaled 0/1, identity scaler saved): silhouette best at k 8 (0.29, moderate). Personas from 645 to 2003 incidents, e.g. Educational Services large server (hacking 0.83, malware 0.75), Public Administration large media (error 0.74).
- Ward on 500-row sample, cut k 8: ARI 0.44 vs K-means, partly stable; card says rough groupings.
- FA on NCRB: 8 crime heads as log10(1 + per lakh), 36 states. Bartlett p 1.3e-19, KMO 0.73 (middling). 2 factors (varimax): F1 stalking, fraud, cheating, blackmail (0.84 to 0.93); F2 cheating by personation, privacy, identity theft. Telangana highest on F1.
- Compat: factor_analyzer 0.5.1 passes force_all_finite to sklearn 1.9; src/segment.py patches its check_array to ensure_all_finite.
