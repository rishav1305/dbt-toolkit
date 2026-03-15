# dbt-toolkit Plugin Marketplace Restructure

**Date:** 2026-03-15
**Status:** Approved
**Goal:** Restructure dbt-toolkit to match preset-toolkit's plugin structure for Claude Code marketplace publication, upgrade README, replicate LICENSE format, and add CI/CD scaffolding.

---

## Context

dbt-toolkit is a 16-skill Claude Code plugin for dbt project management. It works but its packaging doesn't match the marketplace-ready structure of preset-toolkit. The user wants to publish it publicly on the Claude Code plugin marketplace.

### Current State
- Root `plugin.json` duplicated in `.claude-plugin/`
- No `marketplace.json`
- No `docs/superpowers/` directory
- No test fixtures directory
- No CI/CD workflows
- No `CONTRIBUTING.md` or `CHANGELOG.md`
- README is functional but not marketplace-polished
- LICENSE uses a custom BUSL-1.1 wording (not the official MariaDB template)
- Missing `telemetry.py`, `deps.py`, `http.py` scripts

### Target State
- Structure mirrors preset-toolkit exactly
- Marketplace-ready with `marketplace.json`
- Professional README with badges, ASCII diagrams, feature tables
- Official BUSL-1.1 license template
- CI/CD with GitHub Actions
- Test fixtures for cleaner test organization
- Telemetry, dependency management, and HTTP retry modules

---

## Changes

### 1. Plugin Packaging

**Remove:**
- `/plugin.json` (root) — keep only `.claude-plugin/plugin.json`

**Add:**
- `.claude-plugin/marketplace.json`:
```json
{
  "name": "dbt-toolkit",
  "owner": {
    "name": "Rishav Chatterjee",
    "email": "rishav.chatterjee@weather.com"
  },
  "plugins": [
    {
      "name": "dbt-toolkit",
      "source": "./",
      "description": "Workflow-oriented dbt project management for Claude Code",
      "version": "0.1.0"
    }
  ]
}
```

**Add directories:**
- `docs/superpowers/plans/.gitkeep`
- `docs/superpowers/specs/` (this file lives here)

### 2. New Python Modules

**`scripts/telemetry.py`**
Anonymous opt-in PostHog telemetry. Requires both:
- `POSTHOG_API_KEY` environment variable
- `telemetry.enabled: true` in `.dbt-toolkit/config.yaml`

No data sent unless both conditions met. Tracks: skill invocations, execution method used, error categories encountered.

**`scripts/deps.py`**
Dependency management utilities:
- Check if required packages are installed
- Validate version constraints
- Report missing dependencies with install instructions

**`scripts/http.py`**
HTTP retry with exponential backoff + jitter:
- Configurable max retries, base delay, max delay
- Retry on 429, 500, 502, 503, 504
- Used by telemetry module and available for future API integrations

### 3. CI/CD Scaffolding

**`.github/workflows/test.yml`**
- Trigger: push to main, pull requests
- Matrix: Python 3.9, 3.10, 3.11, 3.12
- Steps: checkout, setup-python, install deps, run pytest with coverage

**`.github/workflows/lint.yml`**
- Trigger: push to main, pull requests
- Steps: checkout, setup-python, install ruff, run ruff check + ruff format --check

**`CONTRIBUTING.md`**
Sections:
- Development setup (venv, install, tests)
- Adding a skill (create SKILL.md, add routing, reference docs)
- Design principles (business questions only, no yaml.dump, fail safe)
- Code style (ruff, type hints encouraged)
- Pull request process

**`CHANGELOG.md`**
- Unreleased section (for ongoing work)
- 0.1.0 section listing initial release features (16 skills, 13 scripts, 7 references, 2 agents)

### 4. README Rewrite

Full rewrite following preset-toolkit's format:

1. **Badge row** (centered): Claude Code Plugin, dbt Toolkit, version 0.1.0, tests passing, license BUSL-1.1
2. **Tagline**: "Stop guessing at dbt. A Claude Code plugin that makes dbt development safe, systematic, and mistake-proof."
3. **Install**: marketplace + GitHub install commands
4. **How It Works**: ASCII workflow diagram showing `/dbt run` flow through config detection, selector building, execution, result parsing
5. **Quick Start**: 3-step (install, navigate, `/dbt-toolkit:dbt`)
6. **Features table**: Smart routing, 3 execution methods, 17 error patterns, DAG lineage, test coverage, freshness tracking, secret sanitization, audit health checks, scaffolding templates
7. **Skills table**: All 16 skills, numbered, with invoke command and purpose (flat — no v1/v2 categories)
8. **Execution Methods**: Local, SSH, Docker — brief explanation of each
9. **Error Patterns**: 8 categories, auto-matching, suggested fixes
10. **Lineage**: DAG traversal, impact analysis, upstream/downstream
11. **Configuration**: config.yaml example with key options
12. **Telemetry** (collapsible): opt-in, PostHog, dual-gate
13. **Architecture**: Full directory tree + dependency table
14. **For Contributors**: Tests, design principles, adding skills
15. **License**: BUSL-1.1 with change date

### 5. LICENSE Rewrite

Replace with official MariaDB BUSL-1.1 template (matching preset-toolkit), with parameters:
- Licensor: Rishav Chatterjee
- Licensed Work: dbt-toolkit 0.1.0
- Change Date: 2030-03-15
- Change License: Apache License 2.0
- Additional Use Grant: None
- Copyright: Copyright (c) 2026 Rishav Chatterjee

### 6. Test Fixtures

Add `tests/fixtures/` with:
- `sample_manifest.json` — 2-3 nodes with parent_map/child_map for lineage tests
- `sample_run_results.json` — 3 results (pass, fail, warn) for artifacts tests
- `sample_config.yaml` — valid config with local execution for config tests
- `sample_sources.json` — 1-2 sources with freshness metadata
- `sample_dbt_project.yml` — minimal dbt_project.yml for integration tests

Existing tests unchanged — fixtures are additive for future test migration.

### 7. Minor Modifications

**`pyproject.toml`:**
- Add `[tool.setuptools.packages.find]` with `include = ["scripts*"]`
- Add `posthog>=3.0` and `httpx>=0.24` to dependencies
- Add `ruff>=0.3` to dev dependencies

**`templates/gitignore.template`:**
- Standard Python ignores (__pycache__, .venv, *.egg-info, dist, build)
- dbt-toolkit specifics (.dbt-toolkit/.secrets/, .dbt-toolkit/cache/)
- IDE files (.vscode, .idea)

**`.gitignore`:**
- Add `.github/` workflow caches if any

---

## What Does NOT Change

- All 16 skills (skills/ directory untouched)
- All existing scripts (scripts/*.py — only new files added)
- Both agents (agents/*.md)
- All 7 references (references/*.md)
- All existing templates (templates/ — only gitignore.template added)
- Hooks (hooks/ directory untouched)
- Existing 14 test modules (tests/test_*.py)

---

## File Inventory

### Remove (1 file)
| File | Reason |
|---|---|
| `plugin.json` (root) | Duplicate — `.claude-plugin/plugin.json` is canonical |

### Add (19 files)
| File | Purpose |
|---|---|
| `.claude-plugin/marketplace.json` | Marketplace registry |
| `scripts/telemetry.py` | Anonymous opt-in PostHog telemetry |
| `scripts/deps.py` | Dependency checking and validation |
| `scripts/http.py` | HTTP retry with backoff + jitter |
| `.github/workflows/test.yml` | CI: pytest on Python 3.9-3.12 |
| `.github/workflows/lint.yml` | CI: ruff linting |
| `CONTRIBUTING.md` | Contributor guide |
| `CHANGELOG.md` | Version history |
| `templates/gitignore.template` | .gitignore scaffold for user projects |
| `docs/superpowers/plans/.gitkeep` | Directory placeholder |
| `docs/superpowers/specs/` | This spec lives here |
| `tests/fixtures/sample_manifest.json` | Test fixture: manifest |
| `tests/fixtures/sample_run_results.json` | Test fixture: run results |
| `tests/fixtures/sample_config.yaml` | Test fixture: config |
| `tests/fixtures/sample_sources.json` | Test fixture: sources |
| `tests/fixtures/sample_dbt_project.yml` | Test fixture: dbt project |
| `tests/fixtures/__init__.py` | Package marker |

### Rewrite (2 files)
| File | Change |
|---|---|
| `README.md` | Full rewrite — preset-toolkit format |
| `LICENSE` | Official MariaDB BUSL-1.1 template |

### Modify (2 files)
| File | Change |
|---|---|
| `pyproject.toml` | Add setuptools.packages.find, new deps, ruff |
| `.gitignore` | Minor additions |

---

## Risks

- **Low:** Removing root `plugin.json` — Claude Code reads from `.claude-plugin/` so this is safe
- **Low:** New scripts are additive — no existing code depends on them yet
- **None:** Existing skills, scripts, and tests are untouched
