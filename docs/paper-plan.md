# Paper plan

## Target

- **Format:** short paper, 4 pages plus references and appendix.
- **Venue:** an LLM evaluation workshop (NeurIPS, ICLR, COLM or ACL workshops). Non-archival
  workshops let the full version go to a journal later.
- **Also:** arXiv preprint the day it is submission-ready. Zenodo DOI for the data release.
- **Re-verify every deadline on the official call for papers.** Do not rely on any date
  written in this repo.

## Dependencies

| Item | Why it matters | State |
|---|---|---|
| LA-P1 citable (Cureus or preprint) | LA-P4 reuses its prompt and rubric | Under review, cite the preprint and Zenodo DOI 10.5281/zenodo.22245991 |
| v2 rubric anchors | Scoring instrument | Done in llm-architects |
| LA-P2 finding on stale raters | Justifies mandatory web verification | Cite as in preparation if not yet public |

## What LA-P5 needs from this paper

LA-P5 (architecture-from-spec benchmark) is gated on proof that the rubric is portable.
From this study, report:

1. Inter-rater alpha per dimension on a grid that LA-P1 never saw.
2. Whether rater rankings of the 12 cells agree (Kendall's tau between raters).
3. Which dimensions showed no variance at all, since a benchmark cannot use them.

## Timeline

| Week | Work |
|---|---|
| 1 | Phase 1 of the runbook. Freeze the pre-registration |
| 2 | Collect 60 captures |
| 3 to 4 | Blind scoring by at least two raters |
| 5 | Adjudicate, unblind, analyse |
| 6 to 7 | Write, internal review, metadata strip, submit |

## Salami test

Passes. LA-P1 had one family with three modes and no replicates, and scored modes only
as a side note. This paper has a new crossed design, new data, a new statistic and
pre-registered hypotheses. The LA-P1 DeepSeek captures appear only as motivating pilot data.
