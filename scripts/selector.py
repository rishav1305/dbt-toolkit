"""Build dbt node selection strings from structured input."""

from __future__ import annotations

from typing import List, Optional


def build_select_string(
    models: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    paths: Optional[List[str]] = None,
    include_upstream: bool = False,
    include_downstream: bool = False,
) -> str:
    """Build a dbt --select string from structured components.

    Components are combined with spaces (union). Tags with commas (intersection).
    Graph operators (+) are applied to model names.
    """
    parts = []

    if models:
        for model in models:
            prefix = "+" if include_upstream else ""
            suffix = "+" if include_downstream else ""
            parts.append(f"{prefix}{model}{suffix}")

    if tags:
        if len(tags) == 1:
            parts.append(f"tag:{tags[0]}")
        else:
            # Multiple tags = intersection (comma-separated)
            parts.append(",".join(f"tag:{t}" for t in tags))

    if paths:
        for path in paths:
            parts.append(f"path:{path}")

    return " ".join(parts)
