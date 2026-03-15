"""Tests for telemetry module."""

import yaml
from pathlib import Path

from scripts.telemetry import (
    Telemetry,
    _NullTelemetry,
    get_telemetry,
    _system_properties,
)


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

    mod._instance = None
    t = get_telemetry()
    assert isinstance(t, _NullTelemetry)
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
    cfg = _write_config(
        tmp_path / "config.yaml", enabled=True, anon_id="existing1234abcd"
    )
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
        pass
