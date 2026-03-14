# tests/test_cli.py
from click.testing import CliRunner

from scripts.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "dbt-toolkit" in result.output


def test_cli_audit_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["audit", "--help"])
    assert result.exit_code == 0
    assert "audit" in result.output.lower()


def test_cli_freshness_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["freshness", "--help"])
    assert result.exit_code == 0


def test_cli_coverage_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["coverage", "--help"])
    assert result.exit_code == 0
