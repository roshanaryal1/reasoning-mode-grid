# Brief for the human rater

Thank you for rating. This page tells you what the study needs from you and how to do it.
It adds no rules. Where it and `scoring.md` or the rubric seem to differ, they win.

## What you are doing

An AI assistant was asked to design a home AI workstation for one machine: an Apple Mac mini
with 32 GB of memory. You will read 60 of its answers and score each one on nine qualities.

You do not know which AI wrote an answer, or in which setting. That is on purpose. Please
judge only the text in front of you, and do not try to work out who wrote it.

## What is in your folder

| File | What it is |
|---|---|
| `answers/B001.md` to `B060.md` | The 60 answers, each with a blind id |
| `scoresheet-human.csv` | Your score sheet, in your own reading order |
| `rubric.md` | The nine qualities and what earns 0, 1 or 2 |
| `scoring.md` | The scoring rules |
| `memory_budget.py` | A small calculator for the memory check |
| `kit/` | The same answers, one file each with all the instructions attached, if you prefer that |

## How to score one answer

1. Take the next blind id from your score sheet, top to bottom.
2. Read the answer through once.
3. Give each of D1 to D9 a score of 0, 1 or 2. Whole numbers only.
4. Write one short reason per score in the notes column.
5. Guess which AI family wrote it (claude, deepseek, gemini, gpt, grok or qwen) and whether
   it was a fast or a reasoning setting. Leave the guess blank if you have no idea. Your
   guesses do not change any score. They tell us how well the blinding worked.

Score each answer on its own. Do not go back and adjust earlier scores after reading later
answers.

## The three checks that need care

**D1, memory.** Find the models the answer keeps loaded at the same time, then run the
calculator with their sizes, for example:

```bash
python memory_budget.py --weights 19 2.5 --ctx 16384
```

Use the v2 table in the rubric. A plan that adds up to exactly 32 GB with no spare memory
named is a 1, not a 2.

**D3 and D4, do the tools and models exist?** Search the web for each tool and model the
answer recommends before you score these two. Many are newer than you may know.

- Found it (a real repository, model card or release): it is real.
- Cannot find it either way: score 1, not 0.
- A search shows it does not exist, or a key detail is wrong (such as the wrong size): 0.

Put the links you checked in the notes.

**D9, does the answer contradict itself?** First compare its "what not to install" list
(deliverable J) with the rest of the answer. If it recommends something that list forbids,
D9 is 0.

## The fixed date

The task told the AI that today is 31 August 2026. Judge how current an answer is (D2)
against that date, not against the day you score.

## Time

Plan about 10 to 20 minutes per answer, more for the first few. Breaks are fine. You do not
need to finish in one sitting.

## When you finish

Send back `scoresheet-human.csv` with every row filled. Please do not share the answers or
your scores with anyone else in the study until all rating is done.
