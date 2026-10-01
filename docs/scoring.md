# Scoring protocol

## What raters receive

- `packets/answers/B001.md` to `B060.md`: the final answers, with self-identification
  lines and vendor or model names masked as `[REDACTED]`.
- Their own score sheet `scoresheet-<rater>.csv`, in a reading order unique to them.
- The rubric: `vendor/llm-architects/docs/rubric.md`. Use the **v2 hard anchors** for D1,
  D7, D8 and D9.
- This file.

Raters never receive the key file, the captures, the manifest, or the reasoning traces.

## How to score

1. Score each answer on its own. Do not compare answers and adjust.
2. Fill D1 to D9 with 0, 1 or 2. No blanks, no halves.
3. **D3 and D4: web-verify before scoring.** Search for every tool, framework and model
   name the answer recommends. A name you do not recognise is not a fabrication.
   - Resolves to a real repo, model card or release: it is real.
   - Cannot be found either way: `UNRESOLVED`, scores as 1, not 0.
   - Search positively shows it does not exist, or a load-bearing attribute is wrong
     (wrong size, wrong architecture): 0.
   - Put the URL you checked against in the notes column.
4. **D1: run the memory checker** on the model set the answer keeps resident:

   ```bash
   python vendor/llm-architects/scripts/memory_budget.py --weights <gb> <gb> --ctx <n> --browser
   ```

5. **D9: mechanical check first.** Diff deliverable J ("what not to install") against the
   rest of the answer. Recommending something that J forbids is an automatic 0.
6. The prompt fixes the date as 31 August 2026. Judge recency (D2) against that date,
   not the day you score.
7. Fill `guess_family` and `guess_mode` with your best guess, or leave blank if you have
   no idea. This measures how well blinding held. It does not affect scores.

## LLM raters

An LLM may act as a rater if:

- It is disclosed in the paper, with model name and date.
- It gets the same packet and instructions as a human.
- It has live web search for D3 and D4. LA-P2 shows closed-book LLM raters flag real
  post-cutoff releases as fabricated.
- It is not from the same vendor as any family it scores, or its scores for its own
  vendor's family are reported separately.
- At least one rater is human.

## Agreement and adjudication

```bash
modegrid agreement data/scores/rater1.csv data/scores/rater2.csv
```

- Bar: Krippendorff's ordinal alpha of at least 0.667 per dimension (pre-registered).
- Every cell where raters differ goes to adjudication. Record each decision in
  `data/scores/adjudication-log.md` with the blind id, dimension, both scores, the final
  score and one line of reason. Adjudicate while still blind.
