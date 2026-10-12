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
     cannot be disabled, so the grid's Claude fast mode (Sonnet 5.5) is effort low.
2. **Fill the chat labels.** For each mode, write the exact app, model and switch you
   will select into `web_label` (for example "claude.ai, Sonnet 5.5, Effort High").
   Avoid "auto" model pickers, they can route to a different model.
   Open each app on the plan you will use and confirm the switch exists as labelled.
   Gemini matters most: on 2026-10-06 the app showed 3.6 Flash with an "Extended
   thinking" option, and an October update adds low, medium and high levels. Write the
   exact control names you see into `web_label`. If the control differs from the config,
   revise the mapping before the freeze. Turn off web search in every app; DeepSeek's
   Search toggle was on by default on 2026-10-06.
3. **Run the 12 API mode checks.** One API call per family and mode. This costs a few
   dollars in total and is the evidence that each switch does what you claim.

   ```bash
   modegrid run --dry-run       # lists only the 12 api_check runs
   modegrid run                 # needs the keys in .env for each vendor
   modegrid check-modes         # writes results/mode_check.md
   ```

   Every row should say "switch confirmed", except Claude, Gemini and Grok, which cannot
   disable reasoning and should say "lowest available" (fast uses fewer reasoning tokens,
   not zero). If a row says CHECK, fix the setting or drop the family before freezing.
   Copy the table into the mode registry.
4. **Freeze the pre-registration.** Read [preregistration.md](preregistration.md) end to
   end, change anything you disagree with now, then commit and tag:

   ```bash
   git tag -a prereg-v1 -m "LA-P4 pre-registration frozen"
   git push origin prereg-v1
   ```

   Optional but stronger: upload the same file to OSF Registries or AsPredicted and put
   the link in the file. A dated public registration is what reviewers trust.
5. **Regenerate the manifest** after the config is final: `modegrid plan`. Commit
   `data/manifest/runs.csv`.

Check: `modegrid validate` prints `ok`, `modegrid plan` reports no open placeholders,
and the `prereg-v1` tag exists.

## Phase 2. Collect the 60 chat captures (3 to 5 days)

All 60 scored runs happen in the vendors' chat apps. Work through
`data/manifest/runs.csv` in order (rows with `set` = `main`). The order is random on
purpose, so vendor-side changes during the week do not line up with one mode.

For each run:

```bash
modegrid new-capture claude__fast__p1-v1__r1
```

Then:

- Open a fresh chat. Signed in, no custom instructions, memory off, no files attached,
  web search off where the app allows it.
- Select exactly what the capture's `native_label` says.
- Paste the prompt text between the `=== PROMPT START ===` and `=== PROMPT END ===`
  lines of `vendor/llm-architects/prompts/prompt-v1.md`, and nothing else.
- If the model asks a question, reply only: "Please proceed with reasonable assumptions
  and state them." Note it in Run notes.
- Paste the final answer verbatim into the capture. If the app shows a thinking panel,
  paste it under the reasoning trace heading. Raters never see that section.
- Replace the `FILL IN` value in `model_returned` with the model name the app shows.
- Take a screenshot of the model and mode selector. Keep screenshots outside the repo,
  named by run id.

Tips that save time:

- Do one family per sitting, in manifest order. A family's 10 runs take about an hour.
- Finish each family inside 48 hours, so a silent vendor update cannot split it.
- `modegrid validate` catches a missing section or a leftover `FILL IN`.

Commit in small batches: `git commit -m "data: claude chat captures r1-r5"`.

Check: 60 main captures plus 12 API checks in `data/captures/`, and
`modegrid validate` prints `ok`.

## Phase 3. Score blind (1 to 2 weeks, the long pole)

1. Build the packets. Keep the key away from raters.

   ```bash
   modegrid blind --raters human llm-a llm-b
   ```

   Send the human rater the `packets/answers/` folder, their own score sheet, the rubric
   (`vendor/llm-architects/docs/rubric.md`, v2 anchors) and [scoring.md](scoring.md).
   Give each LLM rater the same packet and instructions, with web search on.
   Before any scoring, record in `data/scores/raters.md` which vendor, model id and run
   date are `llm-a` and `llm-b`. They must be two different vendors.
2. Raters score independently. The author does not score. D3 and D4 require web
   verification of every tool and model name. This rule exists because the LA-P1 anchor
   rater wrongly flagged 14 real post-cutoff tools as fabricated.
3. Collect sheets into `data/scores/human.csv`, `data/scores/llm-a.csv`,
   `data/scores/llm-b.csv` and check agreement:

   ```bash
   # all three raters (the pre-registered alpha)
   modegrid agreement data/scores/human.csv data/scores/llm-a.csv data/scores/llm-b.csv --out results/agreement.csv
   # human against each LLM (exact agreement is reported for the first two sheets)
   modegrid agreement data/scores/human.csv data/scores/llm-a.csv --out results/agreement-human-llm-a.csv
   modegrid agreement data/scores/human.csv data/scores/llm-b.csv --out results/agreement-human-llm-b.csv
   ```

   `results/agreement.csv` is also LA-P5's input: `specbench gate --alpha` reads it.

   Pre-registered bar: Krippendorff's ordinal alpha of at least 0.667 per dimension.
   A dimension below the bar is still reported, but its hypothesis test is labelled
   unreliable. Do not drop it and do not re-score until it passes.
4. Take the median of the three raters (no hand adjudication; the author is not blind):

   ```bash
   modegrid consensus data/scores/human.csv data/scores/llm-a.csv data/scores/llm-b.csv
   ```

   This writes `data/scores/adjudicated-blind.csv`.
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

Then the remaining pre-registered checks:

```bash
# Robustness check 3: the same analysis on each rater's raw scores
for r in human llm-a llm-b; do
  modegrid unblind data/scores/$r.csv --out data/scores/$r-unblinded.csv
  modegrid analyze --scores data/scores/$r-unblinded.csv --out results/$r
done

# Blinding-failure rate: did raters guess family or mode better than chance?
modegrid blinding-check data/scores/human.csv data/scores/llm-a.csv data/scores/llm-b.csv
```

For LA-P5, hand over `results/agreement.csv` and `results/variance_table.csv`:

```bash
specbench gate --alpha ../reasoning-mode-grid/results/agreement.csv \
               --variance ../reasoning-mode-grid/results/variance_table.csv
```

Then run the exploratory extras and label them as exploratory:

- The DeepSeek third mode (instant plus DeepThink toggle) from the pilot.
- Whether the rubric ranked cells the same way across raters (this is the LA-P5 gate).

## Phase 5. Write and submit (1 to 2 weeks)

Follow [paper-plan.md](paper-plan.md) and [`paper/outline.md`](../paper/outline.md).
Before submitting:

- Strip author metadata from the exported PDF and re-check after every re-export.
- Cite LA-P1 (Cureus, or its preprint) and state the relationship.
- Tag the data release: `git tag -a v1.0.0` and archive it on Zenodo for a DOI.
- Update the LA-P4 entry in `research-pipeline`.

## Cost control

- The 60 scored runs use the chat apps, so they cost only your subscriptions and time.
  Free tiers can hide the reasoning mode or cap usage, so check each app has the mode
  before you start.
- The 12 API checks cost a few dollars in total. The prompt is about 3,500 tokens and a
  long reasoning answer is about 15,000. Run Claude's 2 calls first and read the usage
  in the captures before running the rest.
- Never use server-side model fallbacks. A fallback answers from a different model.
