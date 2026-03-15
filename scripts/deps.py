"""Dependency checker for dbt-toolkit."""

import importlib
import subprocess
import sys

from scripts.logger import ToolkitLogger

log = ToolkitLogger("deps")

_PIP_NAMES = {
    "yaml": "PyYAML",
}

CORE_DEPS = ["yaml", "paramiko", "click", "rich"]

OPTIONAL_DEPS = {
    "httpx": "httpx",
    "posthog": "posthog",
}


def _pip_install(package: str) -> bool:
    """Install a package via pip. Returns True on success."""
    log.info("Installing %s...", package)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        log.warning("Timed out installing %s", package)
        return False
    if result.returncode == 0:
        log.info("Installed %s successfully.", package)
        return True
    log.warning("Failed to install %s: %s", package, result.stderr.strip())
    return False


def _is_importable(module_name: str) -> bool:
    """Check if a module can be imported."""
    try:
        importlib.import_module(module_name)
        return True
    except Exception:
        return False


def _pip_name(import_name: str) -> str:
    """Get pip package name for an import name."""
    return _PIP_NAMES.get(import_name, import_name)


def ensure_package(import_name: str) -> bool:
    """Check if a package is available; install it if not."""
    if _is_importable(import_name):
        return True
    pip_pkg = _pip_name(import_name)
    log.info("%s not found.", pip_pkg)
    if _pip_install(pip_pkg):
        importlib.invalidate_caches()
        return _is_importable(import_name)
    return False


def ensure_core() -> list:
    """Ensure all core dependencies are installed. Returns list of failures."""
    failures = []
    for dep in CORE_DEPS:
        if not ensure_package(dep):
            failures.append(_pip_name(dep))
    return failures


def _find_dbt_binary() -> str:
    """Find dbt binary, checking .venv/bin/ first, then system PATH."""
    from pathlib import Path
    import shutil

    venv_dbt = Path(".venv/bin/dbt")
    if venv_dbt.exists():
        return str(venv_dbt.resolve())
    system_dbt = shutil.which("dbt")
    if system_dbt:
        return system_dbt
    return "dbt"


def ensure_dbt_cli() -> bool:
    """Check if dbt CLI is installed and functional."""
    dbt = _find_dbt_binary()
    try:
        result = subprocess.run(
            [dbt, "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    log.warning("dbt CLI not found. Install with: pip install dbt-core dbt-<adapter>")
    return False


def check_all(include_optional: bool = False) -> dict:
    """Run a full dependency check. Returns status dict."""
    status = {"core": {}, "tools": {}, "optional": {}}

    for dep in CORE_DEPS:
        status["core"][_pip_name(dep)] = _is_importable(dep)

    dbt = _find_dbt_binary()
    try:
        dbt_ok = (
            subprocess.run(
                [dbt, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            ).returncode
            == 0
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        dbt_ok = False
    status["tools"]["dbt"] = dbt_ok

    if include_optional:
        for dep in OPTIONAL_DEPS:
            status["optional"][_pip_name(dep)] = _is_importable(dep)

    return status
