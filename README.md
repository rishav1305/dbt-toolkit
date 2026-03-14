# dbt-toolkit

A workflow-oriented Claude Code plugin for dbt project management. Organized around how people actually use dbt — develop, run, test, validate — rather than mirroring CLI commands.

## Installation

Install as a Claude Code plugin:

```bash
claude plugin add /path/to/dbt-toolkit
```

Or clone and link:

```bash
git clone <repo-url> dbt-toolkit
claude plugin add ./dbt-toolkit
```

## Quick Start

1. Navigate to your dbt project directory
2. Run `/dbt-toolkit:dbt` — the router will detect your project and guide you through setup
3. After setup, use `/dbt-toolkit:dbt run`, `/dbt-toolkit:dbt test`, etc.

## Skills

### v1 Core

| Skill | Command | Description |
|---|---|---|
| Router | `/dbt` | Status display + interactive menu |
| Setup | `/dbt setup` | First-time configuration wizard |
| Run | `/dbt run` | Execute models with smart selection |
| Test | `/dbt test` | Run tests, analyze failures, coverage |
| Freshness | `/dbt freshness` | Source data freshness checks |
| Debug | `/dbt debug` | Systematic troubleshooting |
| Audit | `/dbt audit` | Proactive health checks |

### v1 Nice-to-Have

| Skill | Command | Description |
|---|---|---|
| Develop | `/dbt develop` | Scaffold, compile, preview, lineage |
| Docs | `/dbt docs` | Generate and audit documentation |
| Artifacts | `/dbt artifacts` | Parse and compare run outputs |
| Seed & Snapshot | `/dbt seed` | Seed loading, SCD snapshots |

### v2 (Deferred)

- **Brainstorming** — Model design exploration
- **Executing Plans** — Step-by-step with dbt checkpoints
- **Code Review** — SQL quality and best practices

## Configuration

After running `/dbt setup`, a `.dbt-toolkit/config.yaml` is created alongside your `dbt_project.yml`:

```yaml
version: 1

execution:
  method: "local"  # or "ssh" or "docker"

profile:
  name: "my_profile"
  target: "dev"

defaults:
  threads: 4
  full_refresh: false
  fail_fast: false
```

See `templates/config.yaml` for all options.

## Execution Methods

- **Local:** dbt installed on your machine
- **SSH:** dbt on a remote server (auto-handles env vars, venv activation)
- **Docker:** dbt in a container (auto-mounts volumes)

## Scripts

All scripts are importable Python modules:

| Script | Purpose |
|---|---|
| `config.py` | Config discovery and typed access |
| `runner.py` | Execute dbt via local/SSH/Docker |
| `artifacts.py` | Parse manifest, run_results, sources |
| `lineage.py` | DAG traversal from manifest |
| `freshness.py` | Freshness tracking with history |
| `coverage.py` | Test and doc coverage analysis |
| `audit.py` | Health checks (coverage, sort/dist, tags) |
| `selector.py` | Build node selection strings |
| `cli.py` | Unified CLI entry point |
| `logger.py` | Structured logging with secret sanitization |

## Development

```bash
cd dbt-toolkit
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## Requirements

- Python >= 3.9
- dbt-core >= 1.5 (unit tests require >= 1.8)
- Any dbt adapter (Redshift enhancements activate automatically)

## License

BUSL-1.1 (converts to Apache 2.0 on 2030-03-15)
