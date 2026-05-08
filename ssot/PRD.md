---
title: market-news — Product Requirements
type: reference
tags: [market-news, PRD]
updated: 2026-05-09
---

## Active Tickets

### MN-005 — PWA Port to Next.js + Retire GH Pages

See full AC in `docs/tickets/MN-005-pwa-and-retire-ghpages.md`.

Port PWA features from `docs/` to Next.js frontend. Retire GH Pages as production by adding a meta-refresh redirect to Vercel.

AC summary:

- **Phase 1 (PWA assets in Next.js):** AC-MN005-PWA-01/02/03/04
- **Phase 2 (GH Pages retirement):** AC-MN005-RETIRE-01/02/03

---

## Closed Tickets

### MN-004 — Signals Display Port to Next.js

See full AC in `docs/tickets/MN-004-signals-port-nextjs.md`. [Closed 2026-05-09]

AC summary:

- **Phase 1 (Data fetching + JSON route):** AC-MN004-DATA-01/02/03
- **Phase 2 (Signals section UI):** AC-MN004-SIG-01/02/03/04/05/06
- **Phase 3 (News section UI):** AC-MN004-NEWS-01/02/03/04
- **Phase 4 (Translate button + theme-color):** AC-MN004-TRANSLATE-01
- **Phase 5 (README re-label):** AC-MN004-RETIRE-01/02

### MN-003 — Next.js App Shell — SSR/ISR + Real-Time Data Architecture

See full AC in `docs/tickets/MN-003-nextjs-shell.md`. [Closed 2026-05-09]

AC summary:

- **Phase 1 (Next.js scaffold + Vercel config):** AC-MN003-SCAFFOLD-01/02/03/04/05/06
- **Phase 2 (Real-time hook reservation):** AC-MN003-RT-01
- **Phase 3 (Coexist labeling):** AC-MN003-LEGACY-01/02

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
