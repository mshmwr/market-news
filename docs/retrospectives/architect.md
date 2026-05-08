## 2026-05-09 — MN-004 Signals Display Port

**What went well:** Pre-Implementation Design Challenge Sheet all-5-accept with no blocking issues; component tree split (Server → Client boundary) was clearly specified and translated cleanly into implementation without revision.
**What went wrong:** TICKER_CATEGORY constant needed to live in `lib/constants.ts` for both MarketOverview and SignalFilters/SignalCard — design doc correctly specified this but the shared constant location could have been emphasized more clearly to prevent any ambiguity about which component owns the map.
**Next time improvement:** For tickets with multiple components sharing a static lookup table, explicitly state "must be in `lib/constants.ts`, not inline in component" in the Boundary Contracts section to make the canonical location unambiguous.

## 2026-05-09 — MN-003

**What went well:** Pre-Implementation Design Challenge Sheet caught build isolation and coexistence labeling risks before writing design doc; all ACs pre-resolved by PM.
**What went wrong:** Net-new directory creation (frontend/) made some refactorability checklist items (e.g., "replacement cost") less meaningful — no existing components to assess refactor cost.
**Next time improvement:** For net-new scaffold tickets with no existing code, Pre-Implementation Challenge Sheet should focus on build isolation + deploy config + coexistence contracts; defer component-level refactorability to first real feature ticket (e.g., MN-004).
**Slowest step:** Writing §1 Technical Option Analysis for three decisions (monorepo layout, rendering strategy, CSS framework) — could have been faster by focusing on PM's already-resolved scope (monorepo + Tailwind + default App Router) and providing only one alternative per decision instead of full 3-option spread.

## 2026-05-03 — MN-002

**What went well:** All BQs pre-resolved by PM before design start; boundary contracts for all three phases were straightforward to enumerate.
**What went wrong:** `ssot/system-overview.md` listed `ANTHROPIC_API_KEY` but `synthesizer.py` uses `GEMINI_API_KEY` — SSOT was stale from project init and would have caused a silent workflow failure if not caught at design time.
**Next time improvement:** At design start, cross-check every env var in `system-overview.md` against actual `.py` usage via grep before treating SSOT as authoritative.
**Slowest step:** Reading `synthesizer.py` to confirm the env var name mismatch — would have been caught faster with an upfront env var grep.
