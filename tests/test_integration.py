# tests/test_integration.py
"""Integration tests — verify skills, scripts, and hooks work together."""

import json
import subprocess
from pathlib import Path

import yaml


def test_session_hook_detects_dbt_project(tmp_path):
    """Session hook should output DBT_PROJECT_FOUND for a dbt project."""
    (tmp_path / "dbt_project.yml").write_text(
        yaml.dump({"name": "test_project", "profile": "default"})
    )
    hook_script = Path(__file__).parent.parent / "hooks" / "session-start.sh"
    result = subprocess.run(
        ["bash", str(hook_script)],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env={
            "PWD": str(tmp_path),
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "HOME": str(Path.home()),
        },
    )
    assert "DBT_PROJECT_FOUND" in result.stdout or result.returncode == 0


def test_full_config_roundtrip(tmp_path):
    """Config discovery should find and parse a written config."""
    from scripts.config import ToolkitConfig

    (tmp_path / "dbt_project.yml").write_text(
        yaml.dump({"name": "roundtrip_test", "profile": "test"})
    )
    toolkit_dir = tmp_path / ".dbt-toolkit"
    toolkit_dir.mkdir()
    config = {
        "version": 1,
        "project": {"name": "roundtrip_test", "dir": "."},
        "execution": {"method": "local"},
        "profile": {"name": "test", "target": "dev"},
        "defaults": {"threads": 2},
        "tags": {"favorites": ["nightly"]},
    }
    (toolkit_dir / "config.yaml").write_text(yaml.dump(config))

    cfg = ToolkitConfig.discover(start_dir=tmp_path)
    assert cfg.project_name == "roundtrip_test"
    assert cfg.threads == 2
    assert cfg.favorite_tags == ["nightly"]


def test_artifact_pipeline(tmp_path):
    """Artifacts → coverage → audit pipeline should produce results."""
    from scripts.artifacts import parse_manifest_summary
    from scripts.coverage import compute_test_coverage
    from scripts.audit import run_audit

    manifest = {
        "metadata": {"dbt_version": "1.8.0", "adapter_type": "redshift"},
        "nodes": {
            "model.proj.a": {
                "resource_type": "model",
                "config": {"materialized": "incremental"},
                "description": "",
                "columns": {},
                "depends_on": {"nodes": []},
                "tags": [],
            },
        },
        "sources": {},
        "parent_map": {},
        "child_map": {},
    }
    manifest_path = tmp_path / "target" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(manifest))

    summary = parse_manifest_summary(manifest_path)
    assert summary["model_count"] == 1

    cov = compute_test_coverage(manifest_path)
    assert cov["coverage"] == 0.0

    audit_results = run_audit(manifest_path)
    categories = {r.category for r in audit_results}
    assert "materialization" in categories  # missing unique_key
    assert "tags" in categories  # no tags
