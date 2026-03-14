"""Source freshness tracking with history and downstream impact."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from scripts.lineage import get_descendants


def append_freshness_history(history_path: Path, entry: Dict[str, Any]) -> None:
    """Append a freshness check result to history."""
    history_path.parent.mkdir(parents=True, exist_ok=True)

    existing = {"entries": []}
    if history_path.exists():
        existing = json.loads(history_path.read_text())

    existing["entries"].append(entry)
    history_path.write_text(json.dumps(existing, indent=2) + "\n")


def get_freshness_trend(
    history_path: Path, source_unique_id: str, limit: int = 10
) -> List[Dict[str, Any]]:
    """Get the last N freshness statuses for a source."""
    if not history_path.exists():
        return []

    data = json.loads(history_path.read_text())
    trend = []

    for entry in data.get("entries", []):
        for result in entry.get("results", []):
            if result.get("unique_id") == source_unique_id:
                trend.append(
                    {
                        "timestamp": entry["timestamp"],
                        "status": result["status"],
                    }
                )

    return trend[-limit:]


def get_stale_downstream_models(
    manifest_path: Path, stale_source_ids: List[str]
) -> List[str]:
    """Get all models downstream of stale sources."""
    affected = set()
    for source_id in stale_source_ids:
        descendants = get_descendants(manifest_path, source_id)
        for d in descendants:
            if d.get("resource_type") == "model":
                affected.add(d["unique_id"])
    return sorted(affected)
