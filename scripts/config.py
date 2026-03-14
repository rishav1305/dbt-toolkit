"""Config discovery and typed access for dbt-toolkit."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


_DEFAULTS = {
    "threads": 4,
    "full_refresh": False,
    "fail_fast": False,
    "log_format": "json",
}


@dataclass
class ToolkitConfig:
    """Typed access to .dbt-toolkit/config.yaml."""

    project_root: Path
    config_path: Path
    project_name: str
    project_dir: str = "."
    execution_method: str = "local"
    ssh_host: Optional[str] = None
    ssh_user: Optional[str] = None
    ssh_key: Optional[str] = None
    ssh_project_path: Optional[str] = None
    ssh_venv: Optional[str] = None
    ssh_env_vars: List[str] = field(default_factory=list)
    docker_image: Optional[str] = None
    docker_volumes: List[str] = field(default_factory=list)
    profile_name: str = "default"
    target: str = "dev"
    profiles_dir: Optional[str] = None
    threads: int = 4
    full_refresh: bool = False
    fail_fast: bool = False
    log_format: str = "json"
    freshness_enabled: bool = True
    freshness_warn_after_hours: int = 24
    freshness_tracked_sources: List[str] = field(default_factory=list)
    audit_check_sort_dist: bool = True
    audit_check_undocumented: bool = True
    audit_check_test_coverage: bool = True
    audit_min_test_coverage: float = 0.8
    favorite_tags: List[str] = field(default_factory=list)
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def discover(cls, start_dir: Optional[Path] = None) -> Optional["ToolkitConfig"]:
        current = Path(start_dir) if start_dir else Path.cwd()
        current = current.resolve()
        while True:
            dbt_project = current / "dbt_project.yml"
            config_file = current / ".dbt-toolkit" / "config.yaml"
            if dbt_project.exists() and config_file.exists():
                return cls._from_file(config_file, project_root=current)
            parent = current.parent
            if parent == current:
                return None
            current = parent

    @classmethod
    def _from_file(cls, config_path: Path, project_root: Path) -> "ToolkitConfig":
        raw = yaml.safe_load(config_path.read_text()) or {}
        project = raw.get("project", {})
        execution = raw.get("execution", {})
        ssh = execution.get("ssh", {})
        docker = execution.get("docker", {})
        profile = raw.get("profile", {})
        defaults = raw.get("defaults", {})
        freshness = raw.get("freshness", {})
        audit = raw.get("audit", {})
        tags = raw.get("tags", {})
        return cls(
            project_root=project_root,
            config_path=config_path,
            project_name=project.get("name", "unknown"),
            project_dir=project.get("dir", "."),
            execution_method=execution.get("method", "local"),
            ssh_host=ssh.get("host"),
            ssh_user=ssh.get("user"),
            ssh_key=ssh.get("key"),
            ssh_project_path=ssh.get("project_path"),
            ssh_venv=ssh.get("venv"),
            ssh_env_vars=ssh.get("env_vars", []),
            docker_image=docker.get("image"),
            docker_volumes=docker.get("volumes", []),
            profile_name=profile.get("name", "default"),
            target=profile.get("target", "dev"),
            profiles_dir=profile.get("profiles_dir"),
            threads=defaults.get("threads", _DEFAULTS["threads"]),
            full_refresh=defaults.get("full_refresh", _DEFAULTS["full_refresh"]),
            fail_fast=defaults.get("fail_fast", _DEFAULTS["fail_fast"]),
            log_format=defaults.get("log_format", _DEFAULTS["log_format"]),
            freshness_enabled=freshness.get("enabled", True),
            freshness_warn_after_hours=freshness.get("warn_after_hours", 24),
            freshness_tracked_sources=freshness.get("tracked_sources", []),
            audit_check_sort_dist=audit.get("check_sort_dist", True),
            audit_check_undocumented=audit.get("check_undocumented", True),
            audit_check_test_coverage=audit.get("check_test_coverage", True),
            audit_min_test_coverage=audit.get("min_test_coverage", 0.8),
            favorite_tags=tags.get("favorites", []),
            _raw=raw,
        )

    @property
    def cache_dir(self) -> Path:
        return self.config_path.parent / "cache"

    @property
    def secrets_dir(self) -> Path:
        return self.config_path.parent / ".secrets"

    @property
    def summary_path(self) -> Path:
        return self.cache_dir / "summary.json"

    @property
    def freshness_history_path(self) -> Path:
        return self.config_path.parent / "freshness_history.json"
