---
name: dbt-seed-snapshot
description: "Load seed CSVs and execute SCD snapshots with validation"
---

# dbt Seed & Snapshot

Seed loading and snapshot management.

## Seed Capabilities

- Load CSVs with `dbt seed`
- Full refresh on schema change detection
- Validate CSV format before loading (encoding, delimiters, column count)
- Support `--select` for specific seeds

## Snapshot Capabilities

- Execute snapshots with `dbt snapshot`
- Validate SCD integrity: check for duplicate `unique_key` values
- Audit configuration: verify `updated_at` or `check_cols` is set
- Warn if snapshot frequency seems too high for the data change rate

## Conversation Principles

- NEVER ask about snapshot strategy syntax
- ONLY ask: which seeds/snapshots to run, approval for execution
