# Working alone: scorers and outside help

The study has one author (see [AUTHORS.md](../AUTHORS.md)). This file says how blind
scoring and independent checks work without a co-author.

## The one rule

**Whoever sees the captures cannot score them blind.** The author collects all 60 chat
captures, so the author never scores.

## Who does what

| Work | Who |
|---|---|
| Design, pre-registration, mode registry, API checks | Author |
| 60 chat captures | Author |
| Blinded packets and the key | Author builds them and holds the key |
| Scoring | Three blind scorers: one human who is not an author, and two LLMs from different vendors |
| Settling disagreements | Mechanical: the median of the three scores per answer and dimension (`modegrid consensus`). Nobody adjudicates by hand, so no one who has seen the captures touches a score |
| Unblind, analysis | Author runs `modegrid analyze` |
| Independent check of the analysis | Public: the data and code are released so anyone can re-run `modegrid analyze` and get the same table |
| Writing | Author |

## The human scorer

- Has a computing background and can web-search tool and model names.
- Gets only `packets/answers/`, their score sheet, the rubric and
  [scoring.md](scoring.md), by email or a shared folder. **Never** gets repo access,
  captures, the manifest or the key.
- Is thanked in the Acknowledgements with their permission. Not an author unless the
  agreement in AUTHORS.md applies.

## The LLM scorers

Rules from [scoring.md](scoring.md), "LLM raters":

- Named with model id and run date before scoring starts, in the pre-registration
  Deviations table if chosen after the freeze.
- Same packet and instructions as the human.
- Live web search for D3 and D4 (the LA-P2 stale-rater effect).
- Two different vendors. Scores an LLM gives to its own vendor's family are also reported
  separately.

## Repository access

The author does all the work in the repository. One observer also has access (added
while a co-authorship was being planned) and takes no part in collecting, scoring or
analysis. Because the observer can see the captures, the observer can never be a rater.
Nobody who scores is ever added as a collaborator.
