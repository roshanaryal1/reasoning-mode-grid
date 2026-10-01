# Working with a co-author

## The one rule

**Whoever sees the captures cannot score them blind.** Every other decision follows
from that. The captures, the manifest and the blinding key all sit in this repo, so a
rater must not have repo access until scoring is locked.

## Recommended split

| Work | Lead author | Co-author |
|---|---|---|
| Design, hypotheses | Writes the draft | **Reviews before the freeze.** The best moment to catch a weak hypothesis |
| Mode registry, API checks | Does it | Spot-checks two families |
| 60 chat captures | Does all of them | Does not see them |
| Blinded packets, key | Builds them, holds the key | Receives the packet only |
| Scoring | Does not score | **Rater 1.** Recruits and briefs rater 2 |
| Adjudication | Not involved | With rater 2, while still blind |
| Unblind, analysis | Runs `modegrid analyze` | **Re-runs it independently** from a clean clone |
| Writing | Method, results, appendix | Related work, discussion |
| Final edit, submission | Together | Together |

Why this split works:

- Data collection and scoring are the two biggest jobs. One each.
- Blinding survives because the co-author never sees which model wrote what.
- The independent re-run of the analysis is a reproducibility check reviewers value.

### Alternative: share the collection

If the 60 chat runs are too much for one person, split them by family (3 families
each). Then **neither** author can score blind, and you need two outside raters. That
is harder to arrange, so use it only if collection is the bottleneck.

## Repository access

| When | Co-author access |
|---|---|
| Before captures start | Full access to review the design and pre-registration |
| From the first capture until scoring is locked | **No repo access.** Receives only `packets/answers/`, their score sheet, the rubric and `docs/scoring.md`, by email or a shared folder |
| After unblinding | Full access. Add as a GitHub collaborator (Settings, Collaborators) |

If the co-author already has access before captures start, remove it for the
collection and scoring window, or keep captures in a separate private repo until
unblinding. Record which option you used in the pre-registration Deviations table.

## Day-to-day workflow on GitHub

- One branch per task: `data/claude-chat-r1-r5`, `score/rater1`, `docs/related-work`.
- Pull requests into `main`. The other author reviews anything that touches
  `configs/`, `docs/preregistration.md` or `src/modegrid/analyze.py`.
- CI must pass before merge.
- Add the co-author to `.github/CODEOWNERS` once they have access, so their review is
  requested automatically.
- Decisions go in an issue, not a chat message, so the reasoning is on record.

## Agree in writing before starting

Put these in `AUTHORS.md` and both sign off in a pull request:

1. Author order, and what would change it.
2. Who does what, using the CRediT roles below.
3. Each author's affiliation. Do not apply one author's affiliation rule to the other.
4. Who is corresponding author.
5. What happens to the data and the paper if one author leaves.
6. Whether LLM raters are used, and that this will be disclosed.

## CRediT roles

| Role | Lead author | Co-author |
|---|---|---|
| Conceptualization | X | |
| Methodology | X | X |
| Software | X | |
| Investigation (data collection) | X | |
| Validation (blind scoring, independent re-analysis) | | X |
| Formal analysis | X | |
| Data curation | X | |
| Writing, original draft | X | X |
| Writing, review and editing | X | X |
| Project administration | X | |
