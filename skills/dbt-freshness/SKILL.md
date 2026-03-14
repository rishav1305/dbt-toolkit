---
name: dbt-freshness
description: "Check source data freshness, track trends, show downstream impact"
---

# dbt Freshness

Check source data freshness with trend tracking and downstream impact analysis.

## Flow

1. **Execute:** `dbt source freshness` via configured method
2. **Parse:** Read `target/sources.json` using `scripts/artifacts.py`
3. **Display:** Per-source status sorted by urgency (errors → warnings → pass)
4. **Trend tracking:** Compare against previous runs stored in `.dbt-toolkit/freshness_history.json` using `scripts/freshness.py`
5. **Escalation:** If a source has been stale for multiple consecutive checks, escalate severity
6. **Downstream impact:** For stale sources, use `scripts/lineage.py` to show affected models

## Smart Features

- **Filter by urgency:** Errors first, then warnings, then passing
- **Downstream impact:** For stale sources, show affected downstream models
- **Custom thresholds:** Respect per-source `freshness.warn_after` / `error_after` from YAML, fall back to config default
- **History:** Store each check in `.dbt-toolkit/freshness_history.json` for trend analysis

## Conversation Principles

- NEVER ask about freshness config syntax
- ONLY ask: which sources to check, what to do about stale data
