# Provenance of vendored files

Copied unchanged from [roshanaryal1/llm-architects](https://github.com/roshanaryal1/llm-architects)
at commit `d5e39e73680ed1dea0d9b99efb65c4783665cfe5`. Same author. Upstream licences apply:
code MIT, prompts and docs CC-BY-4.0.

| File | Upstream path | sha256 |
|---|---|---|
| `prompts/prompt-v1.md` | `prompts/prompt-v1.md` (frozen 2026-08-31) | `ba2acba8868b254a96897e0552dd62ccd00443bc6afd084df419ba37ba0370e0` |
| `docs/rubric.md` | `docs/rubric.md` (v1 table plus v2 hard anchors) | `515368bdf639e4a338425a47bc902d957d590f4d5aa9979e185e4d3a0f50c985` |
| `scripts/memory_budget.py` | `analysis/scripts/memory_budget.py` | `ebb13a82c62f6aab116958e9ea521e342adf59a45ce8d9a5ef1411ff0bd59991` |

Do not edit these files. CI checks the hashes. To take a newer upstream version, copy it,
update this table and the hash in `configs/grid.yaml`, and log it as a deviation in
`docs/preregistration.md` if the pre-registration is already frozen.
