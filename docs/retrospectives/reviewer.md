## 2026-05-09 — MN-006 Daily Digest Email Scheduler

**What went well:** HTML injection in RSS rendering was caught as a Warning and fixed before merge; Resend SDK surface (TypedDict) verified against source — `.get()` is correct.
**What went wrong:** The initial implementation lacked escaping on all external-data interpolations.
**Next time improvement:** Treat any f-string HTML template touching external network data as a mandatory HTML-escape audit item in breadth review.

## 2026-05-09 — MN-005 PWA Port + GH Pages Retirement

**What went well:** All ACs verified against implementation; tsc + build pass; binary icon copy verified; PwaRegister correctly uses useEffect with no SSR access.
**What went wrong:** `meta http-equiv="refresh"` is placed before `<meta charset="UTF-8">` — technically non-ideal (charset should be first) but functionally correct for ASCII redirect URL; no change warranted.
**Next time improvement:** For HTML redirect additions, note charset-first best practice in design doc; the functional risk is zero for ASCII-only redirect URLs so this is advisory only.

## 2026-05-03 — MN-002 Stock Signals Web Display

**What went well:** All 15 ACs verified traceable to implementation; git status clean; Python syntax check passed.
**What went wrong:** CJK strings in ticket/design .md (UI labels like "股票訊號") triggered the CJK sweep gate — these are intentional UI string literals cited in AC, not verbatim user quotes; gate rule needs a UI-label carve-out for new projects.
**Next time improvement:** When CJK hits in new .md files are only inline-code or quoted UI labels (not prose), classify as informational rather than block.
**Slowest step:** Tracing the signals-list hidden deviation from design doc §4.1 — confirmed intentional via git show on fix commit.
