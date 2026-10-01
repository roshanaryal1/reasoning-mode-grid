# Pilot data (exploratory only)

The three DeepSeek captures that motivated LA-P4, copied unchanged from
`llm-architects@d5e39e7` `data/responses/`. Same base model (DeepSeek-V4-Pro), same
prompt (v1), three chat modes in the web app, captured 2026-08-31.

| Capture | Mode | Harmonised level | Adjudicated v1 total (of 18) |
|---|---|---|---|
| `deepseek-expert.md` | DeepThink / deep reasoning | reasoning | 8 |
| `deepseek-instant.md` | fast, non-thinking | fast | 9 |
| `deepseek-instant-deepthink.md` | Instant plus DeepThink toggle | exploratory | 6 |

Scores: `deepseek-v1-adjudicated.csv`, from `analysis/scoring/scores-adjudicated-2026-09-01.csv`.

## Read this before citing the pilot

- **The adjudicated totals do not show a reasoning advantage.** The reasoning capture
  scored 8, below the fast capture at 9. The upstream note in
  `analysis/deepseek-modes.md` describes the deep mode as scoring higher. The adjudicated
  CSV and that note disagree. Fix the upstream note or the CSV before LA-P1 is revised.
- On the original v1 fabrication audit the fast modes looked much worse. Most of those
  "fabrications" were later shown to be real post-cutoff releases. The mode story then
  rested on internal defects (recommend-then-forbid, memory oversubscription), and on
  D9 both the reasoning and fast captures scored 0.
- n = 1 per cell, one family, v1 rubric, web channel. It cannot separate a mode effect
  from run-to-run noise. That is the reason the grid exists.

These files are not part of the confirmatory analysis.
