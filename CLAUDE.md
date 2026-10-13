# CyCRS
Cyber Security Control Recommendation System. One-line pitch: tells an Indian small business which cyber attacks it is most exposed to, which security controls to buy first for its budget in INR, and shows the statistics behind every number.

## Data (all public online sources, no primary data, no API keys)
- VCDB (github.com/vz-risk/VCDB), validated incident JSON. Main modelling dataset. Downloaded by script.
- NCRB Crime in India report (ncrb.gov.in), cyber crime chapter, state-wise tables. Official PDF downloaded by script and parsed with pdfplumber; if blocked, I place the PDF manually in analysis/data/raw/ncrb/.
- Every other external value (per-record breach cost, annual incident probability, control prices, control effectiveness, FX rate, Indian case studies) lives in analysis/data/sources/ and is collected from fetched web pages in Phase 1B.

## Stack
- analysis/: Python 3.11, pandas, numpy, scipy, statsmodels, scikit-learn, factor_analyzer, scikit-posthocs, matplotlib, seaborn, squarify, jupytext, pytest, ruff, requests, pdfplumber.
- web/: Next.js App Router static export, TypeScript strict, Tailwind, Recharts, KaTeX (rendered at build time), zod, vitest, Playwright. No backend: model parameters and model cards exported to web/public/model/*.json, inference in the browser.
- Infra: GitHub Actions, Vercel (Root Directory = web). No Docker.

## Code style
- No comments in code.
- One- or two-letter variable names, descriptive function names, clean spacing.
- No lambda functions in Python. In TypeScript use named function declarations; inline arrow callbacks only where React requires them.
- No unnecessary output or prints.
- Never use em dashes in any text, code, docs or UI copy.

## Analysis rules
- Every technique maps to the syllabus: descriptive stats, probability distributions, hypothesis tests, SLR, MLR, logistic regression, decision tree, KNN, Naive Bayes, LDA, ROC, confusion matrix, K-means, hierarchical clustering, PCA, FA.
- random_state=42. Stratified 70/30 split. statsmodels wherever p-value tables are needed.
- Figures to analysis/figures/ (PNG, dpi 200, titled, labelled axes). Tables to analysis/outputs/ (CSV).
- Analysis files are jupytext percent-format .py in analysis/notebooks/; "notebook X" means X.py. Convert to .ipynb only in Phase 11.
- Logging through analysis/src/log.py: JSON structured logs, no print-based logging.

## Explainability contract
Every model writes analysis/outputs/cards/<id>.json via src/cards.py with these keys:
- id, title, module (syllabus module number and name), stage (prepare, explore, impact, likelihood, segment, decide, evaluate), used_live (true if the website runs it on the user's profile), order (position in the pipeline)
- question: the business question it answers, one sentence
- data_in: dataset, n_rows, variables [{name, type, scale, transform}], prep_steps [string], sample_rows (8 real rows, seed 42, only the model's columns, never victim names or free text)
- why: 2 to 4 sentences linking measured data properties to the choice of model
- data_properties: [{name, value, implication}] e.g. skewness, class balance, normality p-value, KMO
- alternatives: at least 2 [{model, why_not}], each reason grounded in this data
- formula_tex: [{label, tex}] KaTeX strings for the core equations
- assumptions: [{check, statistic, p_value, verdict, action_taken}]
- results: {key_numbers {name: value}, tables [{title, columns, rows}], charts [{type, title, x_label, y_label, data}]}
- yields: 2 to 3 sentences in plain language on what the result tells a business owner and how CyCRS uses it
- feeds: ids of cards that consume this output
- limitations: [string]
Rules: every number in why, yields and data_properties is interpolated from computed values, never typed. Plain language a shop owner could follow, no jargon without a one-phrase gloss, no em dashes. Charts are exported as data for Recharts. tests/test_cards.py validates every card against this contract.

## Integrity
- Never fabricate data, prices, statistics or sources. A value enters the project only if read from a page fetched in this project, recorded with URL, publisher, year, access date and an excerpt of at most 25 words containing the value.
- Never fill a value from memory. If no source is found, leave it blank, mark it MISSING and tell me.
- Datasets are downloaded by scripts in analysis/src/fetch/ and recorded in analysis/data/sources/datasets.csv with URL, access date and SHA-256.
- Test data: small fixtures (max 20 rows or 5 files) only inside analysis/tests/fixtures and web/tests/fixtures. Never ship demo data or prefilled demo profiles in the app. Remove temporary demo data before a phase ends.

## Security
- Never commit secrets. .env.example committed, .env gitignored. gitleaks runs as a pre-commit hook.
- Validate every user input and everything read back from localStorage or URL params with zod. Invalid stored data is discarded, never trusted.
- No dangerouslySetInnerHTML except KaTeX output rendered at build time from repo-controlled strings. No eval, no external scripts. Fonts self-hosted via next/font; KaTeX CSS and fonts bundled from node_modules.
- Security headers in web/vercel.json: CSP (default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'), HSTS, X-Content-Type-Options nosniff, Referrer-Policy strict-origin-when-cross-origin, Permissions-Policy denying camera, microphone, geolocation.
- Users never see stack traces: friendly error.tsx and not-found pages. No console output in production builds.

## Deployment (Vercel)
- Builds with zero Python. web/public/model/ is committed, never generated at build time, never gitignored.
- web/ is self-contained. next.config: output 'export', images unoptimized, trailingSlash true.
- Static only: no API routes, route handlers, server actions, middleware, cookies(), headers(). Dynamic segments only with generateStaticParams and dynamicParams = false.
- Pages using localStorage or URL params are client components; useSearchParams wrapped in Suspense.
- Model JSON loaded via static imports. Each JSON under 2 MB, floats rounded to 8 decimals.
- package.json: "engines": {"node": "22.x"}, package-lock.json committed, test tools in devDependencies, build script is "next build".
- File names and import paths match case exactly.
- npm run verify = lint + tsc --noEmit + vitest run + next build.

## Phase completion
A phase is done only when:
1. Checks pass: ruff + pytest -q for analysis, npm run verify for web.
2. Changes are committed in 1 to 4 logical commits with conventional messages (feat:, fix:, test:, docs:, ci:, chore:) using my configured git identity.
3. At most 15 lines are appended to PROGRESS.md: files created, key numbers, decisions, open TODOs.
Never add Co-Authored-By or any Claude or Anthropic attribution anywhere. Never push. Never change commit dates.

## Token budget
- CLAUDE.md and PROGRESS.md are the only shared context. Do not re-read earlier phases' code unless editing it.
- Never print or read data in bulk: .shape, .head(5), single-column value_counts. Raw JSON via jq on a few files.
- Script output goes to analysis/logs/<phase>.log; read only the tail or grepped lines.
- grep or glob before reading; read large files by line range.
- Web research: at most 30 page fetches per phase, never re-fetch a recorded source, store excerpts not whole pages.
- Do not open images or screenshots unless something is broken.
- Replies: what changed and key numbers. No recaps.
