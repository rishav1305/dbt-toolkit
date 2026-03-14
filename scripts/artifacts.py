"""Parse dbt artifacts: manifest, run_results, catalog, sources."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_manifest_summary(manifest_path: Path) -> Dict[str, Any]:
    """Extract summary stats from manifest.json."""
    data = json.loads(manifest_path.read_text())
    metadata = data.get("metadata", {})
    nodes = data.get("nodes", {})
    sources = data.get("sources", {})

    models = {k: v for k, v in nodes.items() if v.get("resource_type") == "model"}
    tests = {k: v for k, v in nodes.items() if v.get("resource_type") == "test"}

    materializations = Counter(
        v.get("config", {}).get("materialized", "unknown") for v in models.values()
    )

    return {
        "dbt_version": metadata.get("dbt_version"),
        "adapter": metadata.get("adapter_type"),
        "model_count": len(models),
        "source_count": len(sources),
        "test_count": len(tests),
        "materializations": dict(materializations),
    }


def parse_run_results(results_path: Path) -> Dict[str, Any]:
    """Extract summary from run_results.json."""
    data = json.loads(results_path.read_text())
    results = data.get("results", [])

    status_counts = Counter(r.get("status") for r in results)
    failures = [
        {
            "unique_id": r["unique_id"],
            "status": r["status"],
            "message": r.get("message", ""),
            "execution_time": r.get("execution_time", 0),
        }
        for r in results
        if r.get("status") in ("error", "fail")
    ]

    slowest = max(results, key=lambda r: r.get("execution_time", 0)) if results else None

    return {
        "total": len(results),
        "success": status_counts.get("success", 0),
        "error": status_counts.get("error", 0),
        "fail": status_counts.get("fail", 0),
        "skip": status_counts.get("skipped", 0),
        "elapsed_time": data.get("elapsed_time", 0),
        "slowest": {
            "unique_id": slowest["unique_id"],
            "execution_time": slowest.get("execution_time", 0),
        }
        if slowest
        else None,
        "failures": failures,
    }


def parse_sources_freshness(sources_path: Path) -> Dict[str, Any]:
    """Extract summary from sources.json."""
    data = json.loads(sources_path.read_text())
    results = data.get("results", [])

    status_counts = Counter(r.get("status") for r in results)
    warnings = [
        {
            "unique_id": r["unique_id"],
            "status": r["status"],
            "max_loaded_at": r.get("max_loaded_at"),
            "time_ago_seconds": r.get("max_loaded_at_time_ago_in_s"),
        }
        for r in results
        if r.get("status") in ("warn", "error", "runtime error")
    ]

    return {
        "total": len(results),
        "pass": status_counts.get("pass", 0),
        "warn": status_counts.get("warn", 0),
        "error": status_counts.get("error", 0),
        "runtime_error": status_counts.get("runtime error", 0),
        "warnings": warnings,
    }


def update_summary_cache(
    cache_path: Path,
    model_count: Optional[int] = None,
    source_count: Optional[int] = None,
    test_count: Optional[int] = None,
    last_run_status: Optional[str] = None,
    last_run_time: Optional[str] = None,
    freshness_warnings: Optional[List[Dict]] = None,
) -> None:
    """Update the cached summary.json for session hook."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    existing = {}
    if cache_path.exists():
        existing = json.loads(cache_path.read_text())

    if model_count is not None:
        existing["model_count"] = model_count
    if source_count is not None:
        existing["source_count"] = source_count
    if test_count is not None:
        existing["test_count"] = test_count
    if last_run_status is not None:
        existing["last_run_status"] = last_run_status
    if last_run_time is not None:
        existing["last_run_time"] = last_run_time
    if freshness_warnings is not None:
        existing["freshness_warnings"] = freshness_warnings

    existing["updated_at"] = datetime.now(timezone.utc).isoformat()

    cache_path.write_text(json.dumps(existing, indent=2) + "\n")
