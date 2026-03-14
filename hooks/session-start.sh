#!/usr/bin/env bash
# Session-start hook for dbt-toolkit.
# Detects dbt projects and outputs context for the Claude session.

set -euo pipefail

# Walk up from CWD looking for dbt_project.yml
find_dbt_project() {
    local dir="$PWD"
    while [ "$dir" != "/" ]; do
        if [ -f "$dir/dbt_project.yml" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

PROJECT_ROOT=$(find_dbt_project) || exit 0
echo "DBT_PROJECT_FOUND"

# Parse project name from dbt_project.yml (lightweight, no Python)
PROJECT_NAME=$(grep -m1 "^name:" "$PROJECT_ROOT/dbt_project.yml" | sed "s/name:[[:space:]]*//" | tr -d "'\"" || echo "unknown")
PROFILE_NAME=$(grep -m1 "^profile:" "$PROJECT_ROOT/dbt_project.yml" | sed "s/profile:[[:space:]]*//" | tr -d "'\"" || echo "unknown")

CONFIG_FILE="$PROJECT_ROOT/.dbt-toolkit/config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "[dbt-toolkit] dbt project detected: $PROJECT_NAME (profile: $PROFILE_NAME)"
    echo "  Run /dbt-toolkit:dbt setup to configure."
    exit 0
fi
echo "DBT_TOOLKIT_CONFIGURED"

# Parse execution method from config
EXEC_METHOD=$(grep -m1 "method:" "$CONFIG_FILE" | sed "s/.*method:[[:space:]]*//" | tr -d "'\"" || echo "local")
TARGET=$(grep -m1 "target:" "$CONFIG_FILE" | sed "s/.*target:[[:space:]]*//" | tr -d "'\"" || echo "dev")

# Read cached summary if available
SUMMARY_FILE="$PROJECT_ROOT/.dbt-toolkit/cache/summary.json"
SUMMARY_LINE=""
if [ -f "$SUMMARY_FILE" ]; then
    MODEL_COUNT=$(python3 -c "import json; d=json.load(open('$SUMMARY_FILE')); print(d.get('model_count','?'))" 2>/dev/null || echo "?")
    SOURCE_COUNT=$(python3 -c "import json; d=json.load(open('$SUMMARY_FILE')); print(d.get('source_count','?'))" 2>/dev/null || echo "?")
    TEST_COUNT=$(python3 -c "import json; d=json.load(open('$SUMMARY_FILE')); print(d.get('test_count','?'))" 2>/dev/null || echo "?")
    LAST_STATUS=$(python3 -c "import json; d=json.load(open('$SUMMARY_FILE')); print(d.get('last_run_status','unknown'))" 2>/dev/null || echo "unknown")
    SUMMARY_LINE="  Models: $MODEL_COUNT models, $SOURCE_COUNT sources, $TEST_COUNT tests | Last run: $LAST_STATUS"
fi

echo "[dbt-toolkit] dbt project detected."
echo "  Project: $PROJECT_NAME (profile: $PROFILE_NAME → $TARGET)"
echo "  Execution: $EXEC_METHOD"
if [ -n "$SUMMARY_LINE" ]; then
    echo "$SUMMARY_LINE"
fi
echo "  Available: /dbt-toolkit:dbt [run|test|freshness|audit|debug|docs|help]"
echo "DBT_TOOLKIT_READY"
