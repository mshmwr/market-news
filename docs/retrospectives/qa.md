## 2026-05-09 — MN-004 Signals Display Port

**What went well:** QA Early Consultation (PM proxy) surfaced 5 supplementable challenges early — `matchMedia` SSR safety, filter state persistence across tab switches, and Invalid Date guard all became explicit ACs rather than post-deploy discoveries.
**What went wrong:** Vercel deploy-verification AC (confirm "每日市場新聞" in HTML body) cannot be verified immediately after merge due to Vercel build queue — same pattern as MN-003.
**Next time improvement:** For Vercel-deployed Next.js tickets, add an explicit "post-deploy probe" note in ticket Release Status that PM will poll until build completes; do not block branch cleanup on this.

## 2026-05-09 — MN-003

**What went well:** All locally-verifiable ACs passed; build verification (`npm run build` + tsc) is a clean, reproducible gate.
**What went wrong:** AC-SCAFFOLD-05 (Vercel 200 probe) could not be verified because Vercel project connection is a manual dashboard step — exposes a gap where a deploy-dependent AC has no automated fallback.
**Next time improvement:** For Vercel deploy ACs, split into two sub-ACs: (a) `vercel.json` structure validation (automatable — grep/read) and (b) live URL probe (manual post-deploy). This avoids a deferred AC blocking ticket close.
**Slowest step:** Waiting for Vercel deploy that never came up — 404 indicated the project was never connected.

## 2026-05-03 — MN-002

**What went well:** All 15 ACs passed first inspection; code inspection + py_compile fully replaced Playwright E2E for this plain-HTML project.
**What went wrong:** None — no regressions or boundary gaps found.
**Next time improvement:** For no-test-framework projects, document the code-inspection gate explicitly in CLAUDE.md so QA role handoff knows upfront there is no automated runner.
**Slowest step:** Reading index.html in full to trace all signals JS — split file by concern (CSS / HTML / JS) would accelerate future reviews.
