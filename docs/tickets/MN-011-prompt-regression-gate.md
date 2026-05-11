---
id: MN-011
title: Prompt regression gate — fixtures + CI check before merging prompt diffs
status: open
created: 2026-05-11
type: feature
priority: med
size: M
visual-delta: no
content-delta: no
qa-early-consultation: pending
supersedes: none
depends: MN-010 (uses NDJSON shape for fixture replay)
---

## Why

Prompt edits (`rationale_translate`, news synthesizer, signal narrative) currently go straight to prod cron — no offline check that the new prompt still produces the expected shape / bilingual rationale / sentiment polarity on known inputs. Article §評測層 calls this gap "Demo vs 產品" directly: without offline eval set + CI regression gate, every prompt diff is unverified before users see it.

Goal: every prompt change must pass `tests/prompts/<name>/fixtures.jsonl` replay before merge.

## Scope

### Fixture layout

```
tests/prompts/
├── rationale_translate/
│   ├── fixtures.jsonl     # one record per case
│   └── expected/<id>.json # expected output schema
├── news_synthesizer/
│   ├── fixtures.jsonl
│   └── expected/
└── signal_narrative/
    ├── fixtures.jsonl
    └── expected/
```

`fixtures.jsonl` record:
```json
{ "id": "case-001", "input": { ...prompt input vars... }, "tags": ["bilingual", "bearish"] }
```

`expected/<id>.json`:
```json
{ "schema": { "must_have": ["zh", "en"], "polarity": "bearish" }, "min_len_zh": 30 }
```

### Files touched

- `tests/prompts/run_regression.py` — load fixtures, call prompt, assert against expected schema (presence + structural rules, not exact match)
- `tests/prompts/rationale_translate/fixtures.jsonl` — 5–10 seed cases (existing prod runs anonymised)
- Same for `news_synthesizer/` + `signal_narrative/`
- `.github/workflows/prompt-regression.yml` — runs on PR touching `**/prompts/**.py` or `**/synthesizer.py` or `**/rationale_translate*.py`
- `pyproject.toml` / `requirements-dev.txt` — pytest + jsonschema

### Acceptance Criteria

1. `pytest tests/prompts/ -v` passes locally on current main.
2. Workflow runs on PRs that touch prompt files; blocks merge on regression.
3. Fixtures stored in repo (no live API call required for fixture creation — captured outputs).
4. Adding a new prompt site requires adding ≥3 fixtures (enforced by CI: `len(fixtures) >= 3` per prompt dir).
5. Failure output names the failing case ID + specific schema rule violated.

## Out of Scope

- LLM-as-judge / semantic similarity scoring — schema + length + presence checks only.
- Online A/B — Phase 2 ticket.
- Cost regression (token count drift) — handled by MN-010 NDJSON aggregation if needed.

## Notes

- Tactical TODO seed: `daily-diary.md` 260511 item #4.
- Related: juejin article `AI/fe-agent-runtime-system.md` §六層架構 §6 評測層 + §自檢清單 質量與證據.
- Depends on MN-010 trace shape — fixtures can be bootstrapped from production NDJSON once MN-010 ships.
