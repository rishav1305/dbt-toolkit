# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Marketplace packaging (marketplace.json)
- Telemetry module (anonymous, opt-in via PostHog)
- Dependency checker module
- HTTP retry module with exponential backoff
- GitHub Actions CI (tests + linting)
- CONTRIBUTING.md
- Test fixtures (sample manifest, run_results, config, sources, dbt_project)

## [0.1.0] - 2026-03-15

### Added
- 16 skills: router, setup, run, test, freshness, debug, audit, develop, docs, artifacts, seed/snapshot, deps, run-operation, brainstorming, executing-plans, code-review
- 12 Python modules: config, runner, artifacts, lineage, freshness, coverage, audit, selector, error_patterns, state, cli, logger
- 2 agents: lineage-agent, test-failure-agent
- 7 reference documents: artifacts, common-pitfalls, dbt-commands, incremental-models, jinja-context, node-selection, redshift-specifics
- 5 templates: CLAUDE.md, config.yaml, model.sql, test.sql, unit_test.yaml
- Session-start hook for auto-detection
- 3 execution methods: local, SSH, Docker
- 17 error patterns across 8 categories
