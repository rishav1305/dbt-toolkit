# Plugin Marketplace Restructure Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure dbt-toolkit to match preset-toolkit's plugin structure for Claude Code marketplace publication.

**Architecture:** Remove root plugin.json, add marketplace.json, add 3 new Python modules (telemetry, deps, http), add CI/CD scaffolding, rewrite README and LICENSE, add test fixtures.

**Tech Stack:** Python 3.9+, PyYAML, httpx, posthog, pytest, ruff, GitHub Actions

**Spec:** `docs/superpowers/specs/2026-03-15-plugin-marketplace-restructure-design.md`

---

## Chunk 1: Plugin Packaging & Project Config

### Task 1: Remove root plugin.json and add marketplace.json

**Files:**
- Remove: `plugin.json` (root)
- Create: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Remove root plugin.json**

```bash
git rm plugin.json
```

- [ ] **Step 2: Create marketplace.json**

Create `.claude-plugin/marketplace.json`:

```json
{
  "name": "dbt-toolkit",
  "owner": {
    "name": "Rishav Chatterjee",
    "email": "rishav.chatterjee@weather.com"
  },
  "plugins": [
    {
      "name": "dbt-toolkit",
      "source": "./",
      "description": "Workflow-oriented dbt project management for Claude Code",
      "version": "0.1.0"
    }
  ]
}
```

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat: remove root plugin.json, add marketplace.json"
```

### Task 2: Update pyproject.toml

**Files:**
- Modify: `pyproject.toml:29-30` (replace setuptools section), `:16-21` (add deps), `:23-27` (add dev deps)

- [ ] **Step 1: Replace [tool.setuptools] section**

Replace lines 29-30:
```toml
[tool.setuptools]
py-modules = ["scripts"]
```

With:
```toml
[tool.setuptools.packages.find]
include = ["scripts*"]
```

- [ ] **Step 2: Add httpx and posthog to dependencies**

Add to the `dependencies` list (after `"rich>=13.0"`):
```toml
    "httpx>=0.24",
    "posthog>=3.0",
```

- [ ] **Step 3: Add ruff to dev dependencies**

Add to `[project.optional-dependencies] dev`:
```toml
    "ruff>=0.3",
    "pytest-httpx>=0.21",
```

- [ ] **Step 4: Verify pyproject.toml is valid**

```bash
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb')); print('OK')"
```
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "feat: update pyproject.toml — packages.find, httpx, posthog, ruff"
```

### Task 3: Update .gitignore

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add missing entries to .gitignore**

Append to `.gitignore`:
```
.env
.DS_Store
.idea/
.vscode/
*.pem
*.key
screenshots/
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: expand .gitignore — IDE, secrets, screenshots"
```

### Task 4: Verify directory placeholders

**Note:** `docs/superpowers/plans/` and `docs/superpowers/specs/` already exist (created during brainstorming). This task is a no-op — verify the directories exist and skip if so.

- [ ] **Step 1: Verify directories exist**

```bash
ls docs/superpowers/plans/ docs/superpowers/specs/
```
Expected: Both directories exist with content.

---

## Chunk 2: New Python Modules

### Task 5: Add scripts/http.py

**Files:**
- Create: `scripts/http.py`
- Create: `tests/test_http.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_http.py`:

```python
# tests/test_http.py
"""Tests for HTTP retry module."""
import httpx
import pytest

from scripts.http import resilient_request


def test_successful_request(httpx_mock):
    """A 200 response returns immediately."""
    httpx_mock.add_response(url="https://example.com/api", json={"ok": True})
    resp = resilient_request("GET", "https://example.com/api", retries=1)
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_retries_on_500(httpx_mock):
    """Retries on 500 then succeeds."""
    httpx_mock.add_response(url="https://example.com/api", status_code=500)
    httpx_mock.add_response(url="https://example.com/api", json={"ok": True})
    resp = resilient_request(
        "GET", "https://example.com/api", retries=2, backoff_base=0.01
    )
    assert resp.status_code == 200


def test_no_retry_on_404(httpx_mock):
    """404 is not retried."""
    httpx_mock.add_response(url="https://example.com/api", status_code=404)
    with pytest.raises(httpx.HTTPStatusError):
        resilient_request("GET", "https://example.com/api", retries=3, backoff_base=0.01)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pip install pytest-httpx 2>/dev/null; python -m pytest tests/test_http.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.http'`

- [ ] **Step 3: Write scripts/http.py**

Create `scripts/http.py`:

```python
"""HTTP retry wrapper with exponential backoff and jitter."""
import os
import random
import time
from typing import Any, Optional, Union

import httpx

from scripts.logger import ToolkitLogger

log = ToolkitLogger("http")

_RETRYABLE_STATUS = {500, 502, 503, 504, 429}


def _get_verify() -> Union[str, bool]:
    """Resolve TLS verification: honor SSL_CERT_FILE and REQUESTS_CA_BUNDLE."""
    return (
        os.environ.get("SSL_CERT_FILE")
        or os.environ.get("REQUESTS_CA_BUNDLE")
        or True
    )


def resilient_request(
    method: str,
    url: str,
    *,
    retries: int = 3,
    backoff_base: float = 1.0,
    timeout: float = 30.0,
    **kwargs: Any,
) -> httpx.Response:
    """Make an HTTP request with exponential backoff on transient failures.

    Retries on: connection errors, timeouts, and 5xx/429 status codes.
    Does NOT retry on 4xx client errors (except 429).
    """
    if retries < 1:
        raise ValueError("retries must be >= 1")

    if "verify" not in kwargs:
        kwargs["verify"] = _get_verify()

    last_exc: Optional[Exception] = None

    for attempt in range(1, retries + 1):
        try:
            resp = httpx.request(method, url, timeout=timeout, **kwargs)
            resp.raise_for_status()
            return resp
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            last_exc = e
            if attempt < retries:
                wait = backoff_base * (2 ** (attempt - 1)) * (0.5 + random.random())
                log.warning(
                    "%s %s failed (attempt %d/%d): %s. Retrying in %.1fs...",
                    method, url, attempt, retries, type(e).__name__, wait,
                )
                time.sleep(wait)
            else:
                log.error("%s %s failed after %d attempts: %s", method, url, retries, e)
                raise
        except httpx.HTTPStatusError as e:
            if e.response.status_code not in _RETRYABLE_STATUS:
                raise
            last_exc = e
            if attempt < retries:
                base_wait = backoff_base * (2 ** (attempt - 1))
                jitter = random.uniform(0, base_wait * 0.5)
                wait = base_wait + jitter
                log.warning(
                    "%s %s returned %d (attempt %d/%d). Retrying in %.1fs...",
                    method, url, e.response.status_code, attempt, retries, wait,
                )
                time.sleep(wait)
            else:
                log.error(
                    "%s %s failed after %d attempts: HTTP %d",
                    method, url, retries, e.response.status_code,
                )
                raise

    raise last_exc
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_http.py -v
```
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add scripts/http.py tests/test_http.py
git commit -m "feat: add HTTP retry module with exponential backoff"
```

### Task 6: Add scripts/deps.py

**Files:**
- Create: `scripts/deps.py`
- Create: `tests/test_deps.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_deps.py`:

```python
# tests/test_deps.py
"""Tests for dependency checker."""
from scripts.deps import _is_importable, _pip_name, check_all, CORE_DEPS


def test_is_importable_stdlib():
    """os is always importable."""
    assert _is_importable("os") is True


def test_is_importable_nonexistent():
    """Fake module is not importable."""
    assert _is_importable("__nonexistent_module__") is False


def test_pip_name_mapped():
    """yaml maps to PyYAML."""
    assert _pip_name("yaml") == "PyYAML"


def test_pip_name_passthrough():
    """Unmapped names pass through."""
    assert _pip_name("httpx") == "httpx"


def test_check_all_returns_dict():
    """check_all returns a dict with core and tools keys."""
    status = check_all()
    assert "core" in status
    assert "tools" in status
    assert isinstance(status["core"], dict)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_deps.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.deps'`

- [ ] **Step 3: Write scripts/deps.py**

Create `scripts/deps.py`:

```python
"""Dependency checker for dbt-toolkit."""
import importlib
import subprocess
import sys

from scripts.logger import ToolkitLogger

log = ToolkitLogger("deps")

# Map of import name -> pip package name (only where they differ)
_PIP_NAMES = {
    "yaml": "PyYAML",
}

# Required for core functionality
CORE_DEPS = ["yaml", "paramiko", "click", "rich"]

# Optional extras
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
            capture_output=True, text=True, timeout=120,
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
    except ImportError:
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
            [dbt, "--version"], capture_output=True, text=True, timeout=30,
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
        dbt_ok = subprocess.run(
            [dbt, "--version"], capture_output=True, text=True, timeout=10,
        ).returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        dbt_ok = False
    status["tools"]["dbt"] = dbt_ok

    if include_optional:
        for dep in OPTIONAL_DEPS:
            status["optional"][_pip_name(dep)] = _is_importable(dep)

    return status
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_deps.py -v
```
Expected: 5 PASSED

- [ ] **Step 5: Commit**

```bash
git add scripts/deps.py tests/test_deps.py
git commit -m "feat: add dependency checker module"
```

### Task 7: Add scripts/telemetry.py

**Files:**
- Create: `scripts/telemetry.py`
- Create: `tests/test_telemetry.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_telemetry.py`:

```python
# tests/test_telemetry.py
"""Tests for telemetry module."""
import os
import yaml
from pathlib import Path

from scripts.telemetry import Telemetry, _NullTelemetry, get_telemetry, _system_properties


def _write_config(path: Path, enabled: bool = False, anon_id: str = "") -> Path:
    config = {"version": 1, "telemetry": {"enabled": enabled}}
    if anon_id:
        config["telemetry"]["anonymous_id"] = anon_id
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(config))
    return path


def test_null_telemetry_returned_without_config():
    """get_telemetry() without config returns NullTelemetry."""
    import scripts.telemetry as mod
    mod._instance = None  # reset singleton
    t = get_telemetry()
    assert isinstance(t, _NullTelemetry)
    # No-ops should not raise
    t.track("test")
    t.track_error("cmd", "err", "msg")
    t.identify()
    t.shutdown()


def test_disabled_by_default(tmp_path):
    """Telemetry disabled when config says enabled: false."""
    cfg = _write_config(tmp_path / "config.yaml", enabled=False)
    t = Telemetry(cfg)
    assert t._enabled is False
    assert t._client is None


def test_enabled_but_no_posthog_key(tmp_path, monkeypatch):
    """Enabled in config but no POSTHOG_API_KEY — client is None."""
    monkeypatch.delenv("POSTHOG_API_KEY", raising=False)
    cfg = _write_config(tmp_path / "config.yaml", enabled=True)
    t = Telemetry(cfg)
    assert t._enabled is True
    assert t._client is None
    assert len(t.anonymous_id) == 16


def test_anonymous_id_persisted(tmp_path):
    """Anonymous ID is saved back to config file."""
    cfg = _write_config(tmp_path / "config.yaml", enabled=True)
    t = Telemetry(cfg)
    saved = yaml.safe_load(cfg.read_text())
    assert saved["telemetry"]["anonymous_id"] == t.anonymous_id


def test_anonymous_id_reused(tmp_path):
    """Existing anonymous ID is reused, not regenerated."""
    cfg = _write_config(tmp_path / "config.yaml", enabled=True, anon_id="existing1234abcd")
    t = Telemetry(cfg)
    assert t.anonymous_id == "existing1234abcd"


def test_system_properties():
    """System properties include expected keys."""
    props = _system_properties()
    assert "os" in props
    assert "python_version" in props
    assert "plugin_version" in props


def test_timed_context_manager(tmp_path, monkeypatch):
    """timed() context manager works without error."""
    monkeypatch.delenv("POSTHOG_API_KEY", raising=False)
    cfg = _write_config(tmp_path / "config.yaml", enabled=True)
    t = Telemetry(cfg)
    with t.timed("test_command"):
        pass  # no error
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_telemetry.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.telemetry'`

- [ ] **Step 3: Write scripts/telemetry.py**

Create `scripts/telemetry.py`:

```python
"""Anonymous opt-in telemetry for dbt-toolkit."""
import contextlib
import hashlib
import json
import os
import platform
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from scripts.logger import ToolkitLogger

log = ToolkitLogger("telemetry")


def _read_plugin_version() -> str:
    """Read version from plugin.json (single source of truth)."""
    try:
        plugin_json = Path(__file__).parent.parent / ".claude-plugin" / "plugin.json"
        with open(plugin_json) as f:
            return json.load(f).get("version", "0.0.0")
    except Exception:
        return "0.0.0"


_PLUGIN_VERSION = _read_plugin_version()

_POSTHOG_API_KEY = os.environ.get("POSTHOG_API_KEY", "")
_POSTHOG_HOST = os.environ.get("POSTHOG_HOST", "https://us.i.posthog.com")

_instance: Optional["Telemetry"] = None


def get_telemetry(config_path: Optional[Path] = None) -> "Telemetry":
    """Get or create the global Telemetry singleton."""
    global _instance
    if _instance is None:
        if config_path is None:
            return _NullTelemetry()
        _instance = Telemetry(config_path)
    return _instance


def _system_properties() -> Dict[str, Any]:
    """Collect anonymous system properties."""
    return {
        "os": platform.system(),
        "os_version": platform.release(),
        "python_version": platform.python_version(),
        "arch": platform.machine(),
        "plugin_version": _PLUGIN_VERSION,
    }


def _create_posthog_client():
    """Create PostHog client, returns None if unavailable."""
    if not _POSTHOG_API_KEY:
        return None
    try:
        from posthog import Posthog
        return Posthog(project_api_key=_POSTHOG_API_KEY, host=_POSTHOG_HOST)
    except ImportError:
        log.debug("posthog package not installed — telemetry disabled")
        return None
    except Exception as e:
        log.debug("Failed to create PostHog client: %s", e)
        return None


class _NullTelemetry:
    """No-op telemetry returned when not initialized."""
    anonymous_id = ""

    def track(self, event, properties=None): pass
    def track_error(self, command, error_type, message): pass
    def identify(self): pass
    @contextlib.contextmanager
    def timed(self, command, **extra): yield
    def shutdown(self): pass


class Telemetry:
    """Anonymous usage telemetry. Opt-in via config (telemetry.enabled: true)."""

    def __init__(self, config_path: Path):
        self._config_path = Path(config_path)
        self._enabled = False
        self._client = None
        self.anonymous_id = ""

        config = self._load_config()
        telem_config = config.get("telemetry", {}) or {}
        self._enabled = bool(telem_config.get("enabled", False))

        if not self._enabled:
            return

        self.anonymous_id = telem_config.get("anonymous_id", "") or ""
        if not self.anonymous_id:
            raw_id = str(uuid.uuid4())
            self.anonymous_id = hashlib.sha256(raw_id.encode()).hexdigest()[:16]
            self._save_anonymous_id(self.anonymous_id)

        self._client = _create_posthog_client()

    def _load_config(self) -> dict:
        try:
            with open(self._config_path) as f:
                data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_anonymous_id(self, anon_id: str) -> None:
        """Persist the anonymous ID back into config.yaml."""
        try:
            config = self._load_config()
            if "telemetry" not in config:
                config["telemetry"] = {}
            config["telemetry"]["anonymous_id"] = anon_id

            fd, tmp = tempfile.mkstemp(
                dir=self._config_path.parent, suffix=".tmp"
            )
            try:
                with os.fdopen(fd, "w") as f:
                    yaml.safe_dump(config, f, default_flow_style=False)
                os.replace(tmp, self._config_path)
            except BaseException:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise
        except Exception as e:
            log.debug("Could not persist anonymous_id: %s", e)

    def identify(self) -> None:
        """Send system properties to PostHog."""
        if not self._enabled or not self._client:
            return
        try:
            self._client.identify(
                distinct_id=self.anonymous_id,
                properties=_system_properties(),
            )
        except Exception as e:
            log.debug("Telemetry identify failed: %s", e)

    def track(self, event: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """Send an anonymous event."""
        if not self._enabled or not self._client:
            return
        try:
            props = _system_properties()
            props.update(properties or {})
            self._client.capture(
                distinct_id=self.anonymous_id,
                event=event,
                properties=props,
            )
        except Exception as e:
            log.debug("Telemetry send failed: %s", e)

    def track_error(self, command: str, error_type: str, message: str) -> None:
        """Track an error event (message is sanitized)."""
        self.track("error", {
            "command": command,
            "error_type": error_type,
            "error_message": self._sanitize(message, max_length=200),
        })

    @staticmethod
    def _sanitize(text: str, max_length: int = 500) -> str:
        """Truncate text for telemetry."""
        return text[:max_length]

    @contextlib.contextmanager
    def timed(self, command: str, **extra):
        """Context manager that tracks command duration."""
        start = time.monotonic()
        error = None
        try:
            yield
        except Exception as e:
            error = e
            raise
        finally:
            duration_ms = int((time.monotonic() - start) * 1000)
            props = {"command": command, "duration_ms": duration_ms, **extra}
            if error:
                props["error"] = type(error).__name__
                self.track("command_error", props)
            else:
                self.track("command_success", props)

    def shutdown(self) -> None:
        """Flush and close the client."""
        if self._client:
            try:
                self._client.shutdown()
            except Exception:
                pass
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_telemetry.py -v
```
Expected: 7 PASSED

- [ ] **Step 5: Commit**

```bash
git add scripts/telemetry.py tests/test_telemetry.py
git commit -m "feat: add anonymous opt-in telemetry module"
```

---

## Chunk 3: Test Fixtures

### Task 8: Add tests/fixtures/

**Files:**
- Create: `tests/fixtures/__init__.py`
- Create: `tests/fixtures/sample_manifest.json`
- Create: `tests/fixtures/sample_run_results.json`
- Create: `tests/fixtures/sample_config.yaml`
- Create: `tests/fixtures/sample_sources.json`
- Create: `tests/fixtures/sample_dbt_project.yml`

- [ ] **Step 1: Create tests/fixtures/__init__.py**

```python
# Empty package marker
```

- [ ] **Step 2: Create sample_manifest.json**

Create `tests/fixtures/sample_manifest.json`:

```json
{
  "metadata": {
    "dbt_version": "1.8.0",
    "adapter_type": "redshift",
    "generated_at": "2026-03-14T12:00:00Z"
  },
  "nodes": {
    "model.my_project.stg_orders": {
      "resource_type": "model",
      "unique_id": "model.my_project.stg_orders",
      "name": "stg_orders",
      "schema": "staging",
      "config": {"materialized": "view"},
      "depends_on": {"nodes": ["source.my_project.raw.orders"]}
    },
    "model.my_project.fct_revenue": {
      "resource_type": "model",
      "unique_id": "model.my_project.fct_revenue",
      "name": "fct_revenue",
      "schema": "marts",
      "config": {"materialized": "incremental"},
      "depends_on": {"nodes": ["model.my_project.stg_orders"]}
    },
    "test.my_project.not_null_stg_orders_id": {
      "resource_type": "test",
      "unique_id": "test.my_project.not_null_stg_orders_id",
      "name": "not_null_stg_orders_id",
      "depends_on": {"nodes": ["model.my_project.stg_orders"]}
    }
  },
  "sources": {
    "source.my_project.raw.orders": {
      "resource_type": "source",
      "unique_id": "source.my_project.raw.orders",
      "name": "orders",
      "source_name": "raw",
      "schema": "raw_data"
    }
  },
  "parent_map": {
    "model.my_project.stg_orders": ["source.my_project.raw.orders"],
    "model.my_project.fct_revenue": ["model.my_project.stg_orders"],
    "test.my_project.not_null_stg_orders_id": ["model.my_project.stg_orders"]
  },
  "child_map": {
    "source.my_project.raw.orders": ["model.my_project.stg_orders"],
    "model.my_project.stg_orders": ["model.my_project.fct_revenue", "test.my_project.not_null_stg_orders_id"],
    "model.my_project.fct_revenue": []
  }
}
```

- [ ] **Step 3: Create sample_run_results.json**

Create `tests/fixtures/sample_run_results.json`:

```json
{
  "metadata": {"dbt_version": "1.8.0"},
  "elapsed_time": 45.2,
  "results": [
    {
      "unique_id": "model.my_project.stg_orders",
      "status": "success",
      "execution_time": 10.1,
      "message": "OK"
    },
    {
      "unique_id": "model.my_project.fct_revenue",
      "status": "error",
      "execution_time": 4.6,
      "message": "Relation \"staging\".\"stg_orders\" does not exist"
    },
    {
      "unique_id": "test.my_project.not_null_stg_orders_id",
      "status": "warn",
      "execution_time": 2.3,
      "message": "Got 3 results, configured to warn if != 0"
    }
  ]
}
```

- [ ] **Step 4: Create sample_config.yaml**

Create `tests/fixtures/sample_config.yaml`:

```yaml
version: 1

project:
  name: "my_project"
  dir: "."

execution:
  method: "local"

profile:
  name: "default"
  target: "dev"

defaults:
  threads: 4
  full_refresh: false
  fail_fast: false
  log_format: "json"

freshness:
  enabled: true
  warn_after_hours: 24
  tracked_sources: []

audit:
  check_sort_dist: true
  check_undocumented: true
  check_test_coverage: true
  min_test_coverage: 0.8

tags:
  favorites: ["daily", "revenue"]
```

- [ ] **Step 5: Create sample_sources.json**

Create `tests/fixtures/sample_sources.json`:

```json
{
  "metadata": {},
  "results": [
    {
      "unique_id": "source.my_project.raw.orders",
      "status": "pass",
      "max_loaded_at": "2026-03-14T10:00:00Z",
      "max_loaded_at_time_ago_in_s": 3600
    },
    {
      "unique_id": "source.my_project.raw.events",
      "status": "warn",
      "max_loaded_at": "2026-03-10T10:00:00Z",
      "max_loaded_at_time_ago_in_s": 345600
    }
  ]
}
```

- [ ] **Step 6: Create sample_dbt_project.yml**

Create `tests/fixtures/sample_dbt_project.yml`:

```yaml
name: "my_project"
version: "1.0.0"
config-version: 2
profile: "default"

model-paths: ["models"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]

target-path: "target"
clean-targets: ["target", "dbt_packages"]
```

- [ ] **Step 7: Run existing tests to verify nothing is broken**

```bash
python -m pytest tests/ -v --ignore=tests/test_http.py --ignore=tests/test_deps.py --ignore=tests/test_telemetry.py
```
Expected: All 13 existing test modules pass

- [ ] **Step 8: Commit**

```bash
git add tests/fixtures/
git commit -m "feat: add test fixtures for manifest, run_results, config, sources, dbt_project"
```

---

## Chunk 4: CI/CD Scaffolding

### Task 9: Add GitHub Actions workflows

**Files:**
- Create: `.github/workflows/test.yml`
- Create: `.github/workflows/lint.yml`

- [ ] **Step 1: Create .github/workflows/test.yml**

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests
        run: |
          python -m pytest tests/ -v --tb=short
```

- [ ] **Step 2: Create .github/workflows/lint.yml**

```yaml
name: Lint

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install ruff
        run: pip install ruff>=0.3

      - name: Check formatting
        run: ruff format --check .

      - name: Check linting
        run: ruff check .
```

- [ ] **Step 3: Commit**

```bash
git add .github/
git commit -m "ci: add GitHub Actions for tests (Python 3.9-3.12) and ruff linting"
```

### Task 10: Add CONTRIBUTING.md

**Files:**
- Create: `CONTRIBUTING.md`

- [ ] **Step 1: Write CONTRIBUTING.md**

```markdown
# Contributing to dbt-toolkit

## Development Setup

```bash
git clone https://github.com/rishavchatterjee/dbt-toolkit.git
cd dbt-toolkit
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## Adding a Skill

1. Create `skills/<skill-name>/SKILL.md` with frontmatter:
   ```yaml
   ---
   name: <skill-name>
   description: "One-line description"
   ---
   ```
2. Follow the Conversation Principles: never ask technical/infra questions — only business intent
3. Add routing logic to `skills/dbt/SKILL.md`
4. Reference relevant `references/*.md` docs

## Design Principles

- **Business questions only** — skills never ask CLI flags, config syntax, or YAML formatting
- **Auto-resolve** — derive everything from config + project state
- **Fail safe** — every external call has retries, timeouts, and error handling
- **DRY** — reuse scripts modules, don't duplicate logic in skills
- **TDD** — write failing tests first, then implement

## Code Style

- Linted with [ruff](https://docs.astral.sh/ruff/)
- Run `ruff check .` and `ruff format --check .` before committing
- Type hints encouraged but not required

## Pull Request Process

1. Fork the repo and create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass: `python -m pytest tests/ -v`
4. Ensure linting passes: `ruff check . && ruff format --check .`
5. Open a PR against `main`
```

- [ ] **Step 2: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: add CONTRIBUTING.md"
```

### Task 11: Add CHANGELOG.md

**Files:**
- Create: `CHANGELOG.md`

- [ ] **Step 1: Write CHANGELOG.md**

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Marketplace packaging (marketplace.json)
- Telemetry module (anonymous, opt-in via PostHog)
- Dependency checker module
- HTTP retry module with exponential backoff
- GitHub Actions CI (tests + linting)
- CONTRIBUTING.md
- Test fixtures (sample manifest, run_results, config, sources, dbt_project)

## [0.1.0] - 2026-03-15

### Added
- 16 skills: router, setup, run, test, freshness, debug, audit, develop, docs, artifacts, seed/snapshot, deps, run-operation, brainstorming, executing-plans, code-review
- 12 Python modules: config, runner, artifacts, lineage, freshness, coverage, audit, selector, error_patterns, state, cli, logger
- 2 agents: lineage-agent, test-failure-agent
- 7 reference documents: artifacts, common-pitfalls, dbt-commands, incremental-models, jinja-context, node-selection, redshift-specifics
- 5 templates: CLAUDE.md, config.yaml, model.sql, test.sql, unit_test.yaml
- Session-start hook for auto-detection
- 3 execution methods: local, SSH, Docker
- 17 error patterns across 8 categories
```

- [ ] **Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: add CHANGELOG.md"
```

### Task 12: Add templates/gitignore.template

**Files:**
- Create: `templates/gitignore.template`

- [ ] **Step 1: Write gitignore.template**

```
# Python
__pycache__/
*.pyc
*.pyo
.venv/
*.egg-info/
dist/
build/

# dbt
target/
dbt_packages/
logs/

# dbt-toolkit
.dbt-toolkit/.secrets/
.dbt-toolkit/cache/
.dbt-toolkit/freshness_history.json

# IDE
.vscode/
.idea/

# OS
.DS_Store

# Secrets
.env
*.pem
*.key

# Testing
.pytest_cache/
.coverage
htmlcov/
```

- [ ] **Step 2: Commit**

```bash
git add templates/gitignore.template
git commit -m "feat: add gitignore template for scaffolded dbt projects"
```

---

## Chunk 5: LICENSE & README Rewrite

### Task 13: Rewrite LICENSE

**Files:**
- Rewrite: `LICENSE`

- [ ] **Step 1: Replace LICENSE with official MariaDB BUSL-1.1 template**

Write `LICENSE`:

```
BSL License

Copyright (c) 2026 Rishav Chatterjee

License text copyright © 2024 MariaDB plc, All Rights Reserved. "Business Source License" is a trademark of MariaDB plc.

Parameters

Licensor:             Rishav Chatterjee
Licensed Work:        dbt-toolkit 0.1.0
Change Date:          2030-03-15
Change License:       Apache License 2.0
Additional Use Grant: None

Terms
The Licensor hereby grants you the right to copy, modify, create derivative works, redistribute, and make non-production use of the Licensed Work. The Licensor may make an Additional Use Grant, above, permitting limited production use.

Effective on the Change Date, or the fourth anniversary of the first publicly available distribution of a specific version of the Licensed Work under this License, whichever comes first, the Licensor hereby grants you rights under the terms of the Change License, and the rights granted in the paragraph above terminate.

If your use of the Licensed Work does not comply with the requirements currently in effect as described in this License, you must purchase a commercial license from the Licensor, its affiliated entities, or authorized resellers, or you must refrain from using the Licensed Work.

All copies of the original and modified Licensed Work, and derivative works of the Licensed Work, are subject to this License. This License applies separately for each version of the Licensed Work and the Change Date may vary for each version of the Licensed Work released by Licensor.

You must conspicuously display this License on each original or modified copy of the Licensed Work. If you receive the Licensed Work in original or modified form from a third party, the terms and conditions set forth in this License apply to your use of that work.

Any use of the Licensed Work in violation of this License will automatically terminate your rights under this License for the current and all other versions of the Licensed Work.

This License does not grant you any right in any trademark or logo of Licensor or its affiliates (provided that you may use a trademark or logo of Licensor as expressly required by this License).

TO THE EXTENT PERMITTED BY APPLICABLE LAW, THE LICENSED WORK IS PROVIDED ON AN "AS IS" BASIS. LICENSOR HEREBY DISCLAIMS ALL WARRANTIES AND CONDITIONS, EXPRESS OR IMPLIED, INCLUDING (WITHOUT LIMITATION) WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT, AND TITLE. MariaDB hereby grants you permission to use this License's text to license your works, and to refer to it using the trademark "Business Source License", as long as you comply with the Covenants of Licensor below.

Covenants of Licensor
In consideration of the right to use this License's text and the "Business Source License" name and trademark, Licensor covenants to MariaDB, and to all other recipients of the licensed work to be provided by Licensor:

To specify as the Change License the GPL Version 2.0 or any later version, or a license that is compatible with GPL Version 2.0 or a later version, where "compatible" means that software provided under the Change License can be included in a program with software provided under GPL Version 2.0 or a later version. Licensor may specify additional Change Licenses without limitation.
To either: (a) specify an additional grant of rights to use that does not impose any additional restriction on the right granted in this License, as the Additional Use Grant; or (b) insert the text "None" to specify a Change Date. Not to modify this License in any other way.
```

- [ ] **Step 2: Commit**

```bash
git add LICENSE
git commit -m "docs: replace LICENSE with official MariaDB BUSL-1.1 template"
```

### Task 14: Rewrite README.md

**Files:**
- Rewrite: `README.md`

- [ ] **Step 1: Write the new README.md**

Full content for `README.md` — replace entirely:

```markdown
<p align="center">
  <img src="https://img.shields.io/badge/Claude_Code-Plugin-blueviolet?style=for-the-badge" alt="Claude Code Plugin" />
  <img src="https://img.shields.io/badge/dbt-Toolkit-orange?style=for-the-badge" alt="dbt Toolkit" />
  <img src="https://img.shields.io/badge/version-0.1.0-green?style=for-the-badge" alt="Version 0.1.0" />
  <img src="https://img.shields.io/badge/license-BUSL_1.1-blue?style=for-the-badge" alt="License" />
</p>

# dbt-toolkit

**Stop guessing at dbt.** A Claude Code plugin that makes dbt development safe, systematic, and mistake-proof.

One command — `/dbt-toolkit:dbt` — gives your team smart model selection, execution across local/SSH/Docker, automatic error diagnosis, lineage analysis, test coverage tracking, and freshness monitoring. No more hunting through logs, memorizing CLI flags, or forgetting which models to run.

---

## Install

```bash
# From the Claude Code official marketplace
/plugin install dbt-toolkit

# Or install directly from GitHub
/plugin install github:rishavchatterjee/dbt-toolkit
```

**Prerequisites:** Python 3.9+ and [Claude Code](https://claude.ai/code) with plugin support.

---

## How It Works

```
You say:                              dbt-toolkit does:
───────────────────────────────────── ──────────────────────────────────────
/dbt-toolkit:dbt run                  Config → Selector → Execute → Parse results
/dbt-toolkit:dbt test                 Run tests → Analyze failures → Coverage report
/dbt-toolkit:dbt freshness            Check sources → Track history → Warn on stale
/dbt-toolkit:dbt debug                Error patterns → Root cause → Suggested fix
/dbt-toolkit:dbt "run my revenue      NLP routing → Same safe workflow
  models"
```

### The Execution Flow

```
                    ┌─────────────────────────────────────────┐
                    │       /dbt-toolkit:dbt run               │
                    └────────────────┬────────────────────────┘
                                     │
                    ┌────────────────▼────────────────────────┐
                    │  1. Load config (.dbt-toolkit/config.yaml│
                    │  2. Build selector (tag:, path:, config:)│
                    │  3. Detect execution method              │
                    └────────────────┬────────────────────────┘
                                     │
                          ┌──────────┴──────────┐
                          │                     │
                    ┌─────▼──────┐  ┌───────────▼──┐  ┌──────▼─────┐
                    │   Local    │  │     SSH      │  │   Docker   │
                    │  (direct)  │  │  (remote)    │  │ (container)│
                    └─────┬──────┘  └──────┬───────┘  └──────┬─────┘
                          │                │                  │
                    ┌─────▼────────────────▼──────────────────▼─────┐
                    │  4. Parse run_results.json                     │
                    │  5. Match errors against 17 patterns           │
                    │  6. Report: successes, failures, slowest model │
                    └───────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Install the plugin
/plugin install dbt-toolkit

# 2. Navigate to your dbt project
cd my-dbt-project

# 3. Run the toolkit
/dbt-toolkit:dbt
```

Setup auto-detects your `dbt_project.yml` and walks you through configuration: execution method, profile, target, and defaults.

---

## Features

| Feature | What it does |
|---------|-------------|
| **Smart routing** | `/dbt-toolkit:dbt` + anything — natural language or direct commands |
| **3 execution methods** | Local, SSH (auto-handles venv + env vars), Docker (auto-mounts volumes) |
| **17 error patterns** | Auto-match errors across 8 categories with suggested fixes |
| **DAG lineage** | Traverse upstream/downstream, calculate impact radius |
| **Test coverage** | Track test-to-model ratios, flag undocumented models |
| **Freshness tracking** | Monitor source staleness with history and warnings |
| **Secret sanitization** | Passwords, tokens, and keys never appear in logs |
| **Audit health checks** | Sort/dist keys, materialization, test coverage, tags |
| **Scaffolding templates** | Model, test, unit test, config templates |

---

## Skills (16)

| # | Skill | Invoke with | Purpose |
|---|-------|-------------|---------|
| 1 | Router | `/dbt-toolkit:dbt` | Interactive menu + NLP routing |
| 2 | Setup | `/dbt-toolkit:dbt-setup` | First-time configuration wizard |
| 3 | Run | `/dbt-toolkit:dbt-run` | Execute models with smart selection |
| 4 | Test | `/dbt-toolkit:dbt-test` | Run tests, analyze failures, coverage |
| 5 | Freshness | `/dbt-toolkit:dbt-freshness` | Source data freshness checks |
| 6 | Debug | `/dbt-toolkit:dbt-debug` | Systematic troubleshooting |
| 7 | Audit | `/dbt-toolkit:dbt-audit` | Proactive health checks |
| 8 | Develop | `/dbt-toolkit:dbt-develop` | Scaffold, compile, preview, lineage |
| 9 | Docs | `/dbt-toolkit:dbt-docs` | Generate and audit documentation |
| 10 | Artifacts | `/dbt-toolkit:dbt-artifacts` | Parse and compare run outputs |
| 11 | Seed & Snapshot | `/dbt-toolkit:dbt-seed-snapshot` | Seed loading, SCD snapshots |
| 12 | Deps | `/dbt-toolkit:dbt-deps` | Package management |
| 13 | Run Operation | `/dbt-toolkit:dbt-run-operation` | Execute dbt macros |
| 14 | Brainstorm | `/dbt-toolkit:dbt-brainstorming` | Model design exploration |
| 15 | Execute Plans | `/dbt-toolkit:dbt-executing-plans` | Step-by-step with dbt checkpoints |
| 16 | Code Review | `/dbt-toolkit:dbt-code-review` | SQL quality and best practices |

Or just describe what you want:

```
/dbt-toolkit:dbt run my revenue models
/dbt-toolkit:dbt why did my test fail?
/dbt-toolkit:dbt what depends on stg_orders?
```

---

## Execution Methods

**Local** — dbt installed on your machine. Runs directly.

**SSH** — dbt on a remote server. Auto-handles:
- SSH key authentication
- Virtual environment activation
- Environment variable forwarding
- Remote project path resolution

**Docker** — dbt in a container. Auto-handles:
- Volume mounting for project files
- Image management
- Adapter-specific images

---

## Error Patterns

17 patterns across 8 categories with auto-matching and suggested fixes:

| Category | Patterns | Example |
|----------|----------|---------|
| Connection | 3 | Refused, timeout, authentication failure |
| Compilation | 3 | Undefined ref, missing node, circular dependency |
| Runtime SQL | 4 | Relation not found, duplicate key, missing column, disk full |
| Permission | 2 | Access denied, insufficient privileges |
| Performance | 2 | Statement timeout, serializable isolation |
| Parse | 1 | YAML/Jinja syntax errors |
| Redshift | 1 | Spectrum CTAS, MERGE not supported |
| Incremental | 1 | Schema change, full refresh needed |

---

## Lineage

Traverse the DAG from `manifest.json`:

- **Upstream:** What does this model depend on?
- **Downstream:** What breaks if I change this model?
- **Impact radius:** How many models are affected?

Used by the run, develop, and audit skills to build smart selectors and assess change impact.

---

## Configuration

Created by `/dbt-toolkit:dbt-setup` at `.dbt-toolkit/config.yaml`:

```yaml
version: 1

execution:
  method: "local"  # or "ssh" or "docker"

profile:
  name: "my_profile"
  target: "dev"

defaults:
  threads: 4
  full_refresh: false
  fail_fast: false
  log_format: "json"

freshness:
  enabled: true
  warn_after_hours: 24

audit:
  check_sort_dist: true
  check_test_coverage: true
  min_test_coverage: 0.8
```

See `templates/config.yaml` for all options including SSH and Docker configuration.

<details>
<summary><strong>Telemetry (optional)</strong></summary>

Anonymous, opt-in usage telemetry via PostHog. Inert unless configured:

```bash
export POSTHOG_API_KEY="your-posthog-project-key"
```

Also requires `telemetry.enabled: true` in config. No data is ever sent without both conditions met.

</details>

---

## Architecture

```
dbt-toolkit/
├── .claude-plugin/           Plugin metadata (plugin.json, marketplace.json)
├── hooks/                    Session auto-detection
├── skills/                   16 skills (each with SKILL.md)
│   ├── dbt/                  Router — single entry point
│   ├── dbt-setup/            First-time wizard
│   ├── dbt-run/              Execute models with smart selection
│   ├── dbt-test/             Run tests, analyze failures, coverage
│   ├── dbt-freshness/        Source data freshness checks
│   ├── dbt-debug/            Systematic troubleshooting
│   ├── dbt-audit/            Proactive health checks
│   ├── dbt-develop/          Scaffold, compile, preview, lineage
│   ├── dbt-docs/             Generate and audit documentation
│   ├── dbt-artifacts/        Parse and compare run outputs
│   ├── dbt-seed-snapshot/    Seed loading, SCD snapshots
│   ├── dbt-deps/             Package management
│   ├── dbt-run-operation/    Execute dbt macros
│   ├── dbt-brainstorming/    Model design exploration
│   ├── dbt-executing-plans/  Plan execution with checkpoints
│   └── dbt-code-review/      SQL quality and best practices
├── agents/                   Lineage + test-failure analysis agents
├── references/               dbt knowledge base (7 docs)
├── scripts/                  Python automation (15 modules)
│   ├── config.py             Config discovery and typed access
│   ├── runner.py             Execute dbt via local/SSH/Docker
│   ├── artifacts.py          Parse manifest, run_results, sources
│   ├── lineage.py            DAG traversal from manifest
│   ├── freshness.py          Freshness tracking with history
│   ├── coverage.py           Test and doc coverage analysis
│   ├── audit.py              Health checks (coverage, sort/dist, tags)
│   ├── selector.py           Build node selection strings
│   ├── error_patterns.py     17 patterns across 8 categories
│   ├── state.py              State comparison for CI/CD slim runs
│   ├── cli.py                Unified CLI entry point
│   ├── logger.py             Structured logging + secret sanitization
│   ├── telemetry.py          Anonymous opt-in telemetry
│   ├── deps.py               Dependency checking and validation
│   ├── http.py               HTTP retry with exponential backoff
│   └── bootstrap.sh          Environment detection script
├── templates/                Project scaffolding files
└── tests/                    Test suite (unit + integration)
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `PyYAML` | YAML parsing |
| `paramiko` | SSH execution |
| `click` | CLI framework |
| `rich` | Terminal formatting |
| `httpx` | HTTP client with retry support |
| `posthog` | Anonymous opt-in telemetry |

---

## For Contributors

### Running tests

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

### Design Principles

- **Business questions only** — skills never ask CLI flags, config syntax, or YAML formatting
- **Auto-resolve** — derive everything from config + project state
- **Fail safe** — every external call has retries, timeouts, and error handling
- **3 execution methods** — local, SSH, Docker — same skill logic regardless
- **Secret sanitization** — passwords and tokens never reach logs

### Adding a skill

1. Create `skills/your-skill/SKILL.md` with `name` and `description` frontmatter
2. Follow the Conversation Principles (never ask technical questions)
3. Add routing logic to `skills/dbt/SKILL.md`
4. Reference relevant `references/*.md` docs

---

## License

Business Source License 1.1 — see [LICENSE](LICENSE) for details.
Converts to Apache License 2.0 on 2030-03-15.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README for marketplace — badges, features, architecture"
```

---

## Chunk 6: Final Verification

### Task 15: Run full test suite and verify structure

- [ ] **Step 1: Install new dependencies**

```bash
cd /Users/rishavchatterjee/Desktop/TWC\ Projects/dbt-toolkit
pip install -e ".[dev]"
```

- [ ] **Step 2: Run full test suite**

```bash
python -m pytest tests/ -v
```
Expected: All tests pass (existing 13 modules + 3 new modules)

- [ ] **Step 3: Verify plugin structure matches preset-toolkit**

Check these files exist:
```bash
ls -la .claude-plugin/plugin.json .claude-plugin/marketplace.json
ls -la hooks/hooks.json hooks/session-start.sh
ls -la scripts/telemetry.py scripts/deps.py scripts/http.py
ls -la tests/fixtures/sample_manifest.json
ls -la .github/workflows/test.yml .github/workflows/lint.yml
ls -la CONTRIBUTING.md CHANGELOG.md LICENSE README.md
ls -la templates/gitignore.template
```
Expected: All files exist

- [ ] **Step 4: Verify root plugin.json is removed**

```bash
test ! -f plugin.json && echo "OK: root plugin.json removed"
```
Expected: `OK: root plugin.json removed`

- [ ] **Step 5: Final commit (if any unstaged changes)**

```bash
git status
```
Expected: clean working tree
