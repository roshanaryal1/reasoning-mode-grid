# Contributing

This is a research repository with a pre-registered design. The rules below protect the
validity of the result. They matter more than code style.

## Ground rules

1. **Captures are verbatim and write-once.** Never edit a model's answer. Notes go in
   `## Run notes` with a date.
2. **The design is frozen after the `prereg-v1` tag.** Any change to `configs/grid.yaml`,
   the prompt, the rubric, or the analysis code that affects results needs a dated entry
   in the Deviations table of `docs/preregistration.md`, in the same pull request.
3. **Vendored files are read-only.** CI checks their hashes.
4. **Raters work blind.** Do not open captures, the manifest or the key while scoring.
   Never overwrite another rater's sheet.
5. **No secrets.** API keys live in `.env`, which git ignores.

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,providers]"
pre-commit install
make check
```

`make check` runs ruff (lint and format), mypy, pytest with coverage, the vendored hash
check and `modegrid validate`. CI runs the same on Python 3.10 to 3.13.

## Pull requests

- Branch from `main`: `capture/<family>-<batch>`, `score/<rater>`, `fix/<topic>`, `docs/<topic>`.
- Use [Conventional Commits](https://www.conventionalcommits.org/) style messages:
  `feat:`, `fix:`, `docs:`, `data:`, `test:`, `chore:`.
- Fill in the pull request template. Say whether the change affects results.
- Add a line to `CHANGELOG.md` under Unreleased.

## Adding a capture by hand (web channel)

```bash
modegrid new-capture <run_id>
# paste the answer verbatim
modegrid validate
git checkout -b capture/grok-r1
git add data/captures/<run_id>.md && git commit -m "data: capture <run_id>"
```
