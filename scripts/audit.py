"""Proactive health checks for dbt projects."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from scripts.coverage import compute_test_coverage, compute_doc_coverage


@dataclass
class AuditResult:
    """Single audit finding."""

    severity: str  # "error", "warning", "info"
    category: str  # "test_coverage", "materialization", "redshift", "tags", "docs"
    message: str
    model_id: Optional[str] = None


def run_audit(
    manifest_path: Path,
    check_sort_dist: bool = True,
    min_test_coverage: float = 0.8,
) -> List[AuditResult]:
    """Run all audit checks and return findings."""
    data = json.loads(manifest_path.read_text())
    adapter = data.get("metadata", {}).get("adapter_type", "unknown")
    nodes = data.get("nodes", {})
    models = {k: v for k, v in nodes.items() if v.get("resource_type") == "model"}

    results: List[AuditResult] = []

    # 1. Test coverage
    test_cov = compute_test_coverage(manifest_path)
    if test_cov["coverage"] < min_test_coverage:
        results.append(
            AuditResult(
                severity="warning",
                category="test_coverage",
                message=f"Test coverage {test_cov['coverage']:.0%} is below threshold {min_test_coverage:.0%}. "
                f"Untested: {', '.join(test_cov['untested_models'][:5])}",
            )
        )

    # 2. Doc coverage
    doc_cov = compute_doc_coverage(manifest_path)
    for model_id in doc_cov["undocumented_models"]:
        results.append(
            AuditResult(
                severity="info",
                category="docs",
                message="Model has no description",
                model_id=model_id,
            )
        )

    # 3. Materialization checks
    for model_id, model in models.items():
        config = model.get("config", {})
        materialized = config.get("materialized", "unknown")

        # Incremental without unique_key
        if materialized == "incremental" and not config.get("unique_key"):
            results.append(
                AuditResult(
                    severity="warning",
                    category="materialization",
                    message="Incremental model missing unique_key — risk of duplicates",
                    model_id=model_id,
                )
            )

        # 4. Redshift sort/dist (only if adapter is redshift)
        if check_sort_dist and adapter == "redshift":
            if materialized in ("table", "incremental"):
                if not config.get("sort"):
                    results.append(
                        AuditResult(
                            severity="info",
                            category="redshift",
                            message="No sort key configured",
                            model_id=model_id,
                        )
                    )
                if not config.get("dist"):
                    results.append(
                        AuditResult(
                            severity="info",
                            category="redshift",
                            message="No dist key configured",
                            model_id=model_id,
                        )
                    )

        # 5. Tag hygiene
        tags = model.get("tags", [])
        if not tags:
            results.append(
                AuditResult(
                    severity="info",
                    category="tags",
                    message="Model has no tags",
                    model_id=model_id,
                )
            )

    return results
