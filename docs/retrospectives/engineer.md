## 2026-05-04 — MN-031/032/033/034/035 Engineer

**What went well:** Five tickets shipped in one session — additive-only Pydantic fields (nullable defaults) meant old bundle JSON loaded without migration. Undervaluation + analyst rating fields flowed cleanly through models → synthesizer → frontend card.

**What went wrong:**
1. `git worktree remove` ran while CWD was inside the target worktree → `fatal: Unable to read current working directory`. Fix: always run worktree removal from repo root.
2. MN-032 worktree created before fetching latest `origin/main` → diverged HEAD required `git rebase origin/main`. Fix: fetch + merge origin/main on canonical checkout before every `git worktree add`.
3. Repeated from 2026-05-03: Edit on worktree copy without first Reading that worktree path → "file not read yet" guard hit again.

**Next time improvement:**
- `git worktree remove` must run from repo root — not from inside the target worktree.
- Before `git worktree add`: (1) `git fetch origin`, (2) `git merge origin/main --ff-only`, (3) `git worktree add ... origin/main`.

---

## 2026-05-03 — MN-002 Engineer

**What went well:** Design doc provided exact pseudo-code and CSS verbatim — zero ambiguity on implementation; `ssot/system-overview.md` was already updated in the branch by the Architect, so the SSOT update required no extra commit.

**What went wrong:** First Edit on `docs/index.html` hit "file not read yet" guard because the worktree copy had not been Read before editing (Read had been done on the canonical repo path only). Added a Read call before the Edit.

**Next time improvement:** When worktree path differs from canonical repo path, Read the worktree copy explicitly — do not assume a Read of the canonical path satisfies the Edit guard.

**Slowest step:** Reading 6 files in parallel at session start; all other steps were immediate.
