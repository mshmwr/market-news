---
id: MN-010
title: Cron NDJSON telemetry — trace, cost, latency per LLM call
status: open
created: 2026-05-11
type: feature
priority: med
size: S
visual-delta: no
content-delta: no
qa-early-consultation: pending
supersedes: none
---

## Why

Current cron failures (e.g. 2026-05-10 14:21 rationale_translate three-strike `RemoteDisconnected` → 0 translations) leave only stderr log lines. No structured trace records per LLM call → "為什麼斷在這一檔" not answerable post-incident without re-running. Inspired by juejin Agent runtime article §可觀測層 — unified telemetry (OpenTelemetry GenAI semantics) across offline / online.

Goal: every NIM / LLM call inside cron writes one NDJSON line to `tools/market-news/traces/<date>.ndjson` with replayable fields.

## Scope

### Data shape

Each NDJSON line:

```json
{
  "ts": "2026-05-11T14:21:03Z",
  "trace_id": "<workflow-run-id>",
  "step": "rationale_translate",
  "batch_idx": 3,
  "tickers": ["AAPL", "MSFT", "GOOG", "META"],
  "model": "minimax-m2.7",
  "token_in": 1820,
  "token_out": 412,
  "cost_usd": 0.0034,
  "latency_ms": 8421,
  "outcome": "ok" | "error:<class>",
  "retry_attempt": 0
}
```

### Files touched

- `nim_client.py` (or wherever NIM HTTP call lives) — wrap call, emit NDJSON line on every outcome including retries
- New `telemetry.py` — `emit(event: dict)` writes to `tools/market-news/traces/<YYYY-MM-DD>.ndjson` (append mode)
- `digest.py` / `rationale_translate.py` / `synthesizer.py` — call `telemetry.emit(...)` at every LLM call site
- `.gitignore` — `tools/market-news/traces/` (do not commit; this is runtime telemetry not source)
- `.github/workflows/daily-digest.yml` — upload `traces/<date>.ndjson` as workflow artifact for 30 days

### Acceptance Criteria

1. Every NIM call produces ≥1 NDJSON line with all 11 fields above.
2. Retries logged separately (`retry_attempt: 1`, `2`, …) — not collapsed.
3. Failed runs still emit their `outcome: error:<class>` line before bubbling.
4. Workflow artifact attached on every cron run; downloadable from Actions UI.
5. No new env vars; no PII; no API keys in trace.

## Out of Scope

- Live dashboard / Grafana — local NDJSON + Actions artifact is Phase 1.
- Cross-cron correlation — `trace_id = workflow-run-id` is enough for now.
- Cost aggregation script (separate ticket if needed).

## Notes

- Tactical TODO seed: `daily-diary.md` 260511 item #4.
- Related: juejin article `AI/fe-agent-runtime-system.md` §六層架構 §5 可觀測層.
- Related: MN-008 (`max_workers=2` 救命) + 2026-05-10 cron rationale_translate fix established the failure mode this ticket addresses.
