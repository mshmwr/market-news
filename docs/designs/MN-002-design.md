# MN-002 Design Doc — Stock Signals Web Display

**Ticket:** MN-002  
**Phase:** 1 (JSON output) → 2 (GitHub Actions workflow) → 3 (HTML display)  
**Architect:** Senior Architect  
**Date:** 2026-05-03  
**Status:** Ready for Engineer

---

## 0 Scope Questions / Drift Fixes

**Drift found — env var name mismatch:**
`ssot/system-overview.md` lists `ANTHROPIC_API_KEY` as the required API key, but `synthesizer.py:24` uses `os.environ["GEMINI_API_KEY"]` with `base_url="https://generativelanguage.googleapis.com/..."`. The actual runtime key is `GEMINI_API_KEY`. The system-overview.md entry is stale. This design doc and the workflow both use `GEMINI_API_KEY`. The ssot/system-overview.md Changelog and Environment Variables table are corrected at the bottom of this session (§Architecture Doc Sync).

---

## 1 signals.json Schema (Exact)

### 1.1 Top-level envelope

```
{
  "generated_at": string,   // ISO 8601 UTC — datetime.utcnow().isoformat() + "Z"
  "signals": [ <SignalEntry>, ... ]
}
```

### 1.2 SignalEntry object

```
{
  "ticker":     string,                    // e.g. "NVDA", "^VIX", "BTC-USD"
  "signal":     "BUY" | "HOLD" | "SELL",
  "confidence": integer (0..100 inclusive),
  "rationale":  string                     // 1–3 sentences from Gemini
}
```

Fields are the four public fields of `SignalResult` (models.py:44–49). No additional fields.
Order within each SignalEntry is not guaranteed; frontend must access by key.

### 1.3 Concrete example

```json
{
  "generated_at": "2026-05-03T06:00:12Z",
  "signals": [
    {
      "ticker": "NVDA",
      "signal": "BUY",
      "confidence": 78,
      "rationale": "Strong momentum supported by RSI 62 and volume 1.8x average. PE ratio elevated but revenue growth of 122% justifies premium. Positive sentiment across news and social signals."
    },
    {
      "ticker": "^VIX",
      "signal": "HOLD",
      "confidence": 50,
      "rationale": "Volatility index shows elevated uncertainty. No fundamentals available for index instruments. Neutral stance recommended."
    }
  ]
}
```

### 1.4 Boundary contracts

| Scenario | Behavior |
|----------|----------|
| All tickers succeed | All 12 entries in `signals` array |
| Partial failure (1..11 tickers fail) | Only successful tickers in `signals`; array may be shorter than ticker list |
| All tickers fail | `--output-json` file is NOT written (or existing file is not overwritten); exit code 1 |
| `signals` array is empty | This only occurs if all tickers failed; file not written (see above) |
| `confidence` field | Always integer 0–100 (enforced by pydantic Field constraint in models.py:46) |
| `rationale` null | Cannot occur — pydantic `str` field is required; empty string is the floor |
| `ticker` containing special chars (`^`, `-`) | Stored verbatim as string; no escaping |

---

## 2 analyze_stock.py Changes

### 2.1 argparse replacement for `sys.argv`

Current entry point (lines 46–51) reads tickers directly from `sys.argv[1:]`. Replace with `argparse` to add `--output-json` without breaking positional ticker arguments.

Pseudo-code for new `__main__` block:

```
parser = argparse.ArgumentParser(description="Analyze stock tickers and output signals.")
parser.add_argument("tickers", nargs="+", metavar="TICKER")
parser.add_argument("--output-json", metavar="PATH", default=None,
                    help="Write signals.json to this path")
args = parser.parse_args()
sys.exit(main(args.tickers, output_json=args.output_json))
```

`argparse` is stdlib — no new dependency.

### 2.2 main() signature change

Current: `def main(tickers: list[str]) -> int`  
New:     `def main(tickers: list[str], output_json: str | None = None) -> int`

The `output_json=None` default preserves backward compatibility for any direct callers (AC-MN002-JSON-03).

### 2.3 Result collection inside main()

Pseudo-code for the updated loop body:

```
successful_results: list[SignalResult] = []
failed: list[str] = []

for ticker in tickers:
    try:
        result = analyze_ticker(ticker)
        notify_console(result)
        notify_telegram(result)
        successful_results.append(result)      # NEW: collect on success
    except Exception as exc:
        print(f"ERROR [{ticker}]: {exc}")
        failed.append(ticker)

# JSON write block (NEW, only when --output-json provided)
if output_json is not None and successful_results:
    _write_signals_json(output_json, successful_results)

return 1 if len(failed) == len(tickers) else 0
```

### 2.4 _write_signals_json helper (new private function)

This function is placed above `main()`. Pseudo-code:

```
def _write_signals_json(path: str, results: list[SignalResult]) -> None:
    import json, datetime
    payload = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "signals": [r.model_dump() for r in results],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"[signals] Written {len(results)} signal(s) to {path}")
```

`model_dump()` is the pydantic v2 method (pydantic already in requirements). `ensure_ascii=False` preserves any unicode in rationale strings.

### 2.5 Import additions

Add at top of file (stdlib only, no new packages):
- `import argparse`
- `import json`
- `import datetime`

### 2.6 Skip-on-failure contract (AC-MN002-JSON-02)

- A ticker that raises any `Exception` inside the `try` block is appended to `failed` and NOT appended to `successful_results`.
- The `_write_signals_json` call is guarded by `successful_results` being non-empty (`if output_json is not None and successful_results:`).
- If ALL tickers fail, `successful_results` is empty, guard is false, file is not written / not overwritten. Exit code is 1 (existing logic: `1 if len(failed) == len(tickers) else 0`).

### 2.7 Backward compatibility (AC-MN002-JSON-03)

- `output_json` parameter defaults to `None`.
- When `None`, the `if output_json is not None` guard is false — no file write, no import side effect.
- CLI invocation without `--output-json` produces identical console/Telegram output to the current implementation.
- `python3 analyze_stock.py NVDA` continues to work (positional args still first positional arguments to argparse).

### 2.8 Boundary contracts for Phase 1

| Scenario | Behavior |
|----------|----------|
| `--output-json` path directory does not exist | `open()` raises `FileNotFoundError`; exception propagates (not caught); workflow will fail with clear error |
| `--output-json` provided, zero tickers given | `argparse` `nargs="+"` enforces ≥1 ticker; process exits with argparse usage error before `main()` is reached |
| Partial write (disk full mid-write) | Python `json.dump` uses buffered write; partial JSON may be written; acceptable for MVP (Known Gap — not in AC scope) |

---

## 3 update-signals.yml Structure

### 3.1 Full workflow specification

File: `.github/workflows/update-signals.yml`

```yaml
name: Update Signals

on:
  schedule:
    - cron: '0 6 * * *'   # 06:00 UTC daily
  workflow_dispatch:

concurrency:
  group: signals-push
  cancel-in-progress: false   # queue, do not cancel an in-progress run

jobs:
  update:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    env:
      GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run signal analysis
        run: |
          python analyze_stock.py \
            --output-json docs/signals.json \
            NVDA TSLA AAPL GOOGL TSM BTC-USD ETH-USD SPY QQQ SOXX "^GSPC" "^VIX"

      - name: Commit if changed
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/signals.json
          git diff --staged --quiet || git commit -m "chore: update signals $(date -u +%Y-%m-%dT%H:%M:%SZ)"
          git pull --rebase
          git push
```

### 3.2 Design decisions

**Concurrency group `signals-push` with `cancel-in-progress: false`:**
Using `cancel-in-progress: false` queues a second run rather than cancelling it. This is preferable to cancellation because the analysis result of an already-running job should not be discarded. The group name `signals-push` is separate from any group used in `update-news.yml` — if `update-news.yml` later needs serialization with this workflow, both should share a single group name (currently out of scope).

**`git pull --rebase` before `git push`:**
Placed after `git commit` (if any commit was made) and before `git push`. If `update-news.yml` pushed between this workflow's checkout and push, the rebase fast-forwards cleanly. If the rebase finds a conflict on `docs/signals.json` vs `docs/news.json` (different files), it resolves automatically. True conflict (two signals runs simultaneously) is prevented by the concurrency group.

**`pip install -r requirements.txt` instead of individual packages:**
Mirrors project structure. All analysis dependencies are already in `requirements.txt`. Using the full requirements file avoids drift between local and CI environments.

**`GEMINI_API_KEY` as required env var:**
Injected at job level from `secrets.GEMINI_API_KEY`. If the secret is unset, `synthesizer.py:24` raises `KeyError: 'GEMINI_API_KEY'` — failing the workflow with a clear error (AC-MN002-WF-04 satisfied without additional code).

### 3.3 Boundary contracts for Phase 2

| Scenario | Behavior |
|----------|----------|
| `GEMINI_API_KEY` secret not set | `KeyError` in `synthesizer.py` → workflow step fails with non-zero exit; clear error in logs |
| All 12 tickers fail (network outage) | `main()` returns 1; `analyze_stock.py` exits non-zero; workflow step fails; no commit; no push |
| Some tickers fail | `main()` returns 0; partial `signals.json` written; workflow commits and pushes partial result |
| `docs/signals.json` unchanged | `git diff --staged --quiet` exits 0; no commit; `git pull --rebase && git push` runs on clean state (no-op push) |
| Concurrent `update-news.yml` push | Concurrency group serializes; `git pull --rebase` resolves non-conflicting file changes |

---

## 4 HTML Signals Section Design

### 4.1 Insertion point

Insert the Signals section inside `<main>` (line 108 of current `docs/index.html`), **before** `<div id="status">` and `<div id="news-list">`.

Resulting `<main>` structure:

```
<main>
  <!-- NEW: signals section -->
  <section id="signals-section">
    <div class="signals-header">
      <h2 class="signals-title">股票訊號</h2>
      <span id="signals-updated"></span>
    </div>
    <div id="signals-list" class="signals-grid"></div>
    <div id="signals-placeholder" hidden>訊號暫未生成</div>
  </section>
  <!-- existing -->
  <div id="status">載入中…</div>
  <div id="news-list" class="news-list" hidden></div>
</main>
```

### 4.2 Card HTML structure (per signal)

Cards are built entirely via DOM API (no `innerHTML` string interpolation). The following represents the final DOM shape for each card:

```
<div class="signal-card signal-BUY">          <!-- class varies: signal-BUY / signal-HOLD / signal-SELL -->
  <div class="signal-card-header">
    <span class="signal-ticker"></span>        <!-- textContent = ticker -->
    <span class="signal-badge"></span>         <!-- textContent = signal value -->
  </div>
  <div class="signal-confidence"></div>        <!-- textContent = "信心度 78%" -->
  <div class="signal-rationale"></div>         <!-- textContent = rationale string -->
</div>
```

All user-data fields (ticker, signal label, confidence, rationale) are assigned via `element.textContent = value` — never via `innerHTML` or template literals containing untrusted data (AC-MN002-HTML-05).

### 4.3 CSS additions

All new CSS is added inside the existing `<style>` block. No external stylesheet. Colors match the existing palette (`#1d1d1f`, `#f5f5f7`, white cards).

```css
/* --- Signals section --- */
#signals-section {
  margin-bottom: 24px;
}
.signals-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 12px;
}
.signals-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d1d1f;
}
#signals-updated {
  font-size: 12px;
  color: #999;
}
#signals-placeholder {
  font-size: 14px;
  color: #888;
  padding: 16px 0;
}
.signals-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 10px;
}

/* Signal cards */
.signal-card {
  background: #fff;
  border-radius: 10px;
  padding: 12px 14px;
  border-left: 4px solid transparent;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;                     /* prevent grid blowout */
}
.signal-BUY  { border-left-color: #2e7d32; }  /* green */
.signal-HOLD { border-left-color: #f9a825; }  /* yellow */
.signal-SELL { border-left-color: #c62828; }  /* red   */

.signal-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 6px;
}
.signal-ticker {
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.signal-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
}
.signal-BUY  .signal-badge { background: #e8f5e9; color: #2e7d32; }
.signal-HOLD .signal-badge { background: #fff8e1; color: #f9a825; }
.signal-SELL .signal-badge { background: #ffebee; color: #c62828; }

.signal-confidence {
  font-size: 12px;
  color: #555;
}
.signal-rationale {
  font-size: 12px;
  color: #666;
  line-height: 1.5;
  /* CSS line-clamp (AC-MN002-HTML-06) */
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Mobile: single column below 400px */
@media (max-width: 400px) {
  .signals-grid {
    grid-template-columns: 1fr;
  }
}
```

### 4.4 JavaScript — loadSignals() function

Added after the existing `loadNews()` function. Called once on page load alongside `loadNews()`.

Pseudo-code (to be implemented using DOM API — no innerHTML with untrusted data):

```
function loadSignals() {
  fetch('signals.json')
    .then(r => {
      if (!r.ok) throw new Error('404');
      return r.json();
    })
    .then(data => {
      // Render generated_at timestamp (AC-MN002-HTML-07)
      if (data.generated_at) {
        const d = new Date(data.generated_at);
        signalsUpdatedEl.textContent = '訊號更新於 ' + d.toLocaleString('zh-TW', {
          year: 'numeric', month: '2-digit', day: '2-digit',
          hour: '2-digit', minute: '2-digit'
        });
      }
      // Render each signal card
      data.signals.forEach(s => {
        const card = buildSignalCard(s);
        signalsListEl.appendChild(card);
      });
      signalsListEl.hidden = false;
    })
    .catch(() => {
      // 404 or any fetch error — show placeholder, do NOT throw (AC-MN002-HTML-04)
      signalsPlaceholderEl.hidden = false;
    });
}

function buildSignalCard(s) {
  // All text assigned via textContent — no innerHTML (AC-MN002-HTML-05)
  const card = document.createElement('div');
  card.className = 'signal-card signal-' + (s.signal || 'HOLD');

  const header = document.createElement('div');
  header.className = 'signal-card-header';

  const tickerEl = document.createElement('span');
  tickerEl.className = 'signal-ticker';
  tickerEl.textContent = s.ticker ?? '';          // null-safe (AC-MN002-HTML-03)

  const badgeEl = document.createElement('span');
  badgeEl.className = 'signal-badge';
  badgeEl.textContent = s.signal ?? '';

  header.appendChild(tickerEl);
  header.appendChild(badgeEl);

  const confEl = document.createElement('div');
  confEl.className = 'signal-confidence';
  confEl.textContent = s.confidence != null ? '信心度 ' + s.confidence + '%' : '';

  const ratEl = document.createElement('div');
  ratEl.className = 'signal-rationale';
  ratEl.textContent = s.rationale ?? '';          // null-safe; empty string renders as blank

  card.appendChild(header);
  card.appendChild(confEl);
  card.appendChild(ratEl);
  return card;
}
```

### 4.5 Boundary contracts for Phase 3

| Scenario | Behavior |
|----------|----------|
| `signals.json` returns 404 | `.catch()` shows `#signals-placeholder`; news section unaffected; no uncaught exception (AC-MN002-HTML-04) |
| `signal` value is null/undefined | `card.className` falls back to `signal-HOLD`; `badgeEl.textContent` = empty string |
| `confidence` is null/undefined | `confEl.textContent` = empty string (conditional in `buildSignalCard`) |
| `rationale` is null/undefined | `ratEl.textContent` = empty string (AC-MN002-HTML-03) |
| Ticker = `^GSPC` or `^VIX` | `textContent` assignment is safe — no HTML interpretation (AC-MN002-HTML-05) |
| Rationale > 3 lines | `-webkit-line-clamp: 3` clips text; no overflow (AC-MN002-HTML-06) |
| 375px mobile viewport | `minmax(160px, 1fr)` grid; at 375px fits 2 columns (2×160+10=330 < 375); `@media(max-width:400px)` enforces 1 column |
| `generated_at` absent | `if (data.generated_at)` guard skips timestamp; `#signals-updated` stays empty |
| `signals` array empty (all tickers failed, partial write) | `forEach` loop runs 0 times; `signalsListEl` has no children but is unhidden; no error |

---

## 5 File Change List

| File | Action | Description |
|------|--------|-------------|
| `analyze_stock.py` | Modify | Add `argparse` for `--output-json`; add `_write_signals_json()`; update `main()` signature; add `import argparse, json, datetime` |
| `docs/signals.json` | Create (generated) | Output file written by workflow; committed by CI; initial placeholder may be committed by user after first manual dispatch |
| `.github/workflows/update-signals.yml` | Create | Daily cron (06:00 UTC) + `workflow_dispatch`; runs analysis for 12 tickers; commits `docs/signals.json` if changed |
| `docs/index.html` | Modify | Add `<section id="signals-section">` in `<main>`; add CSS rules inside `<style>`; add `loadSignals()` + `buildSignalCard()` JS; call `loadSignals()` at page init |
| `ssot/system-overview.md` | Modify | Fix env var drift (`ANTHROPIC_API_KEY` → `GEMINI_API_KEY`); add MN-002 changelog entry; add `signals.json` to directory structure; add workflow to data flow |

---

## 6 Implementation Order

### Phase 1 — analyze_stock.py (no external dependency)

1. Edit `analyze_stock.py`: add imports (`argparse`, `json`, `datetime`), add `_write_signals_json()`, update `main()` signature, replace `__main__` block.
2. Verify: `python -m py_compile analyze_stock.py` exits 0 (AC-MN002-JSON-04).
3. Smoke test locally: `python analyze_stock.py --output-json /tmp/test-signals.json NVDA` → confirm file written with correct schema.

### Phase 2 — GitHub Actions workflow (depends on Phase 1 being merged or in same branch)

1. Create `.github/workflows/update-signals.yml` per §3.1 specification.
2. No local verification possible for CI; file is reviewed via diff. Ensure `GEMINI_API_KEY` secret is set in GitHub repo before first scheduled run.

### Phase 3 — docs/index.html (independent of Phase 2; depends on Phase 1 schema)

1. Edit `docs/index.html`:
   a. Add CSS block in `<style>`.
   b. Add `<section id="signals-section">` HTML at top of `<main>`.
   c. Add `signalsListEl`, `signalsUpdatedEl`, `signalsPlaceholderEl` element references after existing `const` declarations.
   d. Add `loadSignals()` and `buildSignalCard()` functions.
   e. Call `loadSignals()` at page init (alongside `loadNews()`).
2. Verify by opening `docs/index.html` locally with a mock `signals.json` placed in `docs/`.
3. Test 404 path: rename `signals.json` temporarily and confirm placeholder renders without console errors.

### Parallelization note

Phase 3 can begin in parallel with Phase 2 once Phase 1 schema is finalized. The HTML/JS only needs the `signals.json` schema contract (§1), which is locked in this design doc.

---

## 7 Risks and Notes

- **GEMINI_API_KEY secret drift:** `ssot/system-overview.md` previously listed `ANTHROPIC_API_KEY`. Any documentation or runbook referencing the old key name will silently fail. The sync is included in this ticket's file change list.
- **`-webkit-line-clamp` vendor prefix:** Required for broader compatibility on older WebKit/Blink browsers. As of 2026, `line-clamp` (unprefixed) has good support but the prefixed form is the safe baseline for a PWA targeting iOS Safari.
- **`git pull --rebase` with no upstream changes:** `git pull --rebase` on an already-up-to-date branch is a no-op and exits 0. Safe in all cases.
- **`update-news.yml` concurrency:** The existing `update-news.yml` has no concurrency group. If concurrent race conditions are observed in production, `update-news.yml` should be updated in a separate ticket to add `concurrency: group: signals-push` (same group as `update-signals.yml`) to serialize all pushes. Currently out of scope per AC-MN002-WF-03 which allows either `git pull --rebase` or concurrency group — this design uses both (belt-and-suspenders).
- **No `signals.json` on initial deploy:** The HTML 404 fallback (placeholder text) handles this gracefully. The workflow `README`/release checklist (in ticket §Release Status) tells the user to trigger the workflow manually.
- **Pydantic v2 `model_dump()`:** `synthesizer.py` imports from `pydantic` — confirm `pydantic>=2.0` is in `requirements.txt` before Phase 1. If pydantic v1 is present, the method is `dict()` not `model_dump()`. Engineer must check `requirements.txt`.

---

## All-Phase Coverage Gate

| Phase | Backend API / Python | Frontend Route | Component Tree | Props Interface |
|-------|---------------------|----------------|----------------|----------------|
| Phase 1 (JSON flag) | `analyze_stock.py` + `_write_signals_json` contract defined in §2 | N/A | N/A | N/A |
| Phase 2 (Workflow) | `.github/workflows/update-signals.yml` spec in §3.1 | N/A | N/A | N/A |
| Phase 3 (HTML) | N/A | `docs/index.html` (single page) | `#signals-section` → `.signals-grid` → `.signal-card` in §4.1–4.2 | `buildSignalCard(s)` input contract in §4.4 |

---

## Boundary Pre-emption Table

| Boundary scenario | Defined? |
|-------------------|---------|
| Empty/null input (ticker list) | Yes — argparse `nargs="+"` enforces ≥1; null fields in SignalResult covered in §4.5 |
| Max/min value boundary (confidence 0–100) | Yes — pydantic Field constraint; not re-validated in HTML (trusted JSON from own workflow) |
| API error (fetch 404/timeout on signals.json) | Yes — §4.5, `.catch()` shows placeholder; does not throw |
| Concurrency / race condition (dual workflow push) | Yes — §3.2, concurrency group + `git pull --rebase` |
| Empty signals array | Yes — §1.4 + §3.3 (not written if all fail) + §4.5 (empty forEach) |

---

## Refactorability Checklist

- [x] **Single responsibility:** `_write_signals_json` is isolated; `buildSignalCard` is isolated; `loadSignals` is isolated from `loadNews`.
- [x] **Interface minimization:** `buildSignalCard(s)` receives a plain object with 4 fields matching SignalEntry schema — no extra coupling.
- [x] **Unidirectional dependency:** Python writes JSON; HTML reads JSON; no circular dependency.
- [x] **Replacement cost:** If Gemini is swapped for another LLM, only `synthesizer.py` changes; `_write_signals_json` consumes `model_dump()` output — no coupling to Gemini.
- [x] **Clear test entry point:** `_write_signals_json(path, results)` is pure I/O — testable with a tmp path and mock `SignalResult` list. `buildSignalCard(s)` returns a DOM node testable without fetch.
- [x] **Change isolation:** Python schema change (add field) requires HTML `buildSignalCard` update, but changing HTML card layout does not affect Python. One-directional coupling is acceptable.

---

## Retrospective

**Where most time was spent:** Verifying env var drift (`ANTHROPIC_API_KEY` vs `GEMINI_API_KEY`) — required reading `synthesizer.py` after spotting the inconsistency in `system-overview.md`.

**Which decisions needed revision:** None — all BQs were pre-resolved by PM (BQ-002-01 through BQ-002-04) before design started.

**Next time improvement:** When reading `system-overview.md` at design start, immediately cross-check every env var name against actual usage in `.py` files — do not assume SSOT is current.
