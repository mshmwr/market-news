## 2026-05-03 — MN-002

**What went well:** All BQs pre-resolved by PM before design start; boundary contracts for all three phases were straightforward to enumerate.
**What went wrong:** `ssot/system-overview.md` listed `ANTHROPIC_API_KEY` but `synthesizer.py` uses `GEMINI_API_KEY` — SSOT was stale from project init and would have caused a silent workflow failure if not caught at design time.
**Next time improvement:** At design start, cross-check every env var in `system-overview.md` against actual `.py` usage via grep before treating SSOT as authoritative.
**Slowest step:** Reading `synthesizer.py` to confirm the env var name mismatch — would have been caught faster with an upfront env var grep.
