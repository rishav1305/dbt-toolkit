"""Tests for manifest state comparison."""

import json
from pathlib import Path

from scripts.state import diff_manifests, find_modified_models


def _write_manifest(path: Path, nodes: dict, sources: dict = None) -> None:
    manifest = {
        "metadata": {"dbt_version": "1.8.0"},
        "nodes": nodes,
        "sources": sources or {},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest))


def test_diff_finds_new_models(tmp_path):
    old_path = tmp_path / "old" / "manifest.json"
    new_path = tmp_path / "new" / "manifest.json"

    _write_manifest(old_path, {
        "model.proj.a": {"resource_type": "model", "checksum": {"checksum": "abc123"}},
    })
    _write_manifest(new_path, {
        "model.proj.a": {"resource_type": "model", "checksum": {"checksum": "abc123"}},
        "model.proj.b": {"resource_type": "model", "checksum": {"checksum": "def456"}},
    })

    diff = diff_manifests(old_path, new_path)
    assert "model.proj.b" in diff["added"]
    assert len(diff["removed"]) == 0
    assert len(diff["modified"]) == 0


def test_diff_finds_removed_models(tmp_path):
    old_path = tmp_path / "old" / "manifest.json"
    new_path = tmp_path / "new" / "manifest.json"

    _write_manifest(old_path, {
        "model.proj.a": {"resource_type": "model", "checksum": {"checksum": "abc123"}},
        "model.proj.b": {"resource_type": "model", "checksum": {"checksum": "def456"}},
    })
    _write_manifest(new_path, {
        "model.proj.a": {"resource_type": "model", "checksum": {"checksum": "abc123"}},
    })

    diff = diff_manifests(old_path, new_path)
    assert "model.proj.b" in diff["removed"]
    assert len(diff["added"]) == 0


def test_diff_finds_modified_models(tmp_path):
    old_path = tmp_path / "old" / "manifest.json"
    new_path = tmp_path / "new" / "manifest.json"

    _write_manifest(old_path, {
        "model.proj.a": {"resource_type": "model", "checksum": {"checksum": "abc123"}},
    })
    _write_manifest(new_path, {
        "model.proj.a": {"resource_type": "model", "checksum": {"checksum": "xyz789"}},
    })

    diff = diff_manifests(old_path, new_path)
    assert "model.proj.a" in diff["modified"]
    assert len(diff["added"]) == 0
    assert len(diff["removed"]) == 0


def test_diff_unchanged(tmp_path):
    old_path = tmp_path / "old" / "manifest.json"
    new_path = tmp_path / "new" / "manifest.json"

    _write_manifest(old_path, {
        "model.proj.a": {"resource_type": "model", "checksum": {"checksum": "abc123"}},
    })
    _write_manifest(new_path, {
        "model.proj.a": {"resource_type": "model", "checksum": {"checksum": "abc123"}},
    })

    diff = diff_manifests(old_path, new_path)
    assert len(diff["added"]) == 0
    assert len(diff["removed"]) == 0
    assert len(diff["modified"]) == 0


def test_find_modified_models(tmp_path):
    old_path = tmp_path / "old" / "manifest.json"
    new_path = tmp_path / "new" / "manifest.json"

    _write_manifest(old_path, {
        "model.proj.a": {"resource_type": "model", "checksum": {"checksum": "abc123"}},
        "model.proj.b": {"resource_type": "model", "checksum": {"checksum": "def456"}},
    })
    _write_manifest(new_path, {
        "model.proj.a": {"resource_type": "model", "checksum": {"checksum": "changed"}},
        "model.proj.b": {"resource_type": "model", "checksum": {"checksum": "def456"}},
        "model.proj.c": {"resource_type": "model", "checksum": {"checksum": "new123"}},
    })

    modified = find_modified_models(old_path, new_path)
    assert "model.proj.a" in modified
    assert "model.proj.c" in modified
    assert "model.proj.b" not in modified


def test_diff_includes_sources(tmp_path):
    old_path = tmp_path / "old" / "manifest.json"
    new_path = tmp_path / "new" / "manifest.json"

    _write_manifest(old_path, {}, sources={
        "source.proj.src.table_a": {"resource_type": "source"},
    })
    _write_manifest(new_path, {}, sources={
        "source.proj.src.table_a": {"resource_type": "source"},
        "source.proj.src.table_b": {"resource_type": "source"},
    })

    diff = diff_manifests(old_path, new_path)
    assert "source.proj.src.table_b" in diff["added"]
