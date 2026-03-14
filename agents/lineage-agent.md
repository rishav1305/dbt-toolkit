# Lineage Agent

Specialized subagent for DAG traversal and impact analysis.

## Input

- `model_name`: The dbt model unique_id or short name
- `question`: What the user wants to know (e.g., "what depends on this?", "what would break?", "show upstream")

## Method

1. Locate `target/manifest.json` in the dbt project
2. Use `scripts/lineage.py` functions:
   - `get_ancestors(manifest_path, unique_id)` — all upstream nodes (transitive parents)
   - `get_descendants(manifest_path, unique_id)` — all downstream nodes (transitive children)
   - `get_impact_radius(manifest_path, unique_id)` — both ancestors and descendants
3. For each node, report: unique_id, resource_type, materialization

## Output Format

```
Model: model.proj.stg_audience_metrics

Upstream (3 nodes):
  source.proj.raw.audience_data (source)
  model.proj.base_audience (table)
  model.proj.stg_audience_raw (view)

Downstream (2 nodes):
  model.proj.int_audience_weekly (incremental)
  model.proj.bi_audience_dashboard (table)

Impact radius: 5 nodes total
```

## Used By

- `dbt-develop` — lineage exploration
- `dbt-run` — dependency warnings (upstream stale)
- `dbt-audit` — orphan detection (no downstream)
