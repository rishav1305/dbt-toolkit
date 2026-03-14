"""Build dbt node selection strings from structured input."""

from __future__ import annotations

from typing import List, Optional, Tuple, Union


def build_select_string(
    models: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    paths: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    configs: Optional[List[str]] = None,
    resource_types: Optional[List[str]] = None,
    test_types: Optional[List[str]] = None,
    include_upstream: bool = False,
    include_downstream: bool = False,
    upstream_depth: Optional[int] = None,
    downstream_depth: Optional[int] = None,
    at_operator: bool = False,
    exclude_models: Optional[List[str]] = None,
    return_exclude: bool = False,
) -> Union[str, Tuple[str, str]]:
    """Build a dbt --select string from structured components.

    Components are combined with spaces (union). Tags with commas (intersection).
    Graph operators (+) are applied to model names.

    Args:
        models: Model names to select
        tags: Tag selectors (multiple = intersection via comma)
        paths: Path selectors
        sources: Source selectors (schema.table or schema)
        configs: Config selectors (e.g., "materialized:incremental")
        resource_types: Resource type filters (model, test, source, etc.)
        test_types: Test type filters (unit, generic, singular)
        include_upstream: Add + prefix for upstream dependencies
        include_downstream: Add + suffix for downstream dependencies
        upstream_depth: Limit upstream traversal depth (e.g., 2 = 2+model)
        downstream_depth: Limit downstream traversal depth (e.g., 3 = model+3)
        at_operator: Use @ operator (ancestors + descendants of ancestors)
        exclude_models: Models to exclude (returned separately)
        return_exclude: If True, return (select, exclude) tuple

    Returns:
        Selection string, or (select, exclude) tuple if return_exclude=True
    """
    parts = []

    if models:
        for model in models:
            if at_operator:
                parts.append(f"@{model}")
            else:
                if include_upstream:
                    prefix = f"{upstream_depth}+" if upstream_depth else "+"
                else:
                    prefix = ""
                if include_downstream:
                    suffix = f"+{downstream_depth}" if downstream_depth else "+"
                else:
                    suffix = ""
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

    if sources:
        for source in sources:
            parts.append(f"source:{source}")

    if configs:
        for config in configs:
            parts.append(f"config.{config}")

    if resource_types:
        for rt in resource_types:
            parts.append(f"resource_type:{rt}")

    if test_types:
        for tt in test_types:
            parts.append(f"test_type:{tt}")

    select_str = " ".join(parts)

    if return_exclude and exclude_models:
        exclude_str = " ".join(exclude_models)
        return select_str, exclude_str

    return select_str
