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
- K-means on the 15 profile features (8 sector, 3 size, 4 asset) (unscaled 0/1, identity scaler saved): silhouette best at k 8 (0.29, moderate). Personas from 645 to 2003 incidents, e.g. Educational Services large server (hacking 0.83, malware 0.75), Public Administration large media (error 0.74).
- Ward on 500-row sample, cut k 8: ARI 0.44 vs K-means, partly stable; card says rough groupings.
- FA on NCRB: 8 crime heads as log10(1 + per lakh), 36 states. Bartlett p 1.3e-19, KMO 0.73 (middling). 2 factors (varimax): F1 stalking, fraud, cheating, blackmail (0.84 to 0.93); F2 cheating by personation, privacy, identity theft. Telangana highest on F1.
- Compat: factor_analyzer 0.5.1 passes force_all_finite to sklearn 1.9; src/segment.py patches its check_array to ensure_all_finite.

## Phase 6 (2026-10-14)
- Files: src/recommender.py, src/export_web.py, notebooks/06_recommendation_engine.py, tests/test_recommender.py (106 pass), fixtures/reference.json (copied to web/tests/fixtures), web/public/model/{model,sources,lineage,cards}.json + SCHEMA.md (largest 183 KB), figures 06_*.png, outputs/06_*.csv, cards expected-loss, budget-optimiser, coverage-hit-rate.
- Fix: VCDB incident_id is not unique (36 ids shared by 241 rows); added source_file key, re-ran 01/04; test split keyed on source_file (7246 train / 3105 test rows, no overlap). vcdb_clean now 55 cols.
- Engine: L_c = pi x p_c x I_c; control effect e_k scaled by coverage share s_kc (share of category-c training incidents with a mitigated token), L_c(S) = L_c x prod(1 - e_k s_kc). Only 4 of 12 controls scorable (MFA, backups, endpoint, email filtering); 8 listed as not scored with reason.
- Greedy vs exhaustive on 5 reference profiles: gap 0.00%.
- Hit rate on 3105 test incidents: 0.209 vs baseline 0.209 (Endpoint, MFA, backups), p 1.0; 100% of plans equal the baseline, so the test cannot show personalisation with 4 controls.
- ISSUE: rupee levels implausible for small businesses (small retail L0 INR 21.8 crore/yr; one malware incident priced 7.9x IBM India average breach). Cause: VCDB record counts and IBM per-record cost come from large organisations. Card says use rankings, not rupee level. Needs a decision before the web UI shows INR.

## Phase 7 (2026-10-14)
- Files: web/ Next 16.3.6 static export (TS 6.0.3 strict, Tailwind 4.3.3, Recharts 3.10.1, KaTeX 0.18.9, zod 4.6.5; all pinned exact, published before 2026-09-29), vercel.json headers, lib/{model,plan,schema,tex,profile,data,format,labels,budget,useStored,events}.ts, pages /, /assess, /results, error, not-found; CI web job.
- model.ts reproduces recommend() and full trace for 5 reference profiles to 1e-6 (relative); reference.json now built from the exported, rounded model.json.
- Answers to inputs: employees <=100 small, <=1000 medium, else large; devices>0 -> user_device, website or cloud -> server, UPI/online payments -> network, customer data -> media. City is display only.
- KaTeX only via server component Tex (throws in browser); results formulas with user numbers are plain mono text. localStorage read via useSyncExternalStore, every read zod-validated, invalid profile removed and redirected to /assess.
- Tests: vitest 31 pass (model, plan edges, zod tamper); Playwright 3 pass (wizard + every panel + budget + sensitivity; tampered storage; no profile).
- Compat: eslint 10 + eslint-plugin-react need settings.react.version (auto-detect calls removed API).
- Local node is v25; engines says 22.x (Vercel/CI use 22).

## Phase 8 (2026-10-14)
- Files: components/{ModelPage,LazyCardChart,CardChart,TableCharts,Pipeline,FunnelChart}.tsx, app/models/{page,[id]/page}.tsx (16 static ids, dynamicParams false), app/data, app/cases, lib/{modelData,profileSchema}.ts, tests/unit/modelpage.test.tsx, tests/e2e/pages.spec.ts. Python export now adds lineage.datasets and sources.cases.
- Tests: vitest 48 pass (every card renders 7 sections, formulas, feeds links); Playwright 26 pass (22 pages at 1440 and 390 px, no console errors, no horizontal scroll; 7 sections on all model pages; pipeline links every card).
- Screenshots: 44 PNGs in web/screenshots/ (gitignored, 17 MB): home, assess, results, models, model-<16 ids>, data, cases, each -1440 and -390.
- Lighthouse 13.5 local (mobile, gzip test server, 2 runs): / perf 88-97, /results 86, /models/mlr-impact 85-90; accessibility 100 and CLS 0 on all. Target 90 not consistently met for /results and model pages; re-measure on Vercel.
- Perf changes: client imports model.json only (no client zod parse; validated in build and tests), profile validation on zod/mini named imports (results chunk 377 KB -> 70 KB), Recharts lazy with fixed-height frames, KaTeX CSS only on /results and /models/[id], fonts display optional, results heading and disclaimer server-rendered.
- Fix: Next 16 static export on Windows writes RSC segment files as __next.x/__PAGE__.txt (backslash bug); local serve.mjs maps it, Linux builds unaffected.

## Phase 9 (2026-10-14)
- Files: notebooks/07_case_replay_sensitivity.py, src/{replay,sensitivity}.py, recommend(p_scale), tests/test_replay_sensitivity.py (113 pass), outputs/07_*.csv, figures/07_tornado.png, cards case-replay (17), sensitivity (18); web lib/cases.ts, /cases rebuilt, tests/unit/cases.test.ts (vitest 55 pass), Playwright 29 pass, 48 screenshots.
- Case replay at INR 50,000: AIIMS 2022, C-Edge 2024, Tata Technologies 2025 (all malware) covered by top 3 Endpoint protection, MFA, backups; Star Health 2024 not assessable (source does not state the method). Verdict uses VERIS variety/vector categories from load_vcdb, not hand mapping.
- Sensitivity, 3 largest personas (all Mixed sector: small, unknown, large; server): largest swings incident probability and per-record cost (tied, both linear x0.5/x1.5), smallest effectiveness. 0 of 24 scenarios change plan order or set; all 4 scorable controls stable. At INR 50,000 every scorable control is affordable, so stability is partly structural.
- Export: sources.cases carry model profile and actual_categories; cards.json now 18 cards. Fixed results disclaimer regex (/^d+_/ lost its backslash in Phase 8).

## Fixes after Phase 9 (2026-10-14)
- Breach target: no confidentiality section (Not coded) now counts as No (VERIS records it only when data is affected). Classifier set 8267 (7492 Yes, 775 No vs 87). Tree CV AUC 0.826 +/- 0.019 (was 0.766 +/- 0.039); NB specificity 0.52.
- Ransomware robustness row: without the 857 incidents dated 2023, share from 2020 is 22.2% vs 2.4% before (h 0.67, Holm reject); 2023 inflated it to 55.2%.
- Impact cap: I_c = min(records x cost per record, cap by size). Caps from UK Cyber security breaches survey 2025/2026 Table 4.1b (orgs with an outcome): small 95th pct GBP 14,440 (INR 18.2 lakh), medium 90th pct GBP 83,600 (INR 1.05 crore), x gbp_inr 125.9222 (RBI page fetched 2026-10-13). Fallback level 3_global_smb; large and unknown uncapped. Small retail reference L0 INR 21.8 crore -> 15.0 lakh/yr; all 6 categories capped, so small-profile risk ranking follows p_c only.
- Phishing training stays unscored; plain-language notes for every unscored control exported (controls[].effectiveness_note) and shown in the plan as "Not ranked yet".
- Checks: pytest 117, vitest 55, Playwright 29, 48 screenshots. Lighthouse still needs a Vercel deploy (TODO: connect repo, Root Directory web, run PageSpeed on /, /results, one model page).

## Phase 10 (2026-10-14)
- CI: jobs analysis (ruff, pytest), web (npm ci, verify, Playwright), security (gitleaks-action, Semgrep p/default+p/typescript+p/python with --error, pip-audit, Trivy fs HIGH/CRITICAL, npm audit). All actions pinned to commit SHAs (checkout v7.0.1, setup-python v7.0.0, setup-node v7.0.0, trivy-action v0.36.0, gitleaks-action v3.0.0); permissions contents: read; persist-credentials false; Dependabot cooldown 14 days.
- Local scans: gitleaks no leaks; pip-audit none; Trivy 0 HIGH/CRITICAL; Semgrep 15 findings -> 0 (cooldown, SHA pins, globals() in notebook find_root replaced; Tex.tsx dangerouslySetInnerHTML rule excluded, KaTeX build-time only, ESLint react/no-danger elsewhere).
- npm audit: next 16.3.6 high (GHSA-3w37-wq28-93x7, cache poisoning; server features, not used by static export) fixed by 16.3.8. 5 high remain, dev-only braces chain via eslint-config-next (GHSA-vfj7-8cjw-p6xm, no patched version): accepted; CI blocks on --omit=dev (0 vulns) and reports full audit.
- Tests: web/tests/unit/headers.test.ts (vercel.json CSP equals CLAUDE.md directives, HSTS >= 1 year, nosniff, referrer, permissions); analysis/tests/test_repo_hygiene.py (no .env or key files tracked, .env.example empty, fixtures only in tests/, nothing demo or reference in public/). pytest 124, vitest 60, Playwright 29.
- Docs: THREAT_MODEL.md (STRIDE, why authz, rate limiting, SQL injection do not apply), SECURITY.md (private GitHub reporting, scope). Rupees: card text now uses Indian notation (₹18.18 lakh), /data shows rupee equivalents.
