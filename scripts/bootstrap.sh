#!/usr/bin/env bash
# Bootstrap dbt-toolkit: create venv, install deps, verify dbt.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${1:-.venv}"

# Python version
PYTHON_BIN=$(command -v python3 || command -v python)
if [ -z "$PYTHON_BIN" ]; then
    echo "ERROR: Python not found" >&2
    exit 1
fi
PYTHON_VERSION=$("$PYTHON_BIN" --version 2>&1 | sed 's/Python //')
echo "PYTHON_VERSION=$PYTHON_VERSION"

# Create venv if needed
if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

# Install plugin dependencies
pip install --quiet PyYAML>=6.0 paramiko>=3.0 click>=8.0 rich>=13.0

# Detect dbt
if command -v dbt &>/dev/null; then
    DBT_VERSION=$(dbt --version 2>&1 | sed -n 's/.*installed: \([0-9.]*\).*/\1/p' | head -1)
    [ -z "$DBT_VERSION" ] && DBT_VERSION=$(dbt --version 2>&1 | sed -n 's/.*Core: *\([0-9.]*\).*/\1/p' | head -1)
    [ -z "$DBT_VERSION" ] && DBT_VERSION="unknown"
    echo "DBT_VERSION=$DBT_VERSION"
else
    echo "DBT_VERSION=not_found"
fi

# Detect adapter
DBT_ADAPTER="unknown"
if pip list 2>/dev/null | grep -q "dbt-redshift"; then
    DBT_ADAPTER="redshift"
elif pip list 2>/dev/null | grep -q "dbt-postgres"; then
    DBT_ADAPTER="postgres"
elif pip list 2>/dev/null | grep -q "dbt-snowflake"; then
    DBT_ADAPTER="snowflake"
elif pip list 2>/dev/null | grep -q "dbt-bigquery"; then
    DBT_ADAPTER="bigquery"
fi
echo "DBT_ADAPTER=$DBT_ADAPTER"

# Test connection (if dbt_project.yml exists in CWD)
if [ -f "dbt_project.yml" ]; then
    if dbt debug --quiet 2>/dev/null; then
        echo "CONNECTION=OK"
    else
        echo "CONNECTION=FAIL"
    fi
else
    echo "CONNECTION=SKIP"
fi

echo "BOOTSTRAP_DONE"
