"""Unified CLI entry point for dbt-toolkit scripts."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from scripts.config import ToolkitConfig

console = Console()


@click.group()
@click.pass_context
def cli(ctx):
    """dbt-toolkit — workflow-oriented dbt project management."""
    ctx.ensure_object(dict)
    cfg = ToolkitConfig.discover()
    if cfg:
        ctx.obj["config"] = cfg
    else:
        ctx.obj["config"] = None


@cli.command()
@click.option("--manifest", type=click.Path(exists=True), help="Path to manifest.json")
@click.option("--check-sort-dist/--no-check-sort-dist", default=True)
@click.option("--min-coverage", type=float, default=0.8)
@click.pass_context
def audit(ctx, manifest, check_sort_dist, min_coverage):
    """Run proactive health checks on the dbt project."""
    from scripts.audit import run_audit

    manifest_path = Path(manifest) if manifest else _find_manifest(ctx)
    if not manifest_path:
        click.echo("Error: manifest.json not found. Run 'dbt parse' first.", err=True)
        sys.exit(1)

    results = run_audit(
        manifest_path, check_sort_dist=check_sort_dist, min_test_coverage=min_coverage
    )

    table = Table(title="Audit Results")
    table.add_column("Severity", style="bold")
    table.add_column("Category")
    table.add_column("Model")
    table.add_column("Message")

    for r in sorted(
        results, key=lambda x: {"error": 0, "warning": 1, "info": 2}[x.severity]
    ):
        style = {"error": "red", "warning": "yellow", "info": "dim"}[r.severity]
        table.add_row(r.severity, r.category, r.model_id or "-", r.message, style=style)

    console.print(table)
    console.print(
        f"\n{len(results)} findings ({sum(1 for r in results if r.severity == 'error')} errors, "
        f"{sum(1 for r in results if r.severity == 'warning')} warnings, "
        f"{sum(1 for r in results if r.severity == 'info')} info)"
    )


@cli.command()
@click.option("--manifest", type=click.Path(exists=True), help="Path to manifest.json")
@click.pass_context
def coverage(ctx, manifest):
    """Show test and documentation coverage."""
    from scripts.coverage import compute_test_coverage, compute_doc_coverage

    manifest_path = Path(manifest) if manifest else _find_manifest(ctx)
    if not manifest_path:
        click.echo("Error: manifest.json not found.", err=True)
        sys.exit(1)

    test_cov = compute_test_coverage(manifest_path)
    doc_cov = compute_doc_coverage(manifest_path)

    console.print(
        f"\n[bold]Test Coverage:[/bold] {test_cov['coverage']:.0%} "
        f"({test_cov['tested_models']}/{test_cov['total_models']} models)"
    )
    if test_cov["untested_models"]:
        console.print(f"  Untested: {', '.join(test_cov['untested_models'][:10])}")

    console.print(
        f"\n[bold]Doc Coverage:[/bold] {doc_cov['documented_models']}/{doc_cov['total_models']} models"
    )
    if doc_cov["undocumented_models"]:
        console.print(
            f"  Undocumented: {', '.join(doc_cov['undocumented_models'][:10])}"
        )


@cli.command()
@click.option(
    "--sources-json", type=click.Path(exists=True), help="Path to sources.json"
)
@click.pass_context
def freshness(ctx, sources_json):
    """Show source freshness results."""
    from scripts.artifacts import parse_sources_freshness

    sources_path = (
        Path(sources_json) if sources_json else _find_artifact(ctx, "sources.json")
    )
    if not sources_path:
        click.echo(
            "Error: sources.json not found. Run 'dbt source freshness' first.", err=True
        )
        sys.exit(1)

    parsed = parse_sources_freshness(sources_path)

    table = Table(title="Source Freshness")
    table.add_column("Source")
    table.add_column("Status")
    table.add_column("Last Loaded")
    table.add_column("Age")

    for w in parsed["warnings"]:
        hours = w.get("time_ago_seconds", 0) / 3600
        table.add_row(
            w["unique_id"],
            w["status"],
            w.get("max_loaded_at", "unknown"),
            f"{hours:.0f}h ago",
            style="yellow" if w["status"] == "warn" else "red",
        )

    console.print(table)
    console.print(
        f"\nTotal: {parsed['total']} sources — "
        f"{parsed['pass']} pass, {parsed['warn']} warn, {parsed['error']} error"
    )


def _find_manifest(ctx) -> Path | None:
    cfg = ctx.obj.get("config")
    if cfg:
        p = cfg.project_root / "target" / "manifest.json"
        if p.exists():
            return p
    local = Path("target/manifest.json")
    return local if local.exists() else None


def _find_artifact(ctx, name: str) -> Path | None:
    cfg = ctx.obj.get("config")
    if cfg:
        p = cfg.project_root / "target" / name
        if p.exists():
            return p
    local = Path(f"target/{name}")
    return local if local.exists() else None


if __name__ == "__main__":
    cli()
