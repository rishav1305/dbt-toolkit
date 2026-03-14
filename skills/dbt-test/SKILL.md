---
name: dbt-test
description: "Run data and unit tests, analyze failures, report coverage"
---

# dbt Test

Run tests, analyze failures, and report coverage.

## Flow

1. **Parse intent:** All tests? Specific model? Data tests only? Unit tests only?
2. **Build selection:**
   - "test my audience model" → `dbt test --select stg_wcbm_audience_metrics`
   - "run all unit tests" → `dbt test --select test_type:unit`
   - "run generic tests only" → `dbt test --select test_type:generic`
3. **Execute and parse results** from `run_results.json`
4. **On failure:**
   - Show failing test name, SQL, and failure rows
   - If `store_failures` enabled, query the failure table for sample bad rows
   - Offer root-cause analysis via `test-failure-agent`
5. **Coverage report:**
   - Use `scripts/coverage.py` for models without tests
   - Show coverage percentage vs configured threshold
   - Suggest missing tests (e.g., "model X has no `not_null` test on its primary key")

## Unit Test Support (dbt 1.8+)

- Detect dbt version from `manifest.json` metadata
- If >= 1.8, include unit test capabilities
- Warn about Redshift-specific limitations (LISTAGG, PERCENTILE_CONT in CTEs)

## Conversation Principles

- NEVER ask about test syntax — auto-detect test types
- ONLY ask: which models to test, what to do about failures
