# Contributing to dbt-toolkit

## Development Setup

```bash
git clone https://github.com/rishavchatterjee/dbt-toolkit.git
cd dbt-toolkit
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## Adding a Skill

1. Create `skills/<skill-name>/SKILL.md` with frontmatter:
   ```yaml
   ---
   name: <skill-name>
   description: "One-line description"
   ---
   ```
2. Follow the Conversation Principles: never ask technical/infra questions — only business intent
3. Add routing logic to `skills/dbt/SKILL.md`
4. Reference relevant `references/*.md` docs

## Design Principles

- **Business questions only** — skills never ask CLI flags, config syntax, or YAML formatting
- **Auto-resolve** — derive everything from config + project state
- **Fail safe** — every external call has retries, timeouts, and error handling
- **DRY** — reuse scripts modules, don't duplicate logic in skills
- **TDD** — write failing tests first, then implement

## Code Style

- Linted with [ruff](https://docs.astral.sh/ruff/)
- Run `ruff check .` and `ruff format --check .` before committing
- Type hints encouraged but not required

## Pull Request Process

1. Fork the repo and create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass: `python -m pytest tests/ -v`
4. Ensure linting passes: `ruff check . && ruff format --check .`
5. Open a PR against `main`
