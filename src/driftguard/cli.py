"""Command-line interface: ``driftguard --help``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from driftguard import __version__
from driftguard.config import load_experiment_config
from driftguard.data.synthetic import generate_synthetic_flows
from driftguard.data_cli import data_app
from driftguard.reporting.provenance import environment_snapshot

app = typer.Typer(
    name="driftguard",
    help="DriftGuard-IoT research toolkit.",
    no_args_is_help=True,
    add_completion=False,
)
app.add_typer(data_app, name="data")

DEFAULT_SMOKE_CONFIG = Path("configs/experiments/smoke-synthetic.yaml")


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo(__version__)


@app.command()
def env() -> None:
    """Print the software environment recorded in run manifests."""
    typer.echo(json.dumps(environment_snapshot(), indent=2))


@app.command("validate-config")
def validate_config(
    path: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
) -> None:
    """Validate an experiment YAML file and its dataset/model references."""
    try:
        config = load_experiment_config(path)
    except (ValidationError, ValueError, OSError) as exc:
        typer.echo(f"INVALID: {path}\n{exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"OK: {config.name} (config hash {config.canonical_hash()[:12]})")


@app.command()
def synth(
    out: Annotated[Path, typer.Option(help="Destination CSV path.")],
    n_samples: Annotated[int, typer.Option(min=50)] = 1000,
    seed: Annotated[int, typer.Option(min=0)] = 0,
) -> None:
    """Write a synthetic flow table (for local fixtures; never a research dataset)."""
    df = generate_synthetic_flows(n_samples=n_samples, seed=seed)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    typer.echo(f"wrote {len(df)} synthetic rows to {out}")


@app.command()
def smoke(
    config: Annotated[
        Path, typer.Option(exists=True, dir_okay=False, help="Experiment config.")
    ] = DEFAULT_SMOKE_CONFIG,
    output_dir: Annotated[Path, typer.Option(help="Run output root.")] = Path("experiments/runs"),
) -> None:
    """Run the synthetic end-to-end smoke pipeline and write a smoke manifest."""
    from driftguard.smoke import run_smoke  # heavy imports only when needed

    summary = run_smoke(load_experiment_config(config), output_dir)
    typer.echo(summary["notice"])
    for model, metrics in summary["metrics"].items():
        typer.echo(f"  {model}: macro_f1={metrics['macro_f1']:.4f} (synthetic)")
    typer.echo(f"run directory: {summary['run_dir']}")


@app.command()
def train(
    config: Annotated[Path, typer.Option(exists=True, dir_okay=False, help="Experiment config.")],
    output_dir: Annotated[Path, typer.Option(help="Run output root.")] = Path("experiments/runs"),
    kind: Annotated[str, typer.Option(help="development | research")] = "development",
    save_models: Annotated[bool, typer.Option(help="Persist fitted pipelines")] = True,
) -> None:
    """Train and evaluate the configured baselines; writes a v2 manifest and metrics."""
    from driftguard.experiments import run_experiment

    if kind not in {"development", "research"}:
        typer.echo("kind must be 'development' or 'research'", err=True)
        raise typer.Exit(code=2)
    try:
        result = run_experiment(
            load_experiment_config(config), output_dir, kind=kind, save_models=save_models
        )
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(f"ERROR: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(result["reportability"])
    typer.echo(
        f"protocol={result['protocol']} dataset={result['dataset']} "
        f"n_train={result['n_train']} n_test={result['n_test']}"
    )
    for name, m in result["metrics"].items():
        typer.echo(
            f"  {name}: macro_f1={m['macro_f1']:.4f} micro_f1={m['micro_f1']:.4f} "
            f"mcc={m['mcc']:.4f}"
        )
    typer.echo(f"run directory: {result['run_dir']}")


@app.command("m5-audit")
def m5_audit(
    root: Annotated[Path, typer.Option(help="Local dataset root")] = Path("data"),
) -> None:
    """Print fail-closed M5 inventory; exit 2 while the research campaign is blocked."""
    from driftguard.m5.readiness import inventory

    typer.echo(json.dumps(inventory(root), indent=2))
    raise typer.Exit(code=2)


@app.command("m5-smoke")
def m5_smoke(
    output_dir: Annotated[Path, typer.Option()] = Path("experiments/runs/m5-smoke"),
    explain: Annotated[bool, typer.Option(help="Exercise optional actual TreeSHAP")] = False,
) -> None:
    """Exercise M5 primitives with synthetic data only; never exports portal metrics."""
    from driftguard.m5.smoke import run_smoke

    result = run_smoke(output_dir, explain=explain)
    typer.echo(result["notice"])


@app.command("campaign")
def campaign_cli(
    config: Annotated[Path, typer.Option(exists=True)],
    output_dir: Annotated[Path, typer.Option()],
    research: Annotated[bool, typer.Option()] = False,
) -> None:
    """Run/resume a five-seed campaign; real data must pass admission first."""
    from driftguard.platform.campaign import campaign_from_file

    try:
        result = campaign_from_file(config, output_dir, research=research)
    except (ValueError, OSError) as exc:
        typer.echo(f"BLOCKED: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"{len(result['cells'])} cells; {result['publication_status']}")


if __name__ == "__main__":  # pragma: no cover
    app()
