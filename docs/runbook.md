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
   Write the exact control names you see into `web_label`. If the control differs from
   the config, revise the mapping before the freeze. Turn off web search in every app:
   DeepSeek's "Smart Search" and AI Studio's "Grounding with Google Search" were both on
   by default. Gemini runs in Google AI Studio (aistudio.google.com), not the Gemini app:
   pick Gemini 3.8 Flash, set Thinking level to Low (fast) or High (reasoning), turn
   every tool off, leave temperature, output length and safety at their defaults, and
   use no system instructions. The app checks of 2026-10-13 are recorded in the mode
   registry.
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

All 60 scored runs happen in the vendors' chat apps. Capture one family at a time, taking
families in the order each first appears in `data/manifest/runs.csv` (rows with `set` =
`main`). Inside a family, follow the manifest order. That order is random on purpose, so
fast and reasoning runs are mixed and a vendor-side change mid-block does not line up
with one mode.

For each run, make the template right before you send the prompt (it stamps the time):

```bash
modegrid new-capture claude__fast__p1-v1__r1
```

If you end up sending the prompt later, set `date_run` to the real UTC time and add a
`date_note` saying why. Never edit `date_stamped`.

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
- **Refusal:** keep it. It is scored (0 on every dimension if it refuses outright).
- **Error, cut-off answer, or wrong model shown:** move the capture to
  `data/captures/superseded/` as `<run_id>.attempt1.md` (then `.attempt2.md`), so two
  failures of the same run never overwrite each other. Leave the `run_id` inside the file
  as it is. Add a line to that folder's README saying why, and run `new-capture` again for
  the same run id straight away, as the next capture in the same family block, before
  moving on in the manifest. Up to 2 replacements per cell for errors or
  cut-offs. A wrong model gets one replacement; if it happens again in that family, stop
  and record the family as dropped (preregistration section 7).

Tips that save time:

- Do one family per sitting. A family's 10 runs take about an hour.
- Finish each family inside 48 hours, so a silent vendor update cannot split it.
- `modegrid validate` catches a missing section or a leftover `FILL IN`.

Commit in small batches: `git commit -m "data: claude chat captures r1-r5"`.

Check: 60 main captures plus 12 API checks in `data/captures/`, and
`modegrid validate` prints `ok`.

## Phase 3. Score blind (1 to 2 weeks, the long pole)

1. Build the packets. Keep the key away from raters.

   ```bash
   modegrid blind --raters human llm-a llm-b
   modegrid rater-kit --raters human llm-a llm-b   # one file per answer
   modegrid blinding-audit                          # must print "no leak probes hit"
   ```

   The audit counts family fingerprints left in the packets, per cell, and writes
   `results/blinding_audit.csv`. A leak probe (app clutter, self-disclosure, a masked
   self-reference) must be zero before scoring starts. Style probes (the model's own
   habits) are reported, not removed. Commit the CSV: it records that blinding was checked
   before any scoring.

   Each LLM session gets one kit file (`packets/kit/<rater>/NN_B###.md`) in a new chat with
   memory and connectors off and web search on, and returns one CSV row. Save the replies to
   text files and collect them; the sheet reaches `data/scores/<rater>.csv` only when all 60
   rows are in:

   ```bash
   modegrid rater-rows llm-a replies/llm-a-*.txt
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
   git add -f data/blinding/key.csv   # gitignored until now, so it needs -f
   git add data/scores/
   ```

Check: `data/scores/adjudicated.csv` has 60 rows and `modegrid validate` prints `ok`.

## Phase 4. Analyse (1 day)

```bash
modegrid analyze --agreement results/agreement.csv --note "Confirmatory analysis, prereg-v1"
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

# Own-vendor scores (preregistration section 4): llm-a on claude, llm-b on gpt,
# against the other raters, relative to how each rates the other families
modegrid own-vendor data/scores/human-unblinded.csv data/scores/llm-a-unblinded.csv \
    data/scores/llm-b-unblinded.csv --out results/own_vendor.csv

# Blinding-failure rate: did raters guess family or mode better than chance?
modegrid blinding-check data/scores/human.csv data/scores/llm-a.csv data/scores/llm-b.csv

# Robustness check 4: split by fast-mode floor (true off vs lowest available)
modegrid analyze --families gpt,qwen,deepseek --out results/fast-off
modegrid analyze --families claude,gemini,grok --out results/fast-lowest
```

For LA-P5, hand over `results/agreement.csv` and `results/variance_table.csv`:

```bash
specbench gate --alpha ../reasoning-mode-grid/results/agreement.csv \
               --variance ../reasoning-mode-grid/results/variance_table.csv
```

Then run the exploratory extras and label them as exploratory:

- The DeepSeek third mode (instant plus DeepThink toggle) from the pilot.
- Whether the rubric ranked cells the same way across raters (this is the LA-P5 gate).
  Uses the per-rater unblinded sheets from robustness check 3:

  ```bash
  modegrid rank-agreement data/scores/human-unblinded.csv data/scores/llm-a-unblinded.csv \
      data/scores/llm-b-unblinded.csv --out results/cell_rank_agreement.csv
  ```

  It prints Kendall's tau-b for each pair of raters and Kendall's W across all three, for the
  total and each dimension, on the 12 cell means.

Figure 1 and its table view (cell means, fast vs reasoning, one line per family):

```bash
pip install -e ".[paper]"   # matplotlib, once
modegrid cells --figure figure1.pdf   # writes results/cell_means.csv and results/figure1.pdf
```

The PDF carries no creator, producer or date metadata, and the same scores give the same file.

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
