"""``driftguard data ...`` commands: registry, acquisition, fingerprints, quality, subsets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from driftguard.data.catalog_export import catalog_json
from driftguard.data.registry import DatasetCard, TableSpec, get_dataset, load_registry

data_app = typer.Typer(help="Dataset registry, acquisition, provenance and quality.")

DatasetArg = Annotated[str, typer.Argument(help="Dataset id, e.g. ton_iot")]
TableOpt = Annotated[str | None, typer.Option(help="Table id (defaults to the card's default)")]
FileOpt = Annotated[
    Path | None, typer.Option(help="Explicit CSV path (defaults to searching data/raw/<id>/)")
]
NRowsOpt = Annotated[int | None, typer.Option(min=1, help="Read at most N rows (dev runs)")]
DEFAULT_PORTAL_CATALOG = Path("apps/research-portal/src/data/datasets.json")


def _card(dataset_id: str) -> DatasetCard:
    try:
        return get_dataset(dataset_id)
    except KeyError as exc:
        typer.echo(str(exc.args[0]), err=True)
        raise typer.Exit(code=2) from exc


def _repo_root() -> Path:
    here = Path.cwd().resolve()
    for candidate in (here, *here.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / ".git").exists():
            return candidate
    return here


def _resolve_file(card: DatasetCard, table: TableSpec, file: Path | None) -> Path:
    from driftguard.data.loader import find_table_file

    if file is not None:
        return file
    try:
        return find_table_file(card.id, table)
    except (FileNotFoundError, FileExistsError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@data_app.command("list")
def list_datasets() -> None:
    """List registered datasets with license and schema status."""
    for card in load_registry().values():
        lic = card.license
        verified = f"verified {lic.verified_on}" if lic.verified else "license NOT verified"
        schemas = ", ".join(f"{t.id}:{t.schema_status}" for t in card.tables)
        typer.echo(
            f"{card.id:<16} {card.name:<16} {card.acquisition.method:<7} {verified}; {schemas}"
        )


@data_app.command()
def show(dataset_id: DatasetArg) -> None:
    """Show provenance, license terms, citations and acquisition instructions."""
    from driftguard.data.licensing import license_summary

    card = _card(dataset_id)
    typer.echo(f"{card.name} ({card.id}) - {card.publisher}\n{card.homepage}\n")
    typer.echo(license_summary(card))
    if card.license.terms_excerpt:
        typer.echo(f'\nTerms (verbatim excerpt): "{card.license.terms_excerpt}"')
    if card.license.notes:
        typer.echo(f"Notes: {card.license.notes}")
    typer.echo("\nRequired citations:")
    for i, c in enumerate(card.citations, 1):
        typer.echo(f"  [{i}] {c.text}" + (f" doi:{c.doi}" if c.doi else ""))
    typer.echo(f"\nAcquisition ({card.acquisition.method}): {card.acquisition.instructions}")
    if card.acquisition.unapproved_mirrors:
        typer.echo(f"Mirrors: {card.acquisition.unapproved_mirrors}")
    for t in card.tables:
        typer.echo(
            f"\nTable {t.id}: {t.filename} | schema {t.schema_status} | {len(t.columns)} columns, "
            f"{len(t.feature_columns)} candidate features | label={t.label_column} "
            f"attack_type={t.attack_type_column} timestamp={t.timestamp_column} | "
            f"sha256={'recorded' if t.sha256 else 'not recorded'}"
        )


@data_app.command("check-license")
def check_license(dataset_id: DatasetArg) -> None:
    """Compare the live Kaggle license with the registry (Kaggle sources only)."""
    from driftguard.data.kaggle import LicenseDriftError, check_license_drift

    card = _card(dataset_id)
    if card.acquisition.kaggle is None:
        typer.echo(
            f"{card.id} has no Kaggle source; re-check {card.license.source_url} manually "
            f"(last verified {card.license.verified_on})."
        )
        return
    try:
        live = check_license_drift(card.acquisition.kaggle)
    except LicenseDriftError as exc:
        typer.echo(f"LICENSE DRIFT: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"OK: Kaggle license for {card.acquisition.kaggle.slug} is still {live!r}")


@data_app.command()
def download(
    dataset_id: DatasetArg,
    accept_license: Annotated[
        bool, typer.Option("--accept-license", help="Confirm you will comply with the license")
    ] = False,
    dest: Annotated[Path | None, typer.Option(help="Destination (default data/raw/<id>)")] = None,
    file: Annotated[
        list[str] | None, typer.Option(help="Specific file(s) within the dataset")
    ] = None,
    all_files: Annotated[bool, typer.Option(help="Download the complete dataset")] = False,
) -> None:
    """Download an approved first-party Kaggle dataset with your own credentials."""
    from driftguard.data.kaggle import KaggleError, download_kaggle_dataset
    from driftguard.data.loader import raw_dir

    card = _card(dataset_id)
    if card.acquisition.method != "kaggle":
        typer.echo(f"{card.id} is acquired manually: {card.acquisition.instructions}", err=True)
        raise typer.Exit(code=2)
    files = list(file or [])
    if not files and not all_files:
        files = [t.relative_path or t.filename for t in [card.table()]]
    try:
        record = download_kaggle_dataset(
            card,
            dest or raw_dir(card.id),
            accept_license=accept_license,
            repo_root=_repo_root(),
            files=files,
        )
    except KaggleError as exc:
        typer.echo(f"ERROR: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"downloaded {len(record.downloaded)} file(s), extracted {len(record.extracted)}")
    typer.echo("next: driftguard data fingerprint " + card.id)


@data_app.command()
def fingerprint(
    dataset_id: DatasetArg,
    extract: Annotated[bool, typer.Option(help="Safely extract .zip archives first")] = True,
) -> None:
    """Fingerprint every file under data/raw/<id>/ and verify against the card."""
    from driftguard.data.fingerprint import (
        fingerprint_directory,
        safe_extract_zip,
        verify_against_card,
    )
    from driftguard.data.loader import data_root, raw_dir

    card = _card(dataset_id)
    base = raw_dir(card.id)
    if not base.is_dir():
        typer.echo(f"{base} does not exist. {card.acquisition.instructions}", err=True)
        raise typer.Exit(code=1)
    if extract:
        for archive in sorted(p for p in base.glob("*.zip")):
            target = base / "extracted" / archive.stem
            if not target.exists():
                safe_extract_zip(archive, target)
                typer.echo(f"extracted {archive.name} -> {target}")
    manifest = fingerprint_directory(card.id, base)
    out = data_root() / "manifests" / f"{card.id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"fingerprinted {len(manifest.files)} file(s) -> {out}")
    for v in verify_against_card(manifest, card):
        typer.echo(f"  {v.table_id}: {v.status} ({v.detail}) {v.observed_sha256 or ''}")


@data_app.command()
def validate(
    dataset_id: DatasetArg, table: TableOpt = None, file: FileOpt = None, nrows: NRowsOpt = 10_000
) -> None:
    """Validate a local file's header and value types against the registry schema."""
    from driftguard.data.loader import read_table
    from driftguard.data.schema import validate_frame

    card = _card(dataset_id)
    spec = card.table(table)
    path = _resolve_file(card, spec, file)
    report = validate_frame(read_table(path, spec, nrows=nrows), spec)
    typer.echo(report.model_dump_json(indent=2))
    raise typer.Exit(code=0 if report.ok else 1)


@data_app.command()
def quality(
    dataset_id: DatasetArg,
    table: TableOpt = None,
    file: FileOpt = None,
    nrows: NRowsOpt = None,
    out_dir: Annotated[Path, typer.Option(help="Report directory")] = Path("data/reports"),
) -> None:
    """Write a data-quality report (JSON + Markdown) for a local table."""
    from driftguard.data.loader import read_table
    from driftguard.data.quality import quality_report, render_markdown

    card = _card(dataset_id)
    spec = card.table(table)
    path = _resolve_file(card, spec, file)
    report = quality_report(read_table(path, spec, nrows=nrows), spec, card.id, nrows)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = out_dir / f"{card.id}__{spec.id}"
    stem.with_suffix(".json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
    stem.with_suffix(".md").write_text(render_markdown(report), encoding="utf-8")
    typer.echo(f"wrote {stem}.json and {stem}.md ({report.n_rows:,} rows)")


@data_app.command()
def sample(
    dataset_id: DatasetArg,
    n: Annotated[int, typer.Option(min=1, help="Subset size")],
    seed: Annotated[int, typer.Option(min=0)] = 0,
    table: TableOpt = None,
    file: FileOpt = None,
    stratify: Annotated[bool, typer.Option(help="Stratify by the label column")] = True,
    min_per_class: Annotated[int, typer.Option(min=0)] = 1,
) -> None:
    """Write a deterministic development subset to data/subsets/<id>/<subset_id>/."""
    from driftguard.data.loader import data_root, read_table
    from driftguard.data.sampling import SubsetSpec, deterministic_sample
    from driftguard.reporting.provenance import sha256_file, utc_timestamp

    card = _card(dataset_id)
    spec = card.table(table)
    path = _resolve_file(card, spec, file)
    source_sha = sha256_file(path)
    subset_spec = SubsetSpec(
        n=n,
        seed=seed,
        stratify_column=spec.label_column if stratify else None,
        min_per_class=min_per_class,
    )
    subset = deterministic_sample(read_table(path, spec), subset_spec)
    subset_id = subset_spec.subset_id(source_sha)
    out = data_root() / "subsets" / card.id / subset_id
    out.mkdir(parents=True, exist_ok=True)
    subset.to_csv(out / "subset.csv", index=False)
    manifest = {
        "dataset_id": card.id,
        "table_id": spec.id,
        "subset_id": subset_id,
        "created_at": utc_timestamp(),
        "source_file": path.name,
        "source_sha256": source_sha,
        "spec": subset_spec.model_dump(),
        "n_rows": len(subset),
        "label_counts": {
            str(k): int(v) for k, v in subset[spec.label_column].value_counts().items()
        },
        "subset_sha256": sha256_file(out / "subset.csv"),
        "notice": "Development subset only; research runs use full tables.",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    typer.echo(f"wrote {len(subset):,} rows -> {out}")


@data_app.command("export-catalog")
def export_catalog(
    out: Annotated[Path, typer.Option(help="Output JSON")] = DEFAULT_PORTAL_CATALOG,
    check: Annotated[bool, typer.Option(help="Fail if the file is out of date")] = False,
) -> None:
    """Export registry metadata (no data) for the research portal."""
    text = catalog_json()
    if check:
        current = out.read_text(encoding="utf-8") if out.is_file() else ""
        if current != text:
            typer.echo(f"{out} is out of date; run `driftguard data export-catalog`", err=True)
            raise typer.Exit(code=1)
        typer.echo(f"{out} is up to date")
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    typer.echo(f"wrote {out}")
