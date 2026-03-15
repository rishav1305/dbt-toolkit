"""Manifest state comparison for CI/CD slim runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set


def _load_manifest(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def _get_all_resources(manifest: Dict) -> Dict[str, Dict]:
    """Merge nodes and sources into a single dict."""
    resources = {}
    resources.update(manifest.get("nodes", {}))
    resources.update(manifest.get("sources", {}))
    return resources


def _get_checksum(resource: Dict) -> str:
    """Extract checksum from a resource, or empty string if missing."""
    return resource.get("checksum", {}).get("checksum", "")


def diff_manifests(
    old_path: Path,
    new_path: Path,
    resource_types: List[str] | None = None,
) -> Dict[str, List[str]]:
    """Compare two manifests and return added, removed, modified resources.

    Args:
        old_path: Path to the baseline manifest.json
        new_path: Path to the current manifest.json
        resource_types: Optional filter (e.g., ["model", "source"])

    Returns:
        Dict with keys: added, removed, modified (lists of unique_ids)
    """
    old_manifest = _load_manifest(old_path)
    new_manifest = _load_manifest(new_path)

    old_resources = _get_all_resources(old_manifest)
    new_resources = _get_all_resources(new_manifest)

    if resource_types:
        old_resources = {
            k: v
            for k, v in old_resources.items()
            if v.get("resource_type") in resource_types
        }
        new_resources = {
            k: v
            for k, v in new_resources.items()
            if v.get("resource_type") in resource_types
        }

    old_ids: Set[str] = set(old_resources.keys())
    new_ids: Set[str] = set(new_resources.keys())

    added = sorted(new_ids - old_ids)
    removed = sorted(old_ids - new_ids)

    modified = []
    for uid in sorted(old_ids & new_ids):
        old_checksum = _get_checksum(old_resources[uid])
        new_checksum = _get_checksum(new_resources[uid])
        if old_checksum and new_checksum and old_checksum != new_checksum:
            modified.append(uid)

    return {
        "added": added,
        "removed": removed,
        "modified": modified,
    }


def find_modified_models(
    old_path: Path,
    new_path: Path,
) -> List[str]:
    """Return unique_ids of models that are new or modified (for slim CI runs).

    This is the equivalent of dbt's `state:modified` + `state:new` selectors.
    """
    diff = diff_manifests(old_path, new_path)
    return sorted(set(diff["added"] + diff["modified"]))
