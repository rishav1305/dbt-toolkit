# tests/test_runner.py
from pathlib import Path
from unittest.mock import MagicMock

from scripts.runner import DbtRunner, RunResult


def _mock_config(method="local", **kwargs):
    cfg = MagicMock()
    cfg.execution_method = method
    cfg.project_root = Path("/tmp/test_project")
    cfg.project_dir = "."
    cfg.profile_name = "default"
    cfg.target = "dev"
    cfg.threads = 4
    cfg.fail_fast = False
    cfg.log_format = "json"
    cfg.profiles_dir = None
    cfg.ssh_host = kwargs.get("ssh_host")
    cfg.ssh_user = kwargs.get("ssh_user")
    cfg.ssh_key = kwargs.get("ssh_key")
    cfg.ssh_project_path = kwargs.get("ssh_project_path")
    cfg.ssh_venv = kwargs.get("ssh_venv")
    cfg.ssh_env_vars = kwargs.get("ssh_env_vars", [])
    cfg.docker_image = kwargs.get("docker_image")
    cfg.docker_volumes = kwargs.get("docker_volumes", [])
    return cfg


def test_build_local_command():
    runner = DbtRunner(_mock_config())
    cmd = runner.build_command("run", select="tag:daily", full_refresh=True)
    assert cmd[0] == "dbt"
    assert "run" in cmd
    assert "--select" in cmd
    assert "tag:daily" in cmd
    assert "--full-refresh" in cmd


def test_build_local_command_with_threads():
    runner = DbtRunner(_mock_config())
    cmd = runner.build_command("test", select="model_name", threads=8)
    assert "--threads" in cmd
    assert "8" in cmd


def test_build_ssh_command():
    cfg = _mock_config(
        method="ssh",
        ssh_host="10.0.0.1",
        ssh_user="ubuntu",
        ssh_key="~/.ssh/key.pem",
        ssh_project_path="/opt/dbt/project",
        ssh_venv="dbt-env/bin/activate",
        ssh_env_vars=["DBT_USER", "DBT_PASS"],
    )
    runner = DbtRunner(cfg)
    cmd = runner.build_command("run", select="tag:daily")
    assert cmd[0] == "ssh"
    assert "10.0.0.1" in " ".join(cmd)
    assert "dbt run" in " ".join(cmd)
    assert "source dbt-env/bin/activate" in " ".join(cmd)


def test_build_docker_command():
    cfg = _mock_config(
        method="docker",
        docker_image="ghcr.io/dbt-labs/dbt-redshift:latest",
        docker_volumes=["/data:/data"],
    )
    runner = DbtRunner(cfg)
    cmd = runner.build_command("run", select="model_a")
    assert cmd[0] == "docker"
    assert "run" in cmd
    assert "ghcr.io/dbt-labs/dbt-redshift:latest" in cmd


def test_parse_run_result_success():
    result = RunResult.from_subprocess(
        returncode=0,
        stdout="Running with dbt=1.8.0\nCompleted successfully\n",
        stderr="",
        command="dbt run --select model_a",
    )
    assert result.success is True
    assert result.returncode == 0


def test_parse_run_result_failure():
    result = RunResult.from_subprocess(
        returncode=1,
        stdout="",
        stderr="Compilation Error in model\n",
        command="dbt run --select model_a",
    )
    assert result.success is False
    assert "Compilation Error" in result.stderr


def test_fail_fast_flag():
    cfg = _mock_config()
    cfg.fail_fast = True
    runner = DbtRunner(cfg)
    cmd = runner.build_command("run")
    assert "--fail-fast" in cmd
