# tests/test_audit.py
import json
from pathlib import Path

from scripts.audit import run_audit, AuditResult


def _write_manifest(tmp_path: Path, nodes: dict, sources: dict = None) -> Path:
    manifest = {
        "metadata": {"adapter_type": "redshift"},
        "nodes": nodes,
        "sources": sources or {},
        "parent_map": {},
        "child_map": {},
    }
    path = tmp_path / "target" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(manifest))
    return path


def test_audit_flags_missing_unique_key(tmp_path):
    nodes = {
        "model.proj.incremental_no_key": {
            "resource_type": "model",
            "config": {"materialized": "incremental"},
            "description": "test",
            "columns": {},
            "depends_on": {"nodes": []},
            "tags": ["daily"],
        },
    }
    manifest_path = _write_manifest(tmp_path, nodes)
    results = run_audit(manifest_path, check_sort_dist=False)
    warnings = [r for r in results if r.severity == "warning"]
    assert any("unique_key" in r.message for r in warnings)


def test_audit_flags_missing_sort_dist(tmp_path):
    nodes = {
        "model.proj.table_no_sort": {
            "resource_type": "model",
            "config": {"materialized": "table"},
            "description": "test",
            "columns": {},
            "depends_on": {"nodes": []},
            "tags": [],
        },
    }
    manifest_path = _write_manifest(tmp_path, nodes)
    results = run_audit(manifest_path, check_sort_dist=True)
    infos = [r for r in results if r.severity == "info"]
    assert any("sort" in r.message.lower() or "dist" in r.message.lower() for r in infos)


def test_audit_flags_untagged_models(tmp_path):
    nodes = {
        "model.proj.no_tags": {
            "resource_type": "model",
            "config": {"materialized": "view"},
            "description": "",
            "columns": {},
            "depends_on": {"nodes": []},
            "tags": [],
        },
    }
    manifest_path = _write_manifest(tmp_path, nodes)
    results = run_audit(manifest_path, check_sort_dist=False)
    infos = [r for r in results if r.severity == "info"]
    assert any("tag" in r.message.lower() for r in infos)
