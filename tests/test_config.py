# tests/test_config.py
from pathlib import Path

import yaml

from scripts.config import ToolkitConfig


def _write_config(tmpdir: Path, config: dict) -> Path:
    """Helper: write a dbt_project.yml and .dbt-toolkit/config.yaml."""
    (tmpdir / "dbt_project.yml").write_text(
        yaml.dump({"name": "test_project", "profile": "test_profile"})
    )
    toolkit_dir = tmpdir / ".dbt-toolkit"
    toolkit_dir.mkdir(exist_ok=True)
    config_path = toolkit_dir / "config.yaml"
    config_path.write_text(yaml.dump(config))
    return config_path


def test_discover_finds_config_in_cwd(tmp_path):
    config_data = {
        "version": 1,
        "project": {"name": "my_project", "dir": "."},
        "execution": {"method": "local"},
        "profile": {"name": "default", "target": "dev"},
        "defaults": {"threads": 4},
    }
    _write_config(tmp_path, config_data)
    cfg = ToolkitConfig.discover(start_dir=tmp_path)
    assert cfg is not None
    assert cfg.project_name == "my_project"
    assert cfg.execution_method == "local"
    assert cfg.profile_name == "default"
    assert cfg.target == "dev"
    assert cfg.threads == 4


def test_discover_walks_up(tmp_path):
    config_data = {
        "version": 1,
        "project": {"name": "parent_project", "dir": "."},
        "execution": {
            "method": "ssh",
            "ssh": {"host": "example.com", "user": "ubuntu"},
        },
        "profile": {"name": "prod", "target": "redshift"},
        "defaults": {"threads": 8},
    }
    _write_config(tmp_path, config_data)
    child = tmp_path / "models" / "staging"
    child.mkdir(parents=True)
    cfg = ToolkitConfig.discover(start_dir=child)
    assert cfg is not None
    assert cfg.project_name == "parent_project"
    assert cfg.execution_method == "ssh"
    assert cfg.ssh_host == "example.com"


def test_discover_returns_none_when_missing(tmp_path):
    cfg = ToolkitConfig.discover(start_dir=tmp_path)
    assert cfg is None


def test_dbt_project_yml_required(tmp_path):
    toolkit_dir = tmp_path / ".dbt-toolkit"
    toolkit_dir.mkdir()
    (toolkit_dir / "config.yaml").write_text(yaml.dump({"version": 1}))
    cfg = ToolkitConfig.discover(start_dir=tmp_path)
    assert cfg is None


def test_defaults_applied(tmp_path):
    config_data = {
        "version": 1,
        "project": {"name": "minimal"},
        "execution": {"method": "local"},
        "profile": {"name": "default", "target": "dev"},
    }
    _write_config(tmp_path, config_data)
    cfg = ToolkitConfig.discover(start_dir=tmp_path)
    assert cfg.threads == 4
    assert cfg.full_refresh is False
    assert cfg.fail_fast is False
    assert cfg.log_format == "json"


def test_ssh_config_fields(tmp_path):
    config_data = {
        "version": 1,
        "project": {"name": "ssh_project", "dir": "."},
        "execution": {
            "method": "ssh",
            "ssh": {
                "host": "10.0.0.1",
                "user": "deploy",
                "key": "~/.ssh/id_rsa",
                "project_path": "/opt/dbt",
                "venv": "venv/bin/activate",
                "env_vars": ["DBT_USER", "DBT_PASS"],
            },
        },
        "profile": {"name": "prod", "target": "redshift"},
        "defaults": {"threads": 8},
    }
    _write_config(tmp_path, config_data)
    cfg = ToolkitConfig.discover(start_dir=tmp_path)
    assert cfg.ssh_host == "10.0.0.1"
    assert cfg.ssh_user == "deploy"
    assert cfg.ssh_key == "~/.ssh/id_rsa"
    assert cfg.ssh_project_path == "/opt/dbt"
    assert cfg.ssh_venv == "venv/bin/activate"
    assert cfg.ssh_env_vars == ["DBT_USER", "DBT_PASS"]


def test_favorite_tags(tmp_path):
    config_data = {
        "version": 1,
        "project": {"name": "tagged"},
        "execution": {"method": "local"},
        "profile": {"name": "default", "target": "dev"},
        "tags": {"favorites": ["daily", "wcbm_dashboard"]},
    }
    _write_config(tmp_path, config_data)
    cfg = ToolkitConfig.discover(start_dir=tmp_path)
    assert cfg.favorite_tags == ["daily", "wcbm_dashboard"]
