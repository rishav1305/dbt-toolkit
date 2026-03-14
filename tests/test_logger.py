from scripts.logger import ToolkitLogger


def test_sanitize_removes_password():
    logger = ToolkitLogger("test")
    result = logger.sanitize("connecting with password=XpT4#gVnL9z2qBwK to host")
    assert "XpT4#gVnL9z2qBwK" not in result
    assert "***" in result


def test_sanitize_removes_token():
    logger = ToolkitLogger("test")
    result = logger.sanitize("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.abc")
    assert "eyJhbGciOiJIUzI1NiJ9" not in result


def test_sanitize_removes_key_path_values():
    logger = ToolkitLogger("test")
    result = logger.sanitize("using secret=my_secret_value for auth")
    assert "my_secret_value" not in result


def test_sanitize_preserves_safe_text():
    logger = ToolkitLogger("test")
    result = logger.sanitize("running dbt run --select tag:daily")
    assert result == "running dbt run --select tag:daily"
