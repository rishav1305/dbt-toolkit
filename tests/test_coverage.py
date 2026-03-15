# tests/test_coverage.py
import json
from pathlib import Path

from scripts.coverage import compute_test_coverage, compute_doc_coverage


def _write_manifest(tmp_path: Path, nodes: dict, sources: dict = None) -> Path:
    manifest = {
        "nodes": nodes,
        "sources": sources or {},
        "parent_map": {},
        "child_map": {},
    }
    path = tmp_path / "target" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(manifest))
    return path


def test_test_coverage_all_tested(tmp_path):
    nodes = {
        "model.proj.a": {"resource_type": "model", "depends_on": {"nodes": []}},
        "test.proj.test_a": {
            "resource_type": "test",
            "depends_on": {"nodes": ["model.proj.a"]},
            "test_metadata": {"name": "not_null"},
        },
    }
    manifest_path = _write_manifest(tmp_path, nodes)
    cov = compute_test_coverage(manifest_path)
    assert cov["total_models"] == 1
    assert cov["tested_models"] == 1
    assert cov["coverage"] == 1.0


def test_test_coverage_some_untested(tmp_path):
    nodes = {
        "model.proj.a": {"resource_type": "model", "depends_on": {"nodes": []}},
        "model.proj.b": {"resource_type": "model", "depends_on": {"nodes": []}},
        "test.proj.test_a": {
            "resource_type": "test",
            "depends_on": {"nodes": ["model.proj.a"]},
            "test_metadata": {"name": "unique"},
        },
    }
    manifest_path = _write_manifest(tmp_path, nodes)
    cov = compute_test_coverage(manifest_path)
    assert cov["total_models"] == 2
    assert cov["tested_models"] == 1
    assert cov["coverage"] == 0.5
    assert "model.proj.b" in cov["untested_models"]


def test_doc_coverage(tmp_path):
    nodes = {
        "model.proj.a": {
            "resource_type": "model",
            "description": "A documented model",
            "columns": {
                "col1": {"description": "has desc"},
                "col2": {"description": ""},
            },
        },
        "model.proj.b": {
            "resource_type": "model",
            "description": "",
            "columns": {},
        },
    }
    manifest_path = _write_manifest(tmp_path, nodes)
    cov = compute_doc_coverage(manifest_path)
    assert cov["total_models"] == 2
    assert cov["documented_models"] == 1
    assert cov["undocumented_models"] == ["model.proj.b"]
    assert cov["undocumented_columns"]["model.proj.a"] == ["col2"]
