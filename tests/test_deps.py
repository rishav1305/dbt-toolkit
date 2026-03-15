"""Tests for dependency checker."""

from scripts.deps import _is_importable, _pip_name, check_all


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
