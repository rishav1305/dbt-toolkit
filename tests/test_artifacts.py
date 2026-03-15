# tests/test_artifacts.py
import json
from pathlib import Path

from scripts.artifacts import (
    parse_manifest_summary,
    parse_run_results,
    parse_sources_freshness,
    update_summary_cache,
)


def _write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def test_parse_manifest_summary(tmp_path):
    manifest = {
        "metadata": {"dbt_version": "1.8.0", "adapter_type": "redshift"},
        "nodes": {
            "model.proj.model_a": {
                "resource_type": "model",
                "config": {"materialized": "table"},
            },
            "model.proj.model_b": {
                "resource_type": "model",
                "config": {"materialized": "incremental"},
            },
            "test.proj.test_a": {"resource_type": "test"},
        },
        "sources": {
            "source.proj.src.table_a": {"resource_type": "source"},
            "source.proj.src.table_b": {"resource_type": "source"},
        },
    }
    _write_json(tmp_path / "target" / "manifest.json", manifest)
    summary = parse_manifest_summary(tmp_path / "target" / "manifest.json")
    assert summary["dbt_version"] == "1.8.0"
    assert summary["adapter"] == "redshift"
    assert summary["model_count"] == 2
    assert summary["source_count"] == 2
    assert summary["test_count"] == 1
    assert summary["materializations"]["table"] == 1
    assert summary["materializations"]["incremental"] == 1


def test_parse_run_results(tmp_path):
    results = {
        "metadata": {"dbt_version": "1.8.0"},
        "elapsed_time": 45.2,
        "results": [
            {"unique_id": "model.proj.a", "status": "success", "execution_time": 10.1},
            {"unique_id": "model.proj.b", "status": "success", "execution_time": 30.5},
            {
                "unique_id": "model.proj.c",
                "status": "error",
                "execution_time": 4.6,
                "message": "SQL error",
            },
        ],
    }
    _write_json(tmp_path / "target" / "run_results.json", results)
    parsed = parse_run_results(tmp_path / "target" / "run_results.json")
    assert parsed["total"] == 3
    assert parsed["success"] == 2
    assert parsed["error"] == 1
    assert parsed["elapsed_time"] == 45.2
    assert parsed["slowest"]["unique_id"] == "model.proj.b"
    assert len(parsed["failures"]) == 1
    assert parsed["failures"][0]["message"] == "SQL error"


def test_parse_sources_freshness(tmp_path):
    sources = {
        "metadata": {},
        "results": [
            {
                "unique_id": "source.proj.src.table_a",
                "status": "pass",
                "max_loaded_at": "2026-03-14T10:00:00Z",
                "max_loaded_at_time_ago_in_s": 3600,
            },
            {
                "unique_id": "source.proj.src.table_b",
                "status": "warn",
                "max_loaded_at": "2026-03-10T10:00:00Z",
                "max_loaded_at_time_ago_in_s": 345600,
            },
        ],
    }
    _write_json(tmp_path / "target" / "sources.json", sources)
    parsed = parse_sources_freshness(tmp_path / "target" / "sources.json")
    assert parsed["total"] == 2
    assert parsed["pass"] == 1
    assert parsed["warn"] == 1
    assert len(parsed["warnings"]) == 1
    assert "table_b" in parsed["warnings"][0]["unique_id"]


def test_update_summary_cache(tmp_path):
    cache_path = tmp_path / ".dbt-toolkit" / "cache" / "summary.json"
    update_summary_cache(
        cache_path,
        model_count=10,
        source_count=5,
        test_count=20,
        last_run_status="success",
        last_run_time="2026-03-14T12:00:00Z",
    )
    assert cache_path.exists()
    data = json.loads(cache_path.read_text())
    assert data["model_count"] == 10
    assert data["last_run_status"] == "success"
