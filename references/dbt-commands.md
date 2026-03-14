# dbt Commands Reference

Complete reference for all 19 dbt CLI commands, including key flags, outputs, and exit codes.

## Core Execution Commands

### dbt run

Execute models in dependency order, materializing them in the database.

**Key Flags:**
- `--select MODEL_NAME` — Run specific model(s) and upstream dependencies
- `--exclude MODEL_NAME` — Exclude model(s)
- `--full-refresh` — Rebuild incremental models as full tables
- `--threads N` — Parallel threads (default: 4)
- `--target TARGET_NAME` — Override dbt_project.yml target
- `--fail-fast` — Stop on first failure (default: continue)
- `--select state:modified` — Run only modified models (requires `--state` path)

**Artifacts Produced:**
- `run_results.json` — Execution results per node
- Compiled SQL in `target/compiled/`

**Exit Codes:**
- `0` — All models ran successfully
- `1` — One or more models failed
- `2` — Unhandled error (parsing, connection, etc.)

---

### dbt test

Run tests (singular and generic) against models and sources.

**Key Flags:**
- `--select MODEL_NAME` — Test specific model(s)
- `--exclude MODEL_NAME` — Exclude model(s)
- `--store-failures` — Store failed rows in a table for debugging
- `--indirect-selection` — Include tests on columns referenced by modified models
- `--target TARGET_NAME` — Override target

**Artifacts Produced:**
- `run_results.json` — Test results per node
- Optional: `dbt_expectations` table with failed rows (if `--store-failures`)

**Exit Codes:**
- `0` — All tests passed
- `1` — One or more tests failed
- `2` — Unhandled error

---

### dbt build

Execute models, tests, snapshots, and seeds in DAG order.

**Key Flags:**
- Same as `dbt run` + `dbt test` combined
- `--select`, `--exclude`, `--full-refresh`, `--threads`, `--fail-fast`

**Artifacts Produced:**
- `run_results.json` — Combined results for all node types

**Exit Codes:**
- `0` — All succeeded
- `1` — One or more failed
- `2` — Unhandled error

---

## Compilation & Analysis

### dbt compile

Parse and compile all models and tests without executing them.

**Key Flags:**
- `--select MODEL_NAME` — Compile specific model(s)
- `--parse-only` — Skip compilation, only parse (faster)

**Artifacts Produced:**
- `manifest.json` — Complete project DAG
- Compiled SQL in `target/compiled/`

**Exit Codes:**
- `0` — Compilation successful
- `1` — Compilation error(s)
- `2` — Unhandled error

---

### dbt parse

Parse the project and generate a manifest without a warehouse connection.

**Key Flags:**
- None (manifest is always generated)

**Artifacts Produced:**
- `manifest.json` — Project DAG and metadata

**Exit Codes:**
- `0` — Parse successful
- `1` — Parse error(s)

**Use Case:** Validate project structure before running expensive commands.

---

### dbt show

Preview query results from a model or inline SQL.

**Key Flags:**
- `--select MODEL_NAME` — Preview specific model (one at a time)
- `--inline "SELECT ..."` — Preview raw SQL (one query)
- `--limit N` — Limit rows (default: 5)
- **Note:** `--select` and `--inline` are mutually exclusive

**Artifacts Produced:**
- Console output only

**Exit Codes:**
- `0` — Query successful
- `1` — Query failed

**Limitation:** Does not support Python models; SQL only.

---

## Documentation & Data Inspection

### dbt docs generate

Generate dbt documentation and data catalog.

**Key Flags:**
- None (uses all models/sources/macros in project)

**Artifacts Produced:**
- `catalog.json` — Column types, row counts, table stats
- `manifest.json` — Project structure
- `index.html` — HTML documentation (in `target/`)

**Exit Codes:**
- `0` — Generation successful
- `1` — Generation error(s)

---

### dbt docs serve

Serve dbt documentation on a local HTTP server.

**Key Flags:**
- `--port PORT` — Port to serve on (default: 8080)
- `--no-browser` — Skip opening browser

**Usage:**
```bash
dbt docs serve
# Opens http://localhost:8080 in browser
```

**Exit Codes:**
- `0` — Server stopped gracefully
- `1` — Server error

---

### dbt source freshness

Check when sources were last updated.

**Key Flags:**
- `--select SOURCE_NAME` — Check specific source(s)

**Artifacts Produced:**
- `sources.json` — Per-source freshness results

**Exit Codes:**
- `0` — All sources fresh
- `1` — One or more sources stale or error

**Output Fields:**
- `max_loaded_at` — Most recent data timestamp
- `max_loaded_at_time_ago_in_s` — Seconds since last update

---

## Data Loading

### dbt seed

Load CSV files from `data/` directory into the database.

**Key Flags:**
- `--select SEED_NAME` — Load specific seed(s)
- `--full-refresh` — Rebuild seed tables (drop and recreate)
- `--threads N` — Parallel threads

**Artifacts Produced:**
- `run_results.json` — Seed load results
- Database tables

**Exit Codes:**
- `0` — All seeds loaded successfully
- `1` — One or more seeds failed
- `2` — Unhandled error

---

### dbt snapshot

Capture point-in-time snapshots of mutable tables.

**Key Flags:**
- `--select SNAPSHOT_NAME` — Run specific snapshot(s)
- `--threads N` — Parallel threads

**Artifacts Produced:**
- `run_results.json` — Snapshot execution results
- `scd_type_2` tables with versioning

**Exit Codes:**
- `0` — All snapshots successful
- `1` — One or more snapshots failed

---

## Utility Commands

### dbt debug

Test dbt configuration and database connection without executing models.

**Key Flags:**
- None (no `--select` support)

**Output:**
- Connection test results
- dbt version and adapter info
- Active profile/target

**Exit Codes:**
- `0` — Connection successful
- `1` — Connection or config error

---

### dbt deps

Install packages defined in `packages.yml` or `dependencies.yml`.

**Key Flags:**
- `--no-lock` — Skip lock file generation (dbt 1.8+, speeds up installs in CI)

**Configuration:**
- Reads: `packages.yml` or `dependencies.yml` in project root
- Installs to: `dbt_packages/` directory
- Lock file: `packages.lock.yml` (or skipped with `--no-lock`)

**Must Run Before:**
- `dbt parse` (if using external packages)
- `dbt compile`, `dbt run` (if packages define macros/sources)

**Artifacts Produced:**
- `dbt_packages/` directory with installed packages
- `packages.lock.yml` — Locked versions (unless `--no-lock` used)

**Exit Codes:**
- `0` — Installation successful
- `1` — Installation failed (missing packages, version conflicts, network error)

---

### dbt clean

Delete build artifacts and logs.

**Key Flags:**
- None

**Deletes:**
- `target/` — Compiled SQL, artifacts
- `dbt_packages/` — External packages
- `logs/` — Execution logs

**Exit Codes:**
- `0` — Cleanup successful

---

### dbt init

Create a new dbt project with skeleton structure.

**Key Flags:**
- `--project-name NAME` — Project name
- `--adapter ADAPTER` — Database adapter (snowflake, redshift, postgres, etc.)

**Creates:**
- Project directory with boilerplate
- `dbt_project.yml`
- `models/` directory with example model
- `profiles.yml` template

**Exit Codes:**
- `0` — Project created successfully
- `1` — Creation error

---

## List & Query Commands

### dbt ls / dbt list

List resources (models, tests, sources, exposures) matching selectors.

**Key Flags:**
- `--select MODEL_NAME` — Filter by selector
- `--resource-type TYPE` — Filter by type (model, test, source, exposure, etc.)
- `--output json|name|path` — Output format
- `--exclude MODEL_NAME` — Exclude resources

**Artifacts Produced:**
- Console output only

**Example:**
```bash
dbt ls --select tag:daily --resource-type model --output json
```

**Exit Codes:**
- `0` — Query successful
- `1` — Query error

---

### dbt retry

Re-run nodes that failed in the previous execution.

**Key Flags:**
- `--threads N` — Parallel threads
- `--fail-fast` — Stop on first failure

**Reads:** `run_results.json` from previous run

**Exit Codes:**
- `0` — All retried nodes succeeded
- `1` — One or more retried nodes failed
- `2` — No previous run_results.json found

**Note:** Targets nodes with `error` or `fail` status from most recent run.

---

## Advanced Commands

### dbt run-operation

Execute a macro without a model context.

**Key Flags:**
- `--macro MACRO_NAME` — Macro to execute (required)
- `--args '{"key": "value"}'` or `--args 'key: value'` — Pass arguments to macro (JSON or YAML inline)

**Arguments:**
- Arguments are passed as a dict to the macro
- JSON format: `--args '{"role": "analyst", "count": 5}'`
- YAML format: `--args 'role: analyst'` (simpler for single args)

**Artifacts Produced:**
- Console output from macro
- NO `run_results.json` (unlike `dbt run`, `dbt test`, etc.)

**Exit Codes:**
- `0` — Macro executed successfully
- `1` — Macro error or missing macro
- `2` — Unhandled error (connection, syntax, etc.)

**Common Use Cases:**
```bash
# Grant permissions
dbt run-operation grant_permissions --args '{"role": "analyst"}'

# Refresh snapshots
dbt run-operation refresh_snapshots --args '{"schema": "stg"}'

# Custom data quality checks
dbt run-operation run_checks --args 'table: my_model'
```

**Note:** Execution does NOT generate `run_results.json`. Capture output for CI/CD logging.

---

### dbt clone

Clone models from one environment to another (dbt 1.6+).

**Key Flags:**
- `--select MODEL_NAME` — Clone specific model(s)
- `--state PATH` — State directory to compare against

**Use Case:** Replicate production data structures to development/staging without re-running computations.

**Exit Codes:**
- `0` — Clone successful
- `1` — Clone error

---

## Summary Table

| Command | Purpose | Key Flags | Produces |
|---------|---------|-----------|----------|
| `run` | Execute models | `--select`, `--full-refresh`, `--threads` | `run_results.json`, compiled SQL |
| `test` | Run tests | `--select`, `--store-failures` | `run_results.json` |
| `build` | Run + test + snapshot | Same as run+test | `run_results.json` |
| `compile` | Parse and compile | `--select`, `--parse-only` | `manifest.json`, compiled SQL |
| `parse` | Generate manifest | None | `manifest.json` |
| `show` | Preview results | `--select` or `--inline` | Console output |
| `docs generate` | Generate docs | None | `catalog.json`, `manifest.json`, HTML |
| `docs serve` | Serve docs locally | `--port`, `--no-browser` | HTTP server |
| `source freshness` | Check source updates | `--select` | `sources.json` |
| `seed` | Load CSVs | `--select`, `--full-refresh` | `run_results.json`, database tables |
| `snapshot` | Capture SCD Type 2 | `--select` | `run_results.json`, snapshot tables |
| `debug` | Test connection | None | Console output |
| `deps` | Install packages | None | `dbt_packages/`, `packages.lock.yml` |
| `clean` | Delete artifacts | None | Deletes `target/`, `dbt_packages/`, `logs/` |
| `init` | Create project | `--project-name`, `--adapter` | Project directory |
| `ls` / `list` | List resources | `--select`, `--resource-type`, `--output` | Console output |
| `retry` | Re-run failures | `--threads`, `--fail-fast` | `run_results.json` |
| `run-operation` | Execute macro | `--macro`, `--args` | Console output or macro result |
| `clone` | Clone models | `--select`, `--state` | Cloned tables in target schema |
