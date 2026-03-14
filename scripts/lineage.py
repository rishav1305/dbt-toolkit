"""DAG traversal from manifest.json — ancestors, descendants, impact radius."""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any, Dict, List


def _load_manifest(manifest_path: Path) -> Dict[str, Any]:
    return json.loads(manifest_path.read_text())


def _node_info(manifest: Dict, unique_id: str) -> Dict[str, Any]:
    """Extract node metadata."""
    node = manifest.get("nodes", {}).get(unique_id) or manifest.get("sources", {}).get(unique_id)
    if not node:
        return {"unique_id": unique_id}
    return {
        "unique_id": unique_id,
        "resource_type": node.get("resource_type"),
        "materialized": node.get("config", {}).get("materialized"),
    }


def get_ancestors(manifest_path: Path, unique_id: str) -> List[Dict[str, Any]]:
    """Get all upstream nodes (transitive parents)."""
    manifest = _load_manifest(manifest_path)
    parent_map = manifest.get("parent_map", {})

    visited = set()
    queue = deque(parent_map.get(unique_id, []))
    result = []

    while queue:
        node_id = queue.popleft()
        if node_id in visited:
            continue
        visited.add(node_id)
        result.append(_node_info(manifest, node_id))
        queue.extend(parent_map.get(node_id, []))

    return result


def get_descendants(manifest_path: Path, unique_id: str) -> List[Dict[str, Any]]:
    """Get all downstream nodes (transitive children)."""
    manifest = _load_manifest(manifest_path)
    child_map = manifest.get("child_map", {})

    visited = set()
    queue = deque(child_map.get(unique_id, []))
    result = []

    while queue:
        node_id = queue.popleft()
        if node_id in visited:
            continue
        visited.add(node_id)
        result.append(_node_info(manifest, node_id))
        queue.extend(child_map.get(node_id, []))

    return result


def get_impact_radius(manifest_path: Path, unique_id: str) -> Dict[str, List[str]]:
    """Get both ancestors and descendants as ID lists."""
    ancestors = get_ancestors(manifest_path, unique_id)
    descendants = get_descendants(manifest_path, unique_id)
    return {
        "ancestors": [a["unique_id"] for a in ancestors],
        "descendants": [d["unique_id"] for d in descendants],
    }
