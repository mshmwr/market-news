---
id: MN-012
title: Unified LLM runtime harness — chunk + retry + budget + snapshot
status: open
created: 2026-05-11
type: refactor
priority: low
size: M
visual-delta: no
content-delta: no
qa-early-consultation: pending
supersedes: none
depends: MN-010 (telemetry emission inside the harness)
---

## Why

Resilience patches are scattered across the codebase:
- `MN-008` learned `max_workers=2` rescues a stalling parallel call
- `2026-05-09 cron push race` added `git pull --rebase` 3-times retry
- `2026-05-10 rationale_translate` switched to 4-tickers-per-batch on `RemoteDisconnected`
- `nim_client.py` has ad-hoc `RemoteDisconnected` retry

Each LLM call site reimplements its own subset of "chunk + retry + log". Article §六層架構 §3 Runtime Harness states this should be a single layer that manages 步數 / 超時 / 預算 / 快照 / 重試 for every LLM call. Otherwise: cross-cron drift, missed retries on new sites, no budget enforcement.

Goal: single `llm_run(...)` entry point that every prompt call site uses.

## Scope

### Proposed API

```python
from llm_runtime import llm_run, RunConfig

result = llm_run(
    step="rationale_translate",
    prompt_fn=build_rationale_prompt,      # () -> str
    inputs=tickers,                         # list[T] — auto-chunked
    cfg=RunConfig(
        batch_size=4,
        max_retries=3,
        retry_classes=("RemoteDisconnected", "TimeoutError"),
        budget_usd=0.50,
        snapshot_dir="runs/<step>/<trace_id>/",
    ),
)
```

Behaviour:
- **Chunking:** split `inputs` into `batch_size`-sized batches; one LLM call per batch
- **Retry:** per-batch retry up to `max_retries` on listed exception classes; failed batches dropped (not whole run)
- **Budget:** stop and return partial results when running total `cost_usd` exceeds `budget_usd`
- **Snapshot:** write batch input + output to `snapshot_dir` before each call; enables replay on failure
- **Telemetry:** emit NDJSON via MN-010 `telemetry.emit(...)` at every batch outcome including retries

### Files touched

- New `llm_runtime.py` — implements `llm_run` + `RunConfig`
- `rationale_translate.py` — refactor to call `llm_run(step="rationale_translate", ...)`
- `synthesizer.py` — refactor
- `digest.py` — refactor any direct NIM calls
- `nim_client.py` — keep as low-level HTTP; remove retry logic (moved to harness)

### Acceptance Criteria

1. Existing cron behaviour preserved bit-for-bit on a captured set of inputs (regression via MN-011 fixtures).
2. Failed batch produces failed-batch NDJSON line + drops only its tickers (no whole-run abort).
3. Budget cap enforced — synthetic test with `budget_usd=0.001` returns ≤1 batch result.
4. Snapshot files present after run; can be loaded by `tests/prompts/run_regression.py`.
5. All three prompt call sites (`rationale_translate` / `synthesizer` / digest narrative) routed through `llm_run`.
6. `grep -r "RemoteDisconnected" --include="*.py"` returns only `llm_runtime.py` after migration.

## Out of Scope

- Step-level state machine (juejin article §Agent Loop) — overkill for single-call cron; revisit if cron grows multi-step.
- HITL approval injection — no high-risk LLM calls in cron yet (auto-execute fine).
- Async — project rule "No async" remains.

## Notes

- Tactical TODO seed: `daily-diary.md` 260511 item #4.
- Related: juejin article `AI/fe-agent-runtime-system.md` §六層架構 §3 Runtime Harness + §自檢清單 執行與韌性.
- Depends on MN-010 telemetry shape; MN-011 fixtures used for bit-for-bit regression check.
