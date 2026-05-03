## 2026-05-03 — MN-002 Stock Signals Web Display

**What went well:** All 15 ACs verified traceable to implementation; git status clean; Python syntax check passed.
**What went wrong:** CJK strings in ticket/design .md (UI labels like "股票訊號") triggered the CJK sweep gate — these are intentional UI string literals cited in AC, not verbatim user quotes; gate rule needs a UI-label carve-out for new projects.
**Next time improvement:** When CJK hits in new .md files are only inline-code or quoted UI labels (not prose), classify as informational rather than block.
**Slowest step:** Tracing the signals-list hidden deviation from design doc §4.1 — confirmed intentional via git show on fix commit.
