# Scoring day: a checklist for the author

This is the practical side of runbook Phase 3. You run 120 LLM rating sessions (60 per LLM
rater) and collect one sheet from the human rater. You never score.

A practice run on 2026-10-15 pushed one answer through the real kit and `rater-rows`. It
shaped the advice below. Its scores were thrown away.

## Before the first session

- [ ] On the reviewed branch (or after the PR is merged), run `make preflight`, which
  includes checks, fresh packets, kits and the blinding audit. Its underlying commands are:

  ```bash
  modegrid blind --raters human llm-a llm-b
  modegrid rater-kit --raters human llm-a llm-b
  modegrid blinding-audit          # must end with "no leak probes hit"
  sha256sum -c data/scores/RATER_SHA256SUMS
  ```

- [ ] Copy `data/blinding/key.csv` somewhere outside the repo. Never send it to a rater.
- [ ] Keep the registered human rater identified as anonymous **H1** (2026-10-19).
  Do not publish their identity; add actual scoring dates when each rater finishes.
- [ ] Check that all three kits have 60 distinct blind IDs and no capture metadata or key.
  Manually verify the collection screenshots kept outside GitHub.
- [ ] Keep draft or AI-assisted preliminary scores strictly outside all independent-rater
  materials; do not prefill H1's sheet or show the drafts to the LLM raters.
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
2. Run `make results`. It runs agreement, consensus, unblind and the whole of Phase 4, and
   writes `results/report.md` with every number the Results section needs.
3. Commit the key with `git add -f data/blinding/key.csv`, then the sheets and `results/`.
4. Fill in `paper/results.md` from `results/report.md`.

## Pace

60 sessions at 5 to 15 minutes each is 5 to 15 hours per LLM rater. Two raters can run side
by side in different browser tabs, one chat per tab, as long as each chat holds one answer.
Spread it over several days if you like. The order within a rater does not matter for the
analysis, but keep to NN order so you never lose track.

## The rubric's leftover notes (settled 2026-10-15)

The vendored rubric still carries notes written for LA-P1: file paths, an "Anchor" bullet
that names a model, and a remark that names DeepSeek answers. Rater prompt rule 8 now tells
every rater to ignore those parts. The rubric file itself is unchanged. Recorded in the
Deviations table.
