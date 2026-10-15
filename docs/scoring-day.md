# Scoring day: a checklist for the author

This is the practical side of runbook Phase 3. You run 120 LLM rating sessions (60 per LLM
rater) and collect one sheet from the human rater. You never score.

A practice run on 2026-10-15 pushed one answer through the real kit and `rater-rows`. It
shaped the advice below. Its scores were thrown away.

## Before the first session

- [ ] Pull `main` and rebuild, so the packets carry every blinding fix:

  ```bash
  modegrid blind --raters human llm-a llm-b
  modegrid rater-kit --raters human llm-a llm-b
  modegrid blinding-audit          # must end with "no leak probes hit"
  sha256sum -c data/scores/RATER_SHA256SUMS
  ```

- [ ] Copy `data/blinding/key.csv` somewhere outside the repo. Never send it to a rater.
- [ ] Fill in `data/scores/raters.md`: the human rater's name, and leave the run dates for
  when you finish.
- [ ] Decide the open question at the bottom of this page (the rubric's leftover notes).
- [ ] Make three folders: `replies/llm-a/`, `replies/llm-b/` and somewhere to keep the human
  rater's sheet when it comes back.

## One LLM session, step by step

Each kit file is one session: `packets/kit/<rater>/NN_B###.md`, where NN is the reading
order (01 to 60) and B### is the answer's blind id. Go in NN order.

1. **Open a fresh chat.**
   - `llm-a`: claude.ai, Claude Opus 5.5, an incognito chat, connectors off, web search on.
   - `llm-b`: chatgpt.com, GPT-6, Thinking effort High, a temporary chat, web search on.

   Both need a tool that can run Python, for the memory checker.
2. **Give it the whole kit file.** It is about 8,000 to 9,000 words. Attaching the `.md` file
   is the safest way. If the app turns a paste into an attachment, that is fine. Add nothing
   of your own: no greeting, no hints, no "this one is from model X".
3. **Let it finish.** A good session searches the web for the tools and models and runs the
   memory checker. Expect 5 to 15 minutes. If it stops early or asks a question, reply only:
   "Please continue and finish with the CSV row."
4. **Save the reply** as `replies/<rater>/NN_B###.txt`, the same name as the kit file but
   ending in `.txt`. Copy the whole reply, or at least the fenced CSV block at the end.
5. **Close the chat.** Never score two answers in one chat.

## Collect after every batch

Run this after every 5 or 10 sessions. It checks each row and shows what is left:

```bash
modegrid rater-rows llm-a replies/llm-a/*.txt
```

It prints `llm-a: 12 of 60 scored` and the blind ids still to do. The rater's final sheet,
`data/scores/llm-a.csv`, appears only when all 60 are in.

### When it reports an error

The command names the bad file and saves nothing from that batch, so you can fix the file
and run the same command again.

| Message says | What happened | What to do |
|---|---|---|
| `D2='1.5', must be 0, 1 or 2` | A half point or a number outside 0 to 2 | Ask in the same chat: "Each score must be 0, 1 or 2. Please give the CSV row again." Save the new reply over the old file |
| `guess_family='openai'` | A guess outside the six names | Same: ask for the row again with a guess from the list, or blank |
| `14 columns, expected 13` | Notes with a comma but no quotes around them | Put double quotes around the notes field yourself. Change nothing else |
| `already scored with different values` | Two reply files for one answer | Keep the first, complete session. Delete the other file. Do not pick the score you prefer |
| `is not on this rater's sheet` | A reply saved under the wrong rater's folder | Move it to the right folder |

Quotes inside the notes (`"the "X" repo"`) are accepted, but one quote mark may be dropped
from the stored note. The scores are unaffected, and notes are not analysed.

## Things that will tempt you

- **Do not re-run an answer to get a different score.** One session per answer per rater.
  The only re-run is for a session that broke (no CSV row at all, or the chat crashed).
- **Do not edit a score**, even one that looks wrong to you. You are not blind. Disagreement
  between raters is what the median of three is for.
- **Do not tell a rater anything** about which family or mode wrote an answer, and do not
  answer their questions about it.
- **Do not open the captures or the key** while a rater is working, so nothing leaks into a
  chat by accident.

## The human rater

Send them `rater-kit-human.zip`: their kit files, the 60 answers, their score sheet, the
rubric, the scoring protocol, the memory checker and `human-rater-brief.md`. They fill in
`scoresheet-human.csv` and send it back. Save it as `data/scores/human.csv`, then:

```bash
modegrid validate      # says which row is wrong, if any
```

## When all three sheets are in

1. Record the first and last scoring date for each rater in `data/scores/raters.md`.
2. Run runbook Phase 3 steps 3 to 5: agreement, consensus, unblind, and commit the key with
   `git add -f`.
3. Tell me, and I can run Phase 4 and fill in the Results section.

## Pace

60 sessions at 5 to 15 minutes each is 5 to 15 hours per LLM rater. Two raters can run side
by side in different browser tabs, one chat per tab, as long as each chat holds one answer.
Spread it over several days if you like. The order within a rater does not matter for the
analysis, but keep to NN order so you never lose track.

## Open question for you: the rubric's leftover notes

The vendored rubric (`vendor/llm-architects/docs/rubric.md`, pinned by hash) still carries
notes written for LA-P1, and every kit file includes them:

- "score `claude-sonnet-5` like any other ... exclude it from cross-response means" names a
  model inside a blind study.
- "Raters missed two clear recommend-then-forbid contradictions (DeepSeek Docker / Ollama)"
  could prime a rater against answers that look like DeepSeek's.
- It says to record scores in `analysis/scoring/...md` and to run
  `analysis/scripts/memory_budget.py`, which do not match the kit. The rater prompt's own
  instructions (a CSV row, `python memory_budget.py`) are clear, so this is only confusing.

The rater prompt says the v2 anchors override the v1 table, but it does not tell raters to
ignore these notes. Two ways forward, both before any scoring:

- **Leave it.** Report it as a limitation. The blinding check measures any leak.
- **Add one line to the rater prompt**, for example: "Ignore the rubric's 'Notes for raters'
  bullets about LA-P1 files, the anchor model and earlier raters. Follow this prompt and the
  scoring protocol." That changes `docs/rater-prompt.md`, so it needs a Deviations row, new
  hashes in `data/scores/RATER_SHA256SUMS` and a kit rebuild. The vendored rubric itself
  stays unchanged.
