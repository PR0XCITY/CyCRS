# CyCRS threat model

CyCRS is a static website (Next.js export on Vercel) plus an offline Python analysis pipeline. There is no server-side code, no database, no user accounts and no network calls from the browser after the page loads. A visitor's answers stay in their own browser's localStorage.

## Why some usual controls do not apply

| Usual control | Why it does not apply | What replaces it |
| --- | --- | --- |
| Server-side authorisation | No server endpoints, no accounts, nothing to authorise | Static files only (no API routes, server actions or middleware, enforced by `output: export`); every visitor gets the same public files |
| Rate limiting | No API to abuse; pages are cached static files | Vercel CDN serves static assets; nothing per-request runs |
| SQL or NoSQL injection | No database and no queries | Model data is static JSON imported at build time; user input never leaves the browser |
| Session and CSRF protection | No sessions, cookies or forms that post anywhere | CSP `form-action 'self'` and `connect-src 'self'`; no cookies are set |

## STRIDE

| Area | STRIDE | Threat | Impact | Mitigation | Status |
| --- | --- | --- | --- | --- | --- |
| Static site | Spoofing | Look-alike site serves altered advice | Users act on false plans | HSTS (2 years, preload); single canonical Vercel domain | Done |
| Static site | Tampering | Third-party script injected or a page framed | Altered numbers, clickjacking | CSP `default-src 'self'`, `script-src 'self'`, no external scripts, fonts self-hosted, `frame-ancestors 'none'`; header test checks vercel.json against the required policy | Done |
| Static site | Info disclosure | Stack traces or console output leak internals | Reveals paths and versions | Friendly `error.tsx` and `not-found.tsx`; `removeConsole` in production; `poweredByHeader` off | Done |
| Static site | Denial of service | Traffic flood | Site unavailable | Static files on Vercel CDN; no origin server to exhaust | Accepted (platform) |
| Browser storage | Tampering | User or extension edits localStorage to inject values | Engine runs on crafted input, UI breaks | Every read validated with zod (`strictObject`, enums, ranges); invalid data removed and user sent to /assess; e2e test covers it | Done |
| Browser storage | Info disclosure | Shared computer reveals answers | Sector, size, city visible to next user | Only business-level answers stored, no personal or payment data; nothing sent off the device | Accepted, documented |
| KaTeX rendering | Tampering (XSS) | Formula HTML injected via `dangerouslySetInnerHTML` | Script execution | Only in `components/Tex.tsx`, server-rendered at build time from repo-controlled strings; `renderTex` throws in the browser; `trust: false`; ESLint `react/no-danger` blocks it elsewhere; user-number formulas are plain text | Done |
| Build pipeline | Tampering | Compromised GitHub Action or dependency | Malicious code in the build | Actions pinned to commit SHAs; `permissions: contents: read`; `persist-credentials: false`; exact npm and pip pins with lockfile; Dependabot with 14-day cooldown | Done |
| Build pipeline | Tampering | Vulnerable dependency | Known exploit in shipped code | CI: npm audit (production, blocking), pip-audit, Trivy fs, Semgrep p/default, p/typescript, p/python | Done |
| Build pipeline | Info disclosure | Secret committed | Credential leak | gitleaks pre-commit hook and CI job; `.env` gitignored; hygiene test fails if `.env` or key files are tracked | Done |
| Build pipeline | Elevation | Dev-only `braces` DoS (GHSA-vfj7-8cjw-p6xm, no patched version) via ESLint | Lint step hangs on hostile glob | Patterns are repo-controlled; not shipped to users; reported in CI | Accepted |
| Data supply chain | Tampering | VCDB or NCRB file altered upstream | Wrong statistics | Download by script, SHA-256 recorded in `datasets.csv`; VCDB pinned to a commit | Done |
| Data supply chain | Tampering | Malicious or malformed NCRB PDF | Parser exploit or silent wrong numbers | pdfplumber reads text only; extracted tables must pass 240 column-total, 396 row and rate, cross-table and spot checks or Phase 5 falls back to VCDB | Done |
| Data supply chain | Repudiation | External value cannot be traced to its source | Unverifiable advice | Every value has URL, publisher, year, access date and an excerpt of at most 25 words; pytest fails without them; MISSING values stay blank | Done |
| Data supply chain | Tampering | Instructions hidden in fetched pages or the VCDB clone | Analyst or AI assistant misled | Fetched content treated as data; only excerpts stored; third-party clone gitignored and excluded from scans | Done |
