# Pre-scoring readiness and handoff (LA-P4)

Updated 2026-10-24. Operational checklist only; **not** an amendment to the
frozen pre-registration (`prereg-v1`, 2026-10-13, OSF nj2zp).
Do not change the prompt, original captured answers, scoring rubric,
hypotheses or analysis decision rules during handoff preparation.

## Research status

- 60 primary chat answers: six families x two modes x five repeats.
- Twelve original API checks and four follow-ups on GPT-6 and Grok 4.7.
  GPT-6's follow-up confirmed its API switch; Grok 4.7's was inconclusive.
  API-check answers are never scored.
- Three independent raters: anonymous human H1 (registered 2026-10-19),
  Claude Opus 5.5 and GPT-6 High. No official sheets were committed
  at the time of this note.
- Qwen reasoning run r2 was restored from the original chat in PR #45.
  Do not re-send the prompt or change that answer.

## Gates before distributing any rating materials

1. Use a clean copy of the reviewed revision; this checklist does not
   authorise merging a pull request.
2. Run `make preflight`: lint, types, tests, frozen hashes, capture
   validation, packet and kit regeneration, and blinding audit. The
   command fails if a primary capture is missing or invalid or an
   existing blinding key would be remapped. Expect **60 blinded
   answers and 180 rater-kit files**.
3. The blinding audit must say **"no leak probes hit"**. Preserve
   observed style fingerprints as limitations.
4. Keep `data/blinding/key.csv` ignored until all official score
   sheets are final. Back it up outside the repo, securely. Never
   send it to a rater, commit it early, or post it in an issue/PR.
5. Inspect the dated model/mode-selector screenshots held outside
   GitHub. CI cannot verify the existence or accuracy of those files.
6. Verify each rater's sheet and kit has 60 distinct blind IDs and
   no source metadata or reasoning traces. Respect H1's anonymity.
7. Exclude exploratory pilot scores and any preliminary AI-assisted
   scores from all independent-rater materials; never prefill the
   human sheet or use them to tune raters.

## After all independent scores arrive

Collect 60 completed rows from each of the three raters, preserve
web-check URLs and memory-check notes as stipulated, then calculate
agreement and lock the median consensus before unblinding. Run
`make results`; fill Results, Discussion, figures and the final
release metadata. Apply the pre-registered H4 reliability, confidence
interval and direction rules regardless of whether the result
supports the paper's provisional title.
