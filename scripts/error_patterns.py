"""Error pattern matching for dbt/Redshift errors."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ErrorMatch:
    """A matched error pattern with diagnosis and suggestions."""

    pattern: str
    category: str  # connection, compilation, runtime_sql, permission, performance, parse, redshift, incremental
    description: str
    suggestions: List[str] = field(default_factory=list)


# Error pattern database: (regex, category, description, suggestions)
_PATTERNS = [
    # Connection errors
    (
        r"could not connect to server|Connection refused|Connection timed out",
        "connection",
        "Database connection failed",
        [
            "Run `dbt debug` to verify connection settings",
            "Check that the database server is running and accessible",
            "Verify profile credentials in ~/.dbt/profiles.yml",
            "For SSH: check that the remote server is reachable",
        ],
    ),
    (
        r"password authentication failed|Access Denied|authentication failed",
        "connection",
        "Authentication failure",
        [
            "Verify credentials in ~/.dbt/profiles.yml or environment variables",
            "Check that the user has login permissions",
            "For Redshift: verify IAM role if using IAM auth",
        ],
    ),
    # Compilation errors
    (
        r"Compilation Error.*'ref' is undefined|Compilation Error.*'source' is undefined",
        "compilation",
        "Jinja compilation error — undefined reference function",
        [
            "Check for typos in ref() or source() calls",
            "Ensure referenced model exists and is not disabled",
            "Run `dbt deps` if using macros from packages",
        ],
    ),
    (
        r"Compilation Error.*Node.*not found|model.*was not found",
        "compilation",
        "Referenced model or node not found",
        [
            "Check the model name in ref() — it's case-sensitive",
            "Verify the model file exists and is not in a disabled directory",
            "Run `dbt parse` to rebuild the manifest",
            "If in a package: run `dbt deps` first",
        ],
    ),
    (
        r"Compilation Error.*circular",
        "compilation",
        "Circular reference detected in model DAG",
        [
            "Check ref() calls for circular dependencies",
            "Use `dbt ls --select +model_name+` to visualize the dependency chain",
            "Consider breaking the cycle by extracting a shared intermediate model",
        ],
    ),
    # Runtime SQL errors
    (
        r"relation.*does not exist|table.*not found|Unknown table",
        "runtime_sql",
        "Referenced table or relation does not exist",
        [
            "The upstream model may not have been run yet — try `dbt run --select +model_name`",
            "Check if the schema name is correct in your profile target",
            "For late binding views: the underlying table may have been dropped",
            "Run `dbt run --full-refresh` if the table was manually dropped",
        ],
    ),
    (
        r"duplicate key value violates unique constraint",
        "runtime_sql",
        "Duplicate key violation — likely an incremental model issue",
        [
            "Check that `unique_key` in the model config matches the actual grain",
            "If unique_key has NULLs, those rows won't be deduped (Redshift delete+insert)",
            "Add a `not_null` test on the unique_key columns",
            "Consider running `dbt run --full-refresh --select model_name` to rebuild cleanly",
        ],
    ),
    (
        r"column.*does not exist|Unknown column",
        "runtime_sql",
        "Referenced column not found in table",
        [
            "Check for column name typos in your SQL",
            "The upstream model schema may have changed — run `dbt run --select +model_name`",
            "For incremental models with `on_schema_change: ignore`, new columns won't appear",
            "Run `--full-refresh` if the column was recently added to an incremental model",
        ],
    ),
    (
        r"No space left on device|disk full|out of disk",
        "runtime_sql",
        "Disk space exhausted",
        [
            "For Redshift: check cluster storage with `SELECT * FROM stv_partitions`",
            "Run `VACUUM DELETE ONLY` to reclaim space from deleted rows",
            "Consider resizing the cluster or using RA3 nodes",
            "For local: free up disk space or increase volume size",
        ],
    ),
    # Permission errors
    (
        r"permission denied|Access denied|not authorized|insufficient privilege",
        "permission",
        "Insufficient permissions to access resource",
        [
            "Verify the dbt user has required grants: SELECT, CREATE, DROP on target schema",
            "For Redshift: check schema ownership and USAGE grants",
            "Run `GRANT ALL ON SCHEMA <schema> TO <user>`",
            "For Spectrum: verify IAM role has S3 read access",
        ],
    ),
    # Performance errors
    (
        r"statement timeout|canceling statement due to.*timeout|query.*timed out",
        "performance",
        "Query timed out — likely a performance issue",
        [
            "Check if the model needs sort/dist key optimization",
            "Review the compiled SQL for full table scans or cross joins",
            "Consider materializing upstream models as tables instead of views",
            "Increase `statement_timeout` in Redshift WLM queue if appropriate",
            "For large models: add WHERE filters or partition the data",
        ],
    ),
    (
        r"serializable isolation violation|concurrent transaction",
        "performance",
        "Concurrent transaction conflict",
        [
            "Another process is modifying the same table",
            "Consider scheduling dbt runs to avoid overlap",
            "For Redshift: check STL_TR_CONFLICT for details",
        ],
    ),
    # Parse errors
    (
        r"YAMLError|yaml\.scanner|mapping values are not allowed",
        "parse",
        "YAML parsing error in model or schema file",
        [
            "Check for indentation issues in .yml files",
            "Ensure no tabs are used (YAML requires spaces)",
            "Look for unquoted special characters (colons, brackets) in values",
            "Validate the YAML with an online parser",
        ],
    ),
    (
        r"Jinja.*Error|UndefinedError|TemplateSyntaxError",
        "parse",
        "Jinja template error",
        [
            "Check for unclosed Jinja blocks ({% %} or {{ }})",
            "Verify macro names are correct and available",
            "Run `dbt deps` if the macro is from a package",
            "Check for Jinja syntax: use `{% endif %}` not `{% end if %}`",
        ],
    ),
    # Redshift-specific
    (
        r"Relation.*already exists.*spectrum|tmp.*already exists",
        "redshift",
        "Spectrum CTAS collision — duplicate internal staging relation",
        [
            "This happens when a CTE references a Spectrum table and is used by multiple downstream CTEs",
            "Fix: ensure the Spectrum table is scanned only once via a linear CTE chain",
            "Use CROSS JOIN unpivot technique instead of branching CTEs from Spectrum source",
            "See references/redshift-specifics.md for the full workaround",
        ],
    ),
    (
        r"Invalid operation.*MERGE|MERGE.*not supported",
        "redshift",
        "Redshift does not support MERGE statements",
        [
            "Use `delete+insert` strategy instead of `merge` for incremental models",
            "Set `incremental_strategy='delete+insert'` in model config",
            "This is the default for Redshift — check if it was overridden",
        ],
    ),
    # Incremental model issues
    (
        r"incremental.*full.?refresh|schema.*change.*detected",
        "incremental",
        "Incremental model needs full refresh",
        [
            "Run `dbt run --full-refresh --select model_name` to rebuild",
            "Check `on_schema_change` config if columns were added/removed",
            "Review the model's unique_key — if it changed, full refresh is needed",
        ],
    ),
]


def match_error(error_text: str) -> Optional[ErrorMatch]:
    """Match an error string against known patterns.

    Args:
        error_text: The error message from dbt output or run_results.json

    Returns:
        ErrorMatch if a pattern matches, None otherwise
    """
    for pattern, category, description, suggestions in _PATTERNS:
        if re.search(pattern, error_text, re.IGNORECASE):
            return ErrorMatch(
                pattern=pattern,
                category=category,
                description=description,
                suggestions=suggestions,
            )
    return None
