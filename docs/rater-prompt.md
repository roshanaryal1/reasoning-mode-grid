# Rater prompt

Fixed instruction for every rating session, human or LLM. One answer per session: a new
chat (LLM) or a fresh reading (human) for each blind id, so no answer is scored against
another. `modegrid rater-kit` wraps this text, the rubric, `scoring.md`, the memory
checker and one blinded answer into a single file per answer. Do not edit this text once
scoring has started; a change needs a Deviations row.

LLM sessions: use a chat with memory, history and personal connectors switched off
(claude.ai incognito chat; ChatGPT temporary chat), live web search on, and a code tool
able to run Python (for the memory checker).

=== RATER PROMPT START ===

You are an independent rater in a blinded research study. You will score ONE answer that
an AI assistant wrote in reply to a fixed task: design a fully local autonomous AI
workstation on an Apple Mac mini M6 with 32 GB unified memory. You do not know which
assistant or which mode wrote it, and you must not try to find out. Judge only the text.

Below this prompt you get, in order: the scoring rubric, the scoring protocol, the memory
checker script `memory_budget.py`, and the answer to score (headed with its blind id,
for example `# B017`).

Rules:

1. Use the rubric's nine dimensions D1 to D9. Score each 0, 1 or 2. No blanks, no halves.
   Use the **v2 hard anchors** for D1, D7, D8 and D9; they override the v1 table.
2. Judge recency (D2) against the task's fixed date, 31 August 2026, not today.
3. D3 and D4: search the web for every tool, framework and model the answer recommends
   before you score them. A name you do not recognise is not a fabrication. Follow the
   protocol: resolves = real; cannot be found either way = UNRESOLVED, scores 1; search
   positively shows it does not exist, or a load-bearing attribute is wrong = 0.
4. D1: work out the set of models the answer keeps resident at the same time and run the
   memory checker on it, for example
   `python memory_budget.py --weights 19 2.5 --ctx 16384 --browser`. Then apply the v2
   anchor.
5. D9: first compare deliverable J ("what not to install") with the rest of the answer.
   Recommending something J forbids is an automatic 0.
6. An outright refusal (declines the task, recommends no models, tools or plan) scores 0
   on all nine dimensions.
7. Also guess which family wrote it (one of: claude, deepseek, gemini, gpt, grok, qwen)
   and which mode (fast or reasoning). Leave a guess blank if you have no idea. Guesses do
   not affect scores.

Work through the answer, do the searches and the memory check, then finish your reply
with exactly one fenced CSV block in this form and nothing after it:

```csv
blind_id,D1,D2,D3,D4,D5,D6,D7,D8,D9,guess_family,guess_mode,notes
B017,2,1,2,1,0,1,2,1,2,qwen,reasoning,"D1: checker 27.4 GB fits, 4 GB floor named; D3: all tools resolve (github.com/...); D4: 'X 14B' UNRESOLVED; ..."
```

Put the blind id from the answer's heading in the first column. Wrap `notes` in double
quotes and use no double quotes inside it. In `notes`, give one short reason per
dimension and the URLs you checked for D3 and D4.

=== RATER PROMPT END ===
