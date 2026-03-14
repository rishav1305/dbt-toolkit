---
name: dbt-setup
description: "First-time project wizard — configure execution, test connection, index project"
---

# dbt Setup Wizard

First-time configuration for dbt-toolkit. Detects existing project state and fills gaps.

## Flow

1. **Detect project:** Check for `dbt_project.yml` — if missing, offer `dbt init` or ask user to point to project
2. **Parse profiles:** Check for `profiles.yml` — parse available profiles/targets
3. **Execution method:** Ask "How do you run dbt?" → local / SSH / Docker
4. **SSH config** (if SSH): discover host, user, key, remote project path, venv path, env vars needed
5. **Bootstrap:** Run `scripts/bootstrap.sh` — parse output markers (PYTHON_VERSION, DBT_VERSION, DBT_ADAPTER, CONNECTION)
6. **Verify connection:** Run `dbt debug` via configured method
7. **Index project:** Run `dbt parse` to generate manifest (no warehouse needed). Fallback: `dbt ls --resource-type model` if dbt < 1.5
8. **Write config:** Generate `.dbt-toolkit/config.yaml` from template
9. **Gitignore:** Write `.dbt-toolkit/.gitignore` (cache/, freshness_history.json, .secrets/) and `.dbt-toolkit/.secrets/.gitignore`
10. **Initial freshness:** Run source freshness check if sources exist
11. **Summary:** Display model count, source count, test coverage, freshness status

## Questions (Business-Only)

- "How do you run dbt — locally, on a remote server via SSH, or in Docker?"
- "Which profile/target should be the default?"
- If SSH: "What's the server address?" (auto-discovers key from `~/.ssh/config` if possible)
- "Any tags you use frequently?" (scans project for existing tags)

## Output Markers from bootstrap.sh

- `PYTHON_VERSION=3.x.y`
- `DBT_VERSION=1.x.y`
- `DBT_ADAPTER=redshift`
- `CONNECTION=OK` or `CONNECTION=FAIL`
- `BOOTSTRAP_DONE`

## Error Recovery

- If `dbt debug` fails → check profile, target, credentials, network
- If `dbt parse` fails → check YAML syntax, missing refs, circular dependencies
- If bootstrap.sh fails → check Python availability, pip, network access
