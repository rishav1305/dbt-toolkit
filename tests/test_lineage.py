# tests/test_lineage.py
import json
from pathlib import Path

from scripts.lineage import get_ancestors, get_descendants, get_impact_radius


def _write_manifest(tmp_path: Path) -> Path:
    """Write a test manifest with a simple DAG: A -> B -> C, A -> D."""
    manifest = {
        "nodes": {
            "model.proj.a": {
                "resource_type": "model",
                "depends_on": {"nodes": []},
                "config": {"materialized": "table"},
            },
            "model.proj.b": {
                "resource_type": "model",
                "depends_on": {"nodes": ["model.proj.a"]},
                "config": {"materialized": "incremental"},
            },
            "model.proj.c": {
                "resource_type": "model",
                "depends_on": {"nodes": ["model.proj.b"]},
                "config": {"materialized": "view"},
            },
            "model.proj.d": {
                "resource_type": "model",
                "depends_on": {"nodes": ["model.proj.a"]},
                "config": {"materialized": "table"},
            },
        },
        "sources": {},
        "parent_map": {
            "model.proj.a": [],
            "model.proj.b": ["model.proj.a"],
            "model.proj.c": ["model.proj.b"],
            "model.proj.d": ["model.proj.a"],
        },
        "child_map": {
            "model.proj.a": ["model.proj.b", "model.proj.d"],
            "model.proj.b": ["model.proj.c"],
            "model.proj.c": [],
            "model.proj.d": [],
        },
    }
    path = tmp_path / "target" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(manifest))
    return path


def test_get_ancestors(tmp_path):
    manifest_path = _write_manifest(tmp_path)
    ancestors = get_ancestors(manifest_path, "model.proj.c")
    ids = [a["unique_id"] for a in ancestors]
    assert "model.proj.b" in ids
    assert "model.proj.a" in ids
    assert "model.proj.c" not in ids


def test_get_descendants(tmp_path):
    manifest_path = _write_manifest(tmp_path)
    descendants = get_descendants(manifest_path, "model.proj.a")
    ids = [d["unique_id"] for d in descendants]
    assert "model.proj.b" in ids
    assert "model.proj.c" in ids
    assert "model.proj.d" in ids
    assert "model.proj.a" not in ids


def test_get_impact_radius(tmp_path):
    manifest_path = _write_manifest(tmp_path)
    impact = get_impact_radius(manifest_path, "model.proj.b")
    assert "model.proj.a" in impact["ancestors"]
    assert "model.proj.c" in impact["descendants"]
    assert "model.proj.d" not in impact["descendants"]  # sibling, not descendant


def test_ancestors_of_root_is_empty(tmp_path):
    manifest_path = _write_manifest(tmp_path)
    ancestors = get_ancestors(manifest_path, "model.proj.a")
    assert ancestors == []


def test_descendants_of_leaf_is_empty(tmp_path):
    manifest_path = _write_manifest(tmp_path)
    descendants = get_descendants(manifest_path, "model.proj.c")
    assert descendants == []
