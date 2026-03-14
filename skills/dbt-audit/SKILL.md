---
name: dbt-audit
description: "Proactive health checks — test coverage, docs, materialization, sort/dist keys"
---

# dbt Audit

Proactive health checks using `scripts/audit.py`.

## Checks Performed

1. **Test coverage** — Models without tests, coverage %, missing primary key tests. Uses `scripts/coverage.py`.
2. **Documentation coverage** — Models/columns without descriptions, prioritized by downstream usage
3. **Materialization review** — Views queried by 3+ models (suggest table), tables queried once (suggest view), incrementals without `unique_key`
4. **Redshift-specific** — Missing sort/dist config, late binding view opportunities, incremental strategy appropriateness. Only when adapter is `redshift`.
5. **Tag hygiene** — Untagged models, orphan tags, coverage by directory
6. **Source freshness baseline** — Sources without `freshness` config, missing `loaded_at_field`

## Output Format

Severity-grouped report with actionable suggestions:

```
Audit Results (3 warnings, 5 info)

WARNINGS:
  [materialization] model.proj.incremental_no_key — Incremental model missing unique_key — risk of duplicates
  [test_coverage] Test coverage 40% is below threshold 80%. Untested: model_a, model_b

INFO:
  [redshift] model.proj.table_a — No sort key configured
  [tags] model.proj.no_tags — Model has no tags
```

## Links to Other Skills

- Documentation gaps → offer `dbt-toolkit:dbt-docs` to bulk document
- Missing tests → offer `dbt-toolkit:dbt-test` to show what's needed
- Materialization issues → offer `dbt-toolkit:dbt-run` with `--full-refresh`

## Conversation Principles

- NEVER ask about audit thresholds — use config defaults
- ONLY ask: want me to fix any of these issues?
