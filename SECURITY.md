# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| `main` branch and the site deployed from it | Yes |
| Older commits and forks | No |

## Reporting a vulnerability

Please report privately through GitHub: open the repository's **Security** tab and choose **Report a vulnerability** (private vulnerability reporting). Do not open a public issue for security problems.

Include what you found, the page or file affected, steps to reproduce and the impact you expect. You should get an acknowledgement within 7 days and a fix or a decision within 30 days. Credit is given in the fix commit unless you ask otherwise.

## Scope

In scope:

- The static website in `web/`: content security policy and headers, handling of data in browser storage, rendering of model cards and formulas.
- The build and CI pipeline: GitHub Actions workflow, dependency pins and lockfiles.
- The analysis pipeline in `analysis/`: dataset download and verification, PDF parsing, exported model files in `web/public/model/`.
- Integrity problems, such as a number on the site that does not match its recorded source.

Out of scope:

- Denial of service against Vercel or GitHub infrastructure.
- Findings that need a compromised device or browser extension.
- Third-party data sources themselves (VCDB, NCRB, cited publishers); report those to their owners.
- The accuracy of published figures CyCRS cites; please report these as normal issues.

CyCRS has no accounts, server or database, so there is no personal data on a server to expose. See `THREAT_MODEL.md` for the full model.
