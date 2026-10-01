# Security policy

## Supported versions

Only the latest commit on `main` is supported.

## Reporting

Email <roshanaryaal@gmail.com> with "SECURITY reasoning-mode-vs-model" in the subject.
Do not open a public issue. You will get a reply within 7 days.

## In scope

- Leaked credentials (API keys) anywhere in the history.
- The harness sending data to an endpoint other than the one configured.
- The blinding key or unblinded data reaching raters before scoring is locked.
- Embargoed content leaking while the paper is under double-blind review.

## Practices in this repo

- Keys only through environment variables. `.env` is git-ignored. `.env.example` holds
  names, never values.
- CI runs with read-only permissions and no secrets.
- GitHub secret scanning and push protection should be enabled in repository settings.
- Dependabot keeps GitHub Actions and Python dependencies current.
