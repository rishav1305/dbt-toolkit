"""Execute dbt commands via local, SSH, or Docker."""

from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from scripts.config import ToolkitConfig
from scripts.logger import ToolkitLogger

logger = ToolkitLogger("runner")


@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str
    command: str

    @property
    def success(self) -> bool:
        return self.returncode == 0

    @classmethod
    def from_subprocess(cls, returncode: int, stdout: str, stderr: str, command: str) -> "RunResult":
        return cls(returncode=returncode, stdout=stdout, stderr=stderr, command=command)


class DbtRunner:
    def __init__(self, config: ToolkitConfig):
        self.config = config

    def build_command(
        self,
        dbt_command: str,
        select: Optional[str] = None,
        exclude: Optional[str] = None,
        full_refresh: bool = False,
        threads: Optional[int] = None,
        target: Optional[str] = None,
        extra_args: Optional[List[str]] = None,
    ) -> List[str]:
        dbt_args = ["dbt", dbt_command]
        if select:
            dbt_args.extend(["--select", select])
        if exclude:
            dbt_args.extend(["--exclude", exclude])
        if full_refresh:
            dbt_args.append("--full-refresh")
        if self.config.fail_fast:
            dbt_args.append("--fail-fast")
        effective_threads = threads or self.config.threads
        dbt_args.extend(["--threads", str(effective_threads)])
        effective_target = target or self.config.target
        dbt_args.extend(["--target", effective_target])
        if self.config.profiles_dir:
            dbt_args.extend(["--profiles-dir", self.config.profiles_dir])
        if self.config.log_format:
            dbt_args.extend(["--log-format", self.config.log_format])
        if extra_args:
            dbt_args.extend(extra_args)

        method = self.config.execution_method
        if method == "local":
            return dbt_args
        elif method == "ssh":
            return self._wrap_ssh(dbt_args)
        elif method == "docker":
            return self._wrap_docker(dbt_args)
        else:
            raise ValueError(f"Unknown execution method: {method}")

    def _wrap_ssh(self, dbt_args: List[str]) -> List[str]:
        cfg = self.config
        ssh_cmd = ["ssh"]
        if cfg.ssh_key:
            ssh_cmd.extend(["-i", os.path.expanduser(cfg.ssh_key)])
        ssh_cmd.append(f"{cfg.ssh_user}@{cfg.ssh_host}")
        parts = []
        if cfg.ssh_project_path:
            parts.append(f"cd {shlex.quote(cfg.ssh_project_path)}")
        if cfg.ssh_venv:
            parts.append(f"source {cfg.ssh_venv}")
        for env_var in cfg.ssh_env_vars:
            local_value = os.environ.get(env_var, "")
            parts.append(f"export {env_var}={shlex.quote(local_value)}")
        parts.append(" ".join(dbt_args))
        ssh_cmd.append(" && ".join(parts))
        return ssh_cmd

    def _wrap_docker(self, dbt_args: List[str]) -> List[str]:
        cfg = self.config
        docker_cmd = ["docker", "run", "--rm"]
        for vol in cfg.docker_volumes:
            docker_cmd.extend(["-v", vol])
        docker_cmd.append(cfg.docker_image)
        docker_cmd.extend(dbt_args)
        return docker_cmd

    def execute(self, dbt_command: str, timeout: Optional[int] = None, **kwargs) -> RunResult:
        cmd = self.build_command(dbt_command, **kwargs)
        cmd_str = " ".join(cmd)
        logger.info(f"Executing: {cmd_str}")
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
                cwd=str(self.config.project_root) if self.config.execution_method == "local" else None,
            )
            return RunResult.from_subprocess(proc.returncode, proc.stdout, proc.stderr, cmd_str)
        except subprocess.TimeoutExpired:
            return RunResult.from_subprocess(-1, "", f"Command timed out after {timeout}s", cmd_str)
        except FileNotFoundError as e:
            return RunResult.from_subprocess(-1, "", f"Command not found: {e}", cmd_str)
