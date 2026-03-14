---
name: dbt-docs
description: "Generate documentation, audit coverage, bulk document models"
---

# dbt Docs

Documentation generation, serving, and gap analysis.

## Capabilities

### 1. Generate
Run `dbt docs generate` to build catalog.json and documentation site.

### 2. Serve
Run `dbt docs serve` to launch local documentation server.

### 3. Audit Undocumented
- Parse catalog.json for documentation gaps
- Use `scripts/coverage.py` for model and column coverage
- Prioritize by downstream usage (more dependents = higher priority)

### 4. Bulk Document
- Inspect column names, types, and sample data
- Generate description suggestions using naming patterns and context
- Write to YAML schema files (user approves each suggestion)

### 5. Doc Blocks
- Create and manage `{% docs %}` blocks for reusable documentation
- Link doc blocks to model/column descriptions

## Conversation Principles

- NEVER ask about YAML formatting or doc block syntax
- ONLY ask: does this description accurately describe the column/model
