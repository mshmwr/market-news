---
title: market-news — Product Requirements
type: reference
tags: [market-news, PRD]
updated: 2026-05-09
---

## Active Tickets

### MN-003 — Next.js App Shell — SSR/ISR + Real-Time Data Architecture

See full AC in `docs/tickets/MN-003-nextjs-shell.md`.

Deploy target: Vercel. `frontend/` subdir monorepo. Coexist with `docs/index.html` until MN-004 ports signals display. Vercel URL labeled "Pre-release" in README.

AC summary:

- **Phase 1 (Next.js scaffold + Vercel config):** AC-MN003-SCAFFOLD-01/02/03/04/05/06
- **Phase 2 (Real-time hook reservation):** AC-MN003-RT-01
- **Phase 3 (Coexist labeling):** AC-MN003-LEGACY-01/02

---

## Closed Tickets

### MN-002 — Stock Signals Web Display

See full AC in `docs/tickets/MN-002-signals-web-display.md`. [Closed 2026-05-03]

AC summary:

- **Phase 1 (JSON output flag):** AC-MN002-JSON-01/02/03/04
- **Phase 2 (GitHub Actions workflow):** AC-MN002-WF-01/02/03/04
- **Phase 3 (HTML Signals section):** AC-MN002-HTML-01/02/03/04/05/06/07

### MN-001 — Stock Signal Analyzer CLI

See full AC in `docs/tickets/MN-001-stock-signal-analyzer.md`. [Closed 2026-05-03]

AC summary:

- **Phase 1 (Models + Signals):** AC-MN001-MODELS-01, AC-MN001-NEWS-01/02, AC-MN001-TECH-01/02, AC-MN001-FUND-01, AC-MN001-SOCIAL-01/02
- **Phase 2 (Synthesizer + Notifier):** AC-MN001-SYNTH-01/02/03, AC-MN001-NOTIFY-01/02
- **Phase 3 (CLI + deps):** AC-MN001-CLI-01/02/03, AC-MN001-DEPS-01
