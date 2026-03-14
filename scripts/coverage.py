"""Test and documentation coverage analysis from manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def compute_test_coverage(manifest_path: Path) -> Dict[str, Any]:
    """Compute test coverage: which models have at least one test."""
    data = json.loads(manifest_path.read_text())
    nodes = data.get("nodes", {})

    models = {k for k, v in nodes.items() if v.get("resource_type") == "model"}
    tests = {k: v for k, v in nodes.items() if v.get("resource_type") == "test"}

    tested_models = set()
    for test in tests.values():
        for dep in test.get("depends_on", {}).get("nodes", []):
            if dep in models:
                tested_models.add(dep)

    untested = sorted(models - tested_models)
    total = len(models)
    tested = len(tested_models)

    return {
        "total_models": total,
        "tested_models": tested,
        "coverage": tested / total if total > 0 else 1.0,
        "untested_models": untested,
    }


def compute_doc_coverage(manifest_path: Path) -> Dict[str, Any]:
    """Compute documentation coverage for models and columns."""
    data = json.loads(manifest_path.read_text())
    nodes = data.get("nodes", {})

    models = {k: v for k, v in nodes.items() if v.get("resource_type") == "model"}

    documented = []
    undocumented = []
    undocumented_columns: Dict[str, List[str]] = {}

    for model_id, model in models.items():
        desc = model.get("description", "").strip()
        if desc:
            documented.append(model_id)
        else:
            undocumented.append(model_id)

        cols = model.get("columns", {})
        missing_cols = [
            col_name
            for col_name, col_data in cols.items()
            if not (col_data.get("description") or "").strip()
        ]
        if missing_cols:
            undocumented_columns[model_id] = missing_cols

    return {
        "total_models": len(models),
        "documented_models": len(documented),
        "undocumented_models": sorted(undocumented),
        "undocumented_columns": undocumented_columns,
    }
