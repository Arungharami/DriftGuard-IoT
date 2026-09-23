from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from driftguard.cli import app
from driftguard.data.catalog_export import build_catalog, catalog_json
from driftguard.data.fixtures import synthesize_table
from driftguard.data.registry import get_dataset, load_registry

runner = CliRunner()
REPO = Path(__file__).resolve().parents[2]
PORTAL_CATALOG = REPO / "apps/research-portal/src/data/datasets.json"


@pytest.fixture
def data_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("DRIFTGUARD_DATA_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def wustl_csv(data_root: Path) -> Path:
    table = get_dataset("wustl_iiot_2021").table()
    target = data_root / "raw" / "wustl_iiot_2021" / "nested"
    target.mkdir(parents=True)
    path = target / table.filename
    synthesize_table(table, n=400, seed=5).to_csv(path, index=False)
    return path


def test_list_and_show() -> None:
    listed = runner.invoke(app, ["data", "list"])
    assert listed.exit_code == 0
    for dataset_id in load_registry():
        assert dataset_id in listed.stdout
    shown = runner.invoke(app, ["data", "show", "ton_iot"])
    assert shown.exit_code == 0
    assert "Free use of the TON_IoT datasets for academic research" in shown.stdout
    assert runner.invoke(app, ["data", "show", "nope"]).exit_code == 2


def test_validate_finds_file_under_raw_dir(wustl_csv: Path) -> None:
    result = runner.invoke(app, ["data", "validate", "wustl_iiot_2021"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["errors"] == []


def test_validate_reports_schema_errors(tmp_path: Path) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("a,b\n1,2\n", encoding="utf-8")
    result = runner.invoke(app, ["data", "validate", "wustl_iiot_2021", "--file", str(bad)])
    assert result.exit_code == 1


def test_missing_file_gives_instructions(data_root: Path) -> None:
    result = runner.invoke(app, ["data", "validate", "ton_iot"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_quality_writes_json_and_markdown(wustl_csv: Path, tmp_path: Path) -> None:
    out = tmp_path / "reports"
    result = runner.invoke(app, ["data", "quality", "wustl_iiot_2021", "--out-dir", str(out)])
    assert result.exit_code == 0, result.output
    report = json.loads((out / "wustl_iiot_2021__wustl_iiot_2021.json").read_text(encoding="utf-8"))
    assert report["n_rows"] == 400
    assert (out / "wustl_iiot_2021__wustl_iiot_2021.md").is_file()


def test_sample_writes_subset_and_manifest(wustl_csv: Path, data_root: Path) -> None:
    args = ["data", "sample", "wustl_iiot_2021", "--n", "50", "--seed", "3"]
    first = runner.invoke(app, args)
    second = runner.invoke(app, args)
    assert first.exit_code == 0, first.output
    manifests = list((data_root / "subsets" / "wustl_iiot_2021").glob("*/manifest.json"))
    assert len(manifests) == 1  # identical spec -> identical subset id
    manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert manifest["n_rows"] == 50
    assert sum(manifest["label_counts"].values()) == 50
    assert second.exit_code == 0


def test_fingerprint_extracts_archives_and_writes_manifest(data_root: Path) -> None:
    raw = data_root / "raw" / "wustl_iiot_2021"
    raw.mkdir(parents=True)
    with zipfile.ZipFile(raw / "wustl_iiot_2021.zip", "w") as zf:
        zf.writestr("wustl_iiot_2021.csv", "a,b\n1,2\n")
    result = runner.invoke(app, ["data", "fingerprint", "wustl_iiot_2021"])
    assert result.exit_code == 0, result.output
    # The card records the official file's SHA-256 (M2), so a stand-in file must mismatch.
    assert "mismatch" in result.stdout
    manifest = json.loads(
        (data_root / "manifests" / "wustl_iiot_2021.json").read_text(encoding="utf-8")
    )
    assert {f["path"] for f in manifest["files"]} == {
        "wustl_iiot_2021.zip",
        "extracted/wustl_iiot_2021/wustl_iiot_2021.csv",
    }


def test_download_guards() -> None:
    manual = runner.invoke(app, ["data", "download", "ton_iot"])
    assert manual.exit_code == 2
    unaccepted = runner.invoke(app, ["data", "download", "edge_iiotset"])
    assert unaccepted.exit_code == 1
    assert "--accept-license" in unaccepted.output


def test_portal_catalog_is_in_sync_with_registry() -> None:
    assert PORTAL_CATALOG.read_text(encoding="utf-8") == catalog_json(), (
        "run `driftguard data export-catalog`"
    )


def test_catalog_exposes_no_column_names_or_data() -> None:
    text = json.dumps(build_catalog())
    for card in load_registry().values():
        for table in card.tables:
            for name in table.private_columns:
                assert f'"{name}"' not in text
