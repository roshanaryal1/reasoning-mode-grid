# Where to submit, and how long it takes

Researched 2026-10-01. Dates marked *projected* follow the previous cycle and are not
yet confirmed. **Re-check every date on the official call for papers before you plan
around it.**

**Superseded 2026-10-27:** the venue is TMLR, then a named preprint on Preprints.org; the
workshop version is deferred and arXiv and the NeurIPS extension are dropped. See
[paper-plan.md](paper-plan.md). The research below is kept as the record of the original plan.

## The short answer

1. **arXiv preprint** as soon as the analysis is done (target: January 2027).
2. **ICLR 2027 workshop**, 4-page short paper, non-archival (submit about 1 Feb 2027,
   decision by 26 Feb, present 29 to 30 April in San Francisco).
3. **TMLR**, the full archival version, submitted at the same time as the workshop
   paper (decision about 2 to 4 months later).
4. **Later, optional:** an extended version (second prompt, more families) for the
   NeurIPS 2027 Evaluations & Datasets track (projected deadline May 2027).

That gets you a public preprint in about 3 to 4 months, a workshop talk or poster in
about 7 months, and a peer-reviewed journal paper in about 5 to 7 months.

## When the paper can be ready

| Step | Earliest finish | Why |
|---|---|---|
| Settings filled, API checks, pre-registration tagged | mid October 2026 | LA-P2 has a hard date on 15 Oct and competes for the same weeks |
| 60 chat captures | early November 2026 | 3 to 5 days of collection |
| Blind scoring (median of three raters) | early December 2026 | 1 to 2 weeks for the human rater, plus finding them; the two LLM raters take a day |
| Analysis and draft | late December 2026 to mid January 2027 | |

So the first realistic submission window is **January to February 2027**. Every venue
whose deadline falls before that is out.

## Deadlines already missed or too close

| Venue | Deadline | Why not |
|---|---|---|
| NeurIPS 2026 workshops (Dec 2026, Sydney) | suggested 29 Aug 2026 | Passed |
| ICLR 2027 main conference | 25 Sep 2026 | Passed |
| EACL 2027 (Athens, Mar 2027) | ARR 3 Aug 2026 | Passed |
| NAACL 2027 | ARR 12 Oct 2026 | No data by then |

## Options that fit, compared

| Venue | Type | Deadline | Decision | Published or presented | Fit |
|---|---|---|---|---|---|
| **ICLR 2027 workshops** | Workshop, usually non-archival | suggested about **1 Feb 2027** (each workshop sets its own) | by **26 Feb 2027** | 29 to 30 Apr 2027, San Francisco | **Best first venue.** 4-page format matches the paper. Non-archival leaves the journal route open |
| **TMLR** | Journal (JMLR family), rolling | **any time** | target about 9 weeks, 2022 median 76 days | on acceptance, OpenReview | **Best archival home.** Judges correctness and evidence, not hype, so a pre-registered result counts whichever way it goes |
| ACL 2027 via ARR | Archival conference, short paper (4 pages) | final ARR cycle **January 2027**, exact date TBA | about May 2027 | 17 to 22 Aug 2027, Kyoto | Strong NLP signal, but short papers are novelty-sensitive. Good alternative to TMLR |
| ICML 2027 | Archival conference | about 22 Jan 2027 *projected* | about May 2027 | Jul 2027 | Too big a venue for a 4-page grid study |
| COLM 2027 | Archival conference | **31 Mar 2027** | about Jul 2027 | 6 to 9 Oct 2027 | Good fit for the extended version, needs a full-length paper |
| NeurIPS 2027 Evaluations & Datasets | Archival track | about **May 2027** *projected* (2026: 6 May) | about Sep 2027 | Dec 2027 | Treats evaluation as research in its own right. Best home for the extended version |

## Why this plan

- **Workshop plus journal at the same time is allowed** when the workshop is
  non-archival. Check the specific workshop's call says "non-archival" before submitting.
- **TMLR over ACL short:** no deadline pressure, a reviewer bar that rewards rigour,
  and the same JMLR-family signal LA-P2 is aiming for. ACL short is the fallback if
  you want a conference talk in August.
- **Not ICML or COLM for this version:** a 4-page, 60-run study is a workshop or short
  paper. Save the big venues for the extended version, if the effect holds.

## Which ICLR 2027 workshop

The list of accepted workshops is announced on **29 November 2026**. Look for workshops
on LLM evaluation, reasoning or test-time compute, or trustworthy and reliable LLMs.
Pick the one whose call mentions evaluation methodology. Each workshop sets its own
deadline, page limit and archival policy.

## PhD application timing

From `llm-architects-planning/paper/venue-strategy.md`: CMU 18 Nov, HKPFS 1 Dec,
MBZUAI 15 Dec 2026. LA-P4 **will not have results** by those dates. In applications,
describe it as "pre-registered, data collection under way", with a link to the frozen
pre-registration. That is honest and still shows method. Do not rush the scoring to
hit an application date.

## Double-blind rules for every submission

- Use an anonymised copy of the repo (for example via anonymous.4open.science), not
  the GitHub link with your name.
- Cite LA-P1 in the third person ("Aryal (2026) found..."), not "our earlier work".
- Strip PDF author metadata after every export (`DECISIONS.md` in research-pipeline).
- Check whether the venue allows arXiv posting during review. TMLR and most ICLR
  workshops do. Check ARR's current policy before posting if you go the ACL route.

## Timeline at a glance

| Date | Event |
|---|---|
| mid Oct 2026 | Pre-registration tagged |
| Nov 2026 | Captures done, scoring under way |
| 29 Nov 2026 | ICLR 2027 workshops announced, pick one |
| Dec 2026 | Scoring and adjudication locked, analysis |
| Jan 2027 | Draft, arXiv preprint, submit to TMLR |
| about 1 Feb 2027 | Submit the 4-page version to the ICLR workshop |
| by 26 Feb 2027 | Workshop decision |
| Mar to Apr 2027 | TMLR decision (typical) |
| 29 to 30 Apr 2027 | Present at ICLR 2027 workshop, San Francisco |
| May 2027 | Optional: extended version to NeurIPS 2027 Evaluations & Datasets |

## Sources (checked 2026-10-01)

- ICLR 2027 workshop call: <https://iclr.cc/Conferences/2027/CallForWorkshops>
- ICLR 2027 dates: <https://mldeadlines.com/conference/iclr-2027/>
- TMLR reviewer guide (9-week target): <https://jmlr.org/tmlr/reviewer-guide.html>
- TMLR 2022 median time to decision: <https://x.com/thegautamkamath/status/1613959414486126598>
- ARR dates: <https://aclrollingreview.org/dates>
- ACL 2027: <https://www.opencurious.com/ai-conference-deadlines/acl-2027>
- EACL 2027: <https://2027.eacl.org/calls/papers/>
- COLM 2027 deadline: <https://x.com/COLM_conf/status/2000952053565415807>
- NeurIPS 2026 Evaluations & Datasets track: <https://blog.neurips.cc/2026/03/23/introducing-the-evaluations-datasets-track-at-neurips-2026/>
- NeurIPS 2026 workshop dates: <https://neurips.cc/Conferences/2026/CallForWorkshops>
- ICML 2027 (projected): <https://trybibby.com/conference-deadlines/icml-2027>
