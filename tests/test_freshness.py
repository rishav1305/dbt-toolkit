# tests/test_freshness.py
import json
from pathlib import Path

from scripts.freshness import (
    append_freshness_history,
    get_freshness_trend,
    get_stale_downstream_models,
)


def _write_manifest(tmp_path: Path) -> Path:
    manifest = {
        "nodes": {
            "model.proj.stg_a": {
                "resource_type": "model",
                "depends_on": {"nodes": ["source.proj.src.table_a"]},
                "config": {"materialized": "view"},
            },
        },
        "sources": {
            "source.proj.src.table_a": {"resource_type": "source"},
        },
        "parent_map": {
            "model.proj.stg_a": ["source.proj.src.table_a"],
        },
        "child_map": {
            "source.proj.src.table_a": ["model.proj.stg_a"],
            "model.proj.stg_a": [],
        },
    }
    path = tmp_path / "target" / "manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(manifest))
    return path


def test_append_freshness_history(tmp_path):
    history_path = tmp_path / "freshness_history.json"
    entry = {
        "timestamp": "2026-03-14T12:00:00Z",
        "results": [
            {"unique_id": "source.proj.src.table_a", "status": "pass"},
        ],
    }
    append_freshness_history(history_path, entry)
    data = json.loads(history_path.read_text())
    assert len(data["entries"]) == 1

    # Append another
    entry2 = {
        "timestamp": "2026-03-14T13:00:00Z",
        "results": [
            {"unique_id": "source.proj.src.table_a", "status": "warn"},
        ],
    }
    append_freshness_history(history_path, entry2)
    data = json.loads(history_path.read_text())
    assert len(data["entries"]) == 2


def test_get_freshness_trend(tmp_path):
    history_path = tmp_path / "freshness_history.json"
    entries = {
        "entries": [
            {"timestamp": "2026-03-12T12:00:00Z", "results": [{"unique_id": "source.proj.src.table_a", "status": "pass"}]},
            {"timestamp": "2026-03-13T12:00:00Z", "results": [{"unique_id": "source.proj.src.table_a", "status": "warn"}]},
            {"timestamp": "2026-03-14T12:00:00Z", "results": [{"unique_id": "source.proj.src.table_a", "status": "warn"}]},
        ]
    }
    history_path.write_text(json.dumps(entries))
    trend = get_freshness_trend(history_path, "source.proj.src.table_a")
    assert len(trend) == 3
    assert trend[-1]["status"] == "warn"
    assert trend[0]["status"] == "pass"


def test_get_stale_downstream_models(tmp_path):
    manifest_path = _write_manifest(tmp_path)
    stale_sources = ["source.proj.src.table_a"]
    affected = get_stale_downstream_models(manifest_path, stale_sources)
    assert "model.proj.stg_a" in affected
