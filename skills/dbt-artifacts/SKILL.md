---
name: dbt-artifacts
description: "Parse run results, explore manifest, compare states, inspect catalog"
---

# dbt Artifacts

Parse and analyze dbt artifacts for insights.

## Capabilities

### 1. Run Results Analysis
- Use `scripts/artifacts.py` to parse `run_results.json`
- Pass/fail/skip counts, timing, slowest models
- Compare two runs side-by-side

### 2. Manifest Exploration
- Model count by materialization type
- Lineage chains via `scripts/lineage.py`
- Find models by config (tags, materialization, schema)

### 3. State Comparison
- Diff two manifests for new/removed/modified models
- Schema changes (column additions, type changes)
- Useful for deployment review

### 4. Catalog Inspection
- Column types, table stats, row counts
- Drift detection vs YAML schema definitions
- Stale catalog detection

## Conversation Principles

- NEVER ask about JSON schema details
- ONLY ask: which runs to compare, what aspects to focus on
