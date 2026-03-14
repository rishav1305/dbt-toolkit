---
name: dbt-run
description: "Execute dbt models with smart selection, full-refresh detection, and retry"
---

# dbt Run

Execute dbt models with smart selection, approval gates, and failure handling.

## Flow

1. **Parse intent:** Which models? Full-refresh? Build vs run-only?
2. **Build selection:** Use `scripts/selector.py` to construct `--select` string
   - Natural language → selection syntax (e.g., "all audience models" → `tag:wcbm_dashboard,path:models/staging/audience`)
   - Supports `+model+`, `tag:`, `path:`, `config:`, `source:+`
   - Show resolved node list from `dbt ls --select <selector>` before executing
3. **Detect full-refresh need:**
   - If model SQL changed since last run (compare manifest), suggest `--full-refresh`
   - If user says "rebuild" or "from scratch", auto-add `--full-refresh`
4. **Show execution plan:** "Will run 6 models on `redshift` target with 4 threads. Proceed?"
5. **Execute:** Via configured method (local/SSH/Docker) using `scripts/runner.py`
6. **Parse results:** Read `run_results.json` — pass/fail per model, timing, rows affected
7. **Report:** Summary table with status, duration, row counts
8. **On failure:** Offer debug skill or `dbt retry` for failed nodes only

## Smart Features

- **Dependency awareness:** If user selects a downstream model, warn if upstream staging is stale
- **Retry integration:** On failure, parse `run_results.json` for failed nodes, offer `dbt retry`
- **Environment targeting:** `--target prod` vs `--target dev` with confirmation gate for prod

## Conversation Principles

- NEVER ask about CLI flags — build them from intent
- ONLY ask: which models, approval to run, what to do on failure
