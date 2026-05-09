---
id: MN-007
title: Daily Digest LLM Narrative (NIM / MiniMax M2.7)
status: in-progress
created: 2026-05-09
type: feature
priority: medium
size: S
visual-delta: none
content-delta: yes
qa-early-consultation: skipped — single-file additive change, no failure modes that block delivery (NIM failures degrade gracefully to raw lists)
---

## Summary

Add per-section LLM narratives to the daily digest email so each block (stocks,
F&G, geopolitical, FOMC) carries a Chinese-language interpretation, not just raw
lists / titles. Generation goes through NVIDIA NIM (`minimaxai/minimax-m2.7`) to
match user's existing `/nim` slash-command stack and avoid an Anthropic key.

Inspired by Threads post @lyn0707_ — original target user feedback: "他的會不
只列新聞，會用文字說明".

## Scope

Files touched:
- `digest.py` — add `_call_nim()` + four `_narrative_*()` builders; thread a
  `narratives: dict[str, str]` arg through `_render_html`; call NIM once per
  section in `main()`.
- `.github/workflows/daily-digest.yml` — pass `NVIDIA_API_KEY` from secrets.
- `docs/tickets/MN-007-*.md` — this ticket.

## Acceptance Criteria

1. **Narrative present.** Successful run with `NVIDIA_API_KEY` set produces a
   `<p>` paragraph (styled blockquote) before each section's data block.
2. **Graceful degradation.** Missing `NVIDIA_API_KEY` or NIM API failure → narrative
   skipped, raw section still renders, exit code remains 0 (only Resend failure
   exits 1).
3. **Stocks section.** Narrative covers板塊 / 主題 / 偏多偏空 / 催化劑 in 120–180
   字 Chinese.
4. **F&G section.** Narrative covers情緒解讀 / 風險資產含意 / 短線方向 in 80–120
   字 Chinese.
5. **Geopolitical section.** Narrative covers主要風險主題 / 對能源原物料避險資產
   影響 in 100–150 字.
6. **FOMC section.** Narrative covers利率走向 / 美股與全球風險資產影響 in 100–150
   字.
7. **NIM call budget.** ≤4 calls per run × 2 runs/day = ≤8 calls/day.

## Out of Scope

- Translating NIM output language (always 繁體中文).
- Dynamic temperature / system prompt tuning per section.
- Fallback to alternate model on NIM outage.

## Required Secrets

- `NVIDIA_API_KEY` — already used locally for `/nim`; user adds to repo secrets
  before next workflow run.
