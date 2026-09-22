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


if __name__ == "__main__":  # pragma: no cover
    app()
