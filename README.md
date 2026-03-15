<p align="center">
  <img src="https://img.shields.io/badge/Claude_Code-Plugin-blueviolet?style=for-the-badge" alt="Claude Code Plugin" />
  <img src="https://img.shields.io/badge/dbt-Toolkit-orange?style=for-the-badge" alt="dbt Toolkit" />
  <img src="https://img.shields.io/badge/version-0.1.0-green?style=for-the-badge" alt="Version 0.1.0" />
  <img src="https://img.shields.io/badge/license-BUSL_1.1-blue?style=for-the-badge" alt="License" />
</p>

# dbt-toolkit

**Stop guessing at dbt.** A Claude Code plugin that makes dbt development safe, systematic, and mistake-proof.

One command — `/dbt-toolkit:dbt` — gives your team smart model selection, execution across local/SSH/Docker, automatic error diagnosis, lineage analysis, test coverage tracking, and freshness monitoring. No more hunting through logs, memorizing CLI flags, or forgetting which models to run.

---

## Install

```bash
# From the Claude Code official marketplace
/plugin install dbt-toolkit

# Or install directly from GitHub
/plugin install github:rishavchatterjee/dbt-toolkit
```

**Prerequisites:** Python 3.9+ and [Claude Code](https://claude.ai/code) with plugin support.

---

## How It Works

```
You say:                              dbt-toolkit does:
───────────────────────────────────── ──────────────────────────────────────
/dbt-toolkit:dbt run                  Config → Selector → Execute → Parse results
/dbt-toolkit:dbt test                 Run tests → Analyze failures → Coverage report
/dbt-toolkit:dbt freshness            Check sources → Track history → Warn on stale
/dbt-toolkit:dbt debug                Error patterns → Root cause → Suggested fix
/dbt-toolkit:dbt "run my revenue      NLP routing → Same safe workflow
  models"
```

### The Execution Flow

```
                    ┌─────────────────────────────────────────┐
                    │       /dbt-toolkit:dbt run               │
                    └────────────────┬────────────────────────┘
                                     │
                    ┌────────────────▼────────────────────────┐
                    │  1. Load config (.dbt-toolkit/config.yaml│
                    │  2. Build selector (tag:, path:, config:)│
                    │  3. Detect execution method              │
                    └────────────────┬────────────────────────┘
                                     │
                          ┌──────────┴──────────┐
                          │                     │
                    ┌─────▼──────┐  ┌───────────▼──┐  ┌──────▼─────┐
                    │   Local    │  │     SSH      │  │   Docker   │
                    │  (direct)  │  │  (remote)    │  │ (container)│
                    └─────┬──────┘  └──────┬───────┘  └──────┬─────┘
                          │                │                  │
                    ┌─────▼────────────────▼──────────────────▼─────┐
                    │  4. Parse run_results.json                     │
                    │  5. Match errors against 17 patterns           │
                    │  6. Report: successes, failures, slowest model │
                    └───────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Install the plugin
/plugin install dbt-toolkit

# 2. Navigate to your dbt project
cd my-dbt-project

# 3. Run the toolkit
/dbt-toolkit:dbt
```

Setup auto-detects your `dbt_project.yml` and walks you through configuration: execution method, profile, target, and defaults.

---

## Features

| Feature | What it does |
|---------|-------------|
| **Smart routing** | `/dbt-toolkit:dbt` + anything — natural language or direct commands |
| **3 execution methods** | Local, SSH (auto-handles venv + env vars), Docker (auto-mounts volumes) |
| **17 error patterns** | Auto-match errors across 8 categories with suggested fixes |
| **DAG lineage** | Traverse upstream/downstream, calculate impact radius |
| **Test coverage** | Track test-to-model ratios, flag undocumented models |
| **Freshness tracking** | Monitor source staleness with history and warnings |
| **Secret sanitization** | Passwords, tokens, and keys never appear in logs |
| **Audit health checks** | Sort/dist keys, materialization, test coverage, tags |
| **Scaffolding templates** | Model, test, unit test, config templates |

---

## Skills (16)

| # | Skill | Invoke with | Purpose |
|---|-------|-------------|---------|
| 1 | Router | `/dbt-toolkit:dbt` | Interactive menu + NLP routing |
| 2 | Setup | `/dbt-toolkit:dbt-setup` | First-time configuration wizard |
| 3 | Run | `/dbt-toolkit:dbt-run` | Execute models with smart selection |
| 4 | Test | `/dbt-toolkit:dbt-test` | Run tests, analyze failures, coverage |
| 5 | Freshness | `/dbt-toolkit:dbt-freshness` | Source data freshness checks |
| 6 | Debug | `/dbt-toolkit:dbt-debug` | Systematic troubleshooting |
| 7 | Audit | `/dbt-toolkit:dbt-audit` | Proactive health checks |
| 8 | Develop | `/dbt-toolkit:dbt-develop` | Scaffold, compile, preview, lineage |
| 9 | Docs | `/dbt-toolkit:dbt-docs` | Generate and audit documentation |
| 10 | Artifacts | `/dbt-toolkit:dbt-artifacts` | Parse and compare run outputs |
| 11 | Seed & Snapshot | `/dbt-toolkit:dbt-seed-snapshot` | Seed loading, SCD snapshots |
| 12 | Deps | `/dbt-toolkit:dbt-deps` | Package management |
| 13 | Run Operation | `/dbt-toolkit:dbt-run-operation` | Execute dbt macros |
| 14 | Brainstorm | `/dbt-toolkit:dbt-brainstorming` | Model design exploration |
| 15 | Execute Plans | `/dbt-toolkit:dbt-executing-plans` | Step-by-step with dbt checkpoints |
| 16 | Code Review | `/dbt-toolkit:dbt-code-review` | SQL quality and best practices |

Or just describe what you want:

```
/dbt-toolkit:dbt run my revenue models
/dbt-toolkit:dbt why did my test fail?
/dbt-toolkit:dbt what depends on stg_orders?
```

---

## Execution Methods

**Local** — dbt installed on your machine. Runs directly.

**SSH** — dbt on a remote server. Auto-handles:
- SSH key authentication
- Virtual environment activation
- Environment variable forwarding
- Remote project path resolution

**Docker** — dbt in a container. Auto-handles:
- Volume mounting for project files
- Image management
- Adapter-specific images

---

## Error Patterns

17 patterns across 8 categories with auto-matching and suggested fixes:

| Category | Patterns | Example |
|----------|----------|---------|
| Connection | 3 | Refused, timeout, authentication failure |
| Compilation | 3 | Undefined ref, missing node, circular dependency |
| Runtime SQL | 4 | Relation not found, duplicate key, missing column, disk full |
| Permission | 2 | Access denied, insufficient privileges |
| Performance | 2 | Statement timeout, serializable isolation |
| Parse | 1 | YAML/Jinja syntax errors |
| Redshift | 1 | Spectrum CTAS, MERGE not supported |
| Incremental | 1 | Schema change, full refresh needed |

---

## Lineage

Traverse the DAG from `manifest.json`:

- **Upstream:** What does this model depend on?
- **Downstream:** What breaks if I change this model?
- **Impact radius:** How many models are affected?

Used by the run, develop, and audit skills to build smart selectors and assess change impact.

---

## Configuration

Created by `/dbt-toolkit:dbt-setup` at `.dbt-toolkit/config.yaml`:

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
  log_format: "json"

freshness:
  enabled: true
  warn_after_hours: 24

audit:
  check_sort_dist: true
  check_test_coverage: true
  min_test_coverage: 0.8
```

See `templates/config.yaml` for all options including SSH and Docker configuration.

<details>
<summary><strong>Telemetry (optional)</strong></summary>

Anonymous, opt-in usage telemetry via PostHog. Inert unless configured:

```bash
export POSTHOG_API_KEY="your-posthog-project-key"
```

Also requires `telemetry.enabled: true` in config. No data is ever sent without both conditions met.

</details>

---

## Architecture

```
dbt-toolkit/
├── .claude-plugin/           Plugin metadata (plugin.json, marketplace.json)
├── hooks/                    Session auto-detection
├── skills/                   16 skills (each with SKILL.md)
│   ├── dbt/                  Router — single entry point
│   ├── dbt-setup/            First-time wizard
│   ├── dbt-run/              Execute models with smart selection
│   ├── dbt-test/             Run tests, analyze failures, coverage
│   ├── dbt-freshness/        Source data freshness checks
│   ├── dbt-debug/            Systematic troubleshooting
│   ├── dbt-audit/            Proactive health checks
│   ├── dbt-develop/          Scaffold, compile, preview, lineage
│   ├── dbt-docs/             Generate and audit documentation
│   ├── dbt-artifacts/        Parse and compare run outputs
│   ├── dbt-seed-snapshot/    Seed loading, SCD snapshots
│   ├── dbt-deps/             Package management
│   ├── dbt-run-operation/    Execute dbt macros
│   ├── dbt-brainstorming/    Model design exploration
│   ├── dbt-executing-plans/  Plan execution with checkpoints
│   └── dbt-code-review/      SQL quality and best practices
├── agents/                   Lineage + test-failure analysis agents
├── references/               dbt knowledge base (7 docs)
├── scripts/                  Python automation (13 modules)
│   ├── config.py             Config discovery and typed access
│   ├── runner.py             Execute dbt via local/SSH/Docker
│   ├── artifacts.py          Parse manifest, run_results, sources
│   ├── lineage.py            DAG traversal from manifest
│   ├── freshness.py          Freshness tracking with history
│   ├── coverage.py           Test and doc coverage analysis
│   ├── audit.py              Health checks (coverage, sort/dist, tags)
│   ├── selector.py           Build node selection strings
│   ├── error_patterns.py     17 patterns across 8 categories
│   ├── state.py              State comparison for CI/CD slim runs
│   ├── cli.py                Unified CLI entry point
│   ├── logger.py             Structured logging + secret sanitization
│   ├── telemetry.py          Anonymous opt-in telemetry
│   └── bootstrap.sh          Environment detection script
├── templates/                Project scaffolding files
└── tests/                    Test suite (unit + integration)
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `PyYAML` | YAML parsing |
| `paramiko` | SSH execution |
| `click` | CLI framework |
| `rich` | Terminal formatting |
| `posthog` | Anonymous opt-in telemetry |

---

## For Contributors

### Running tests

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

### Design Principles

- **Business questions only** — skills never ask CLI flags, config syntax, or YAML formatting
- **Auto-resolve** — derive everything from config + project state
- **Fail safe** — every external call has retries, timeouts, and error handling
- **3 execution methods** — local, SSH, Docker — same skill logic regardless
- **Secret sanitization** — passwords and tokens never reach logs

### Adding a skill

1. Create `skills/your-skill/SKILL.md` with `name` and `description` frontmatter
2. Follow the Conversation Principles (never ask technical questions)
3. Add routing logic to `skills/dbt/SKILL.md`
4. Reference relevant `references/*.md` docs

---

## License

Business Source License 1.1 — see [LICENSE](LICENSE) for details.
Converts to Apache License 2.0 on 2030-03-15.
