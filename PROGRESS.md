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
