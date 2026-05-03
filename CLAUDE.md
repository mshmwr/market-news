# CLAUDE.md — market-news

Daily market news aggregator + stock signal analyzer CLI.

## SSOT Routing

| When you need... | Read |
|---|---|
| System architecture, data flow, env vars | [ssot/system-overview.md](./ssot/system-overview.md) |
| Acceptance criteria | [ssot/PRD.md](./ssot/PRD.md) |
| Ticket details | `docs/tickets/MN-*.md` |

## Tech Stack

- **Python:** use `python -m py_compile <file>` after any edit to verify syntax
- **Naming:** snake_case throughout (Python-only project)
- **No async:** all I/O is synchronous; do not introduce asyncio

## Ticket ID Convention

Prefix: `MN-` (market-news)
Next ID: `MN-002`

## Behavior Triggers

| Event | Action |
|---|---|
| Edit any `.py` file | Run `python -m py_compile <file>` to verify |
| Role finishes task | Prepend entry to `docs/retrospectives/<role>.md` |
