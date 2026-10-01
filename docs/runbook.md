# Runbook: from today to a submitted paper

Follow the phases in order. Each one ends with a check you can run. Do not start a phase
until the previous check passes.

Time estimates assume one person working part time.

## Phase 0. Set up (1 hour)

1. Clone and install.

   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev,providers]"
   pre-commit install
   cp .env.example .env    # then fill in the keys you have
   ```

2. Prove the pipeline works with no spend.

   ```bash
   make check
   modegrid demo
   ```

   Check: `make check` is green and the demo prints a table marked SYNTHETIC.

## Phase 1. Lock the design (1 to 2 days)

This is the phase that decides whether the paper survives review. Take it slowly.

1. **Fill the mode registry.** For each family in `configs/grid.yaml`, open the vendor's
   current API docs and replace every `FILL-ME` and `VERIFY` value. For each one, write the
   doc URL and the date you read it into [mode-registry.md](mode-registry.md).
   - The model must be **one set of weights** that runs in both modes. If the only way to
     get a fast mode is a different model (Flash vs Pro, mini vs full), that family is out
     or needs a different model.
   - If a vendor no longer lets you turn reasoning fully off, use its lowest setting and
     record that. Claude's newest models are an example: on Opus 5.5 and Sonnet 5.5 thinking
     cannot be disabled, which is why the grid uses Sonnet 5.
2. **Smoke-test each API family with one call** before freezing. Use a throwaway prompt
   so no real cell is spent:

   ```bash
   modegrid run --family claude --limit 1 --dry-run
   ```

   Then make one real call per family and mode from a scratch script and confirm that
   the fast call returns no reasoning tokens and the reasoning call does. Record the
   usage numbers in the mode registry as evidence that the switch works.
3. **Freeze the pre-registration.** Read [preregistration.md](preregistration.md) end to
   end, change anything you disagree with now, then commit and tag:

   ```bash
   git tag -a prereg-v1 -m "LA-P4 pre-registration frozen"
   git push origin prereg-v1
   ```

   Optional but stronger: upload the same file to OSF Registries or AsPredicted and put
   the link in the file. A dated public registration is what reviewers trust.
4. **Regenerate the manifest** after the config is final: `modegrid plan`. Commit
   `data/manifest/runs.csv`.

Check: `modegrid validate` prints `ok`, `modegrid plan` reports no open placeholders,
and the `prereg-v1` tag exists.

## Phase 2. Collect the 60 captures (3 to 5 days)

Run in manifest order. The order is random on purpose, so vendor-side changes during the
week do not line up with one mode.

**API families** (Claude, GPT, Gemini, Qwen, DeepSeek):

```bash
modegrid run --dry-run        # list what will execute
modegrid run                  # executes every API run without a capture
modegrid validate
```

The command skips runs that already have a capture, so you can stop and restart it.
If a run ends with a finish reason other than a normal stop, the capture notes say so.
Do not delete it. Follow the exclusion rules in the pre-registration.

**Web families** (Grok Fast vs Expert):

```bash
modegrid new-capture grok__fast__p1-v1__r1
```

Then, for each web run:

- Open a fresh chat. Signed in, no custom instructions, memory off, no files attached.
- Select the mode named in the capture's `native_label`.
- Paste the prompt text between the `=== PROMPT START ===` and `=== PROMPT END ===`
  lines of `vendor/llm-architects/prompts/prompt-v1.md`, and nothing else.
- If the model asks a question, reply only: "Please proceed with reasonable assumptions
  and state them." Note it in Run notes.
- Paste the answer verbatim into the capture. Take a screenshot of the mode selector and
  keep it outside the repo.

Commit captures in small batches: `git commit -m "captures: claude r1-r5"`.

Check: 60 files in `data/captures/`, `modegrid validate` prints `ok`.

## Phase 3. Score blind (1 to 2 weeks, the long pole)

1. Build the packets. Keep the key away from raters.

   ```bash
   modegrid blind --raters rater1 rater2 rater3
   ```

   Send each rater the `packets/answers/` folder, their own score sheet, the rubric
   (`vendor/llm-architects/docs/rubric.md`, v2 anchors) and [scoring.md](scoring.md).
2. Raters score independently. At least two. D3 and D4 require web verification of every
   tool and model name. This rule exists because the LA-P1 anchor rater wrongly flagged
   14 real post-cutoff tools as fabricated.
3. Collect sheets into `data/scores/rater1.csv`, `data/scores/rater2.csv` and check
   agreement:

   ```bash
   modegrid agreement data/scores/rater1.csv data/scores/rater2.csv
   ```

   Pre-registered bar: Krippendorff's ordinal alpha of at least 0.667 per dimension.
   A dimension below the bar is still reported, but its hypothesis test is labelled
   unreliable. Do not drop it and do not re-score until it passes.
4. Adjudicate every disagreement listed in the queue. Write the decision and the reason
   in `data/scores/adjudication-log.md`. Save the final sheet as
   `data/scores/adjudicated-blind.csv`.
5. Unblind and commit the key now that scoring is locked:

   ```bash
   modegrid unblind data/scores/adjudicated-blind.csv
   git add data/blinding/key.csv data/scores/
   ```

Check: `data/scores/adjudicated.csv` has 60 rows and `modegrid validate` prints `ok`.

## Phase 4. Analyse (1 day)

```bash
modegrid analyze --note "Confirmatory analysis, prereg-v1"
```

This writes `results/variance_table.md` and `results/variance_table.csv`. Report every
dimension and every hypothesis, including the ones that fail. A clean "model > mode" on
the headline would still be a publishable result, because LA-P1 implied the opposite.

Then run the exploratory extras and label them as exploratory:

- The DeepSeek third mode (instant plus DeepThink toggle) from the pilot.
- Blinding-failure rate from the raters' `guess_family` and `guess_mode` columns.
- Whether the rubric ranked cells the same way across raters (this is the LA-P5 gate).

## Phase 5. Write and submit (1 to 2 weeks)

Follow [paper-plan.md](paper-plan.md) and [`paper/outline.md`](../paper/outline.md).
Before submitting:

- Strip author metadata from the exported PDF and re-check after every re-export.
- Cite LA-P1 (Cureus, or its preprint) and state the relationship.
- Tag the data release: `git tag -a v1.0.0` and archive it on Zenodo for a DOI.
- Update the LA-P4 entry in `research-pipeline`.

## Cost control

- Run one family end to end first (Claude, 10 runs) and look at the token usage in the
  captures before running the rest.
- The prompt is about 13 KB of input. Reasoning modes can produce long outputs. The
  `max_tokens` cap is 32,000 so answers are not cut off.
- Never use server-side model fallbacks. A fallback puts a different model in a cell.
