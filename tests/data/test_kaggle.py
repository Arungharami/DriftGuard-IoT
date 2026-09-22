"""Kaggle adapter tests. No network access and no real Kaggle CLI: both are injected."""

from __future__ import annotations

import json
import subprocess
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from driftguard.data.kaggle import (
    CredentialsMissingError,
    KaggleError,
    LicenseDriftError,
    LicenseNotAcceptedError,
    credentials_available,
    download_kaggle_dataset,
    ensure_safe_destination,
)
from driftguard.data.registry import DatasetCard, get_dataset

FAKE_ENV = {"KAGGLE_USERNAME": "user", "KAGGLE_KEY": "not-a-real-key"}


def _meta(license_name: str = "CC BY-NC-SA 4.0"):  # type: ignore[no-untyped-def]
    def fetch(slug: str) -> Mapping[str, Any]:
        return {"ref": slug, "licenseName": license_name}

    return fetch


class FakeKaggleCLI:
    """Records argv and writes a small zip into the -p destination, like the real CLI."""

    def __init__(self, returncode: int = 0) -> None:
        self.calls: list[list[str]] = []
        self.returncode = returncode

    def __call__(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert isinstance(cmd, list), "argv must be a list (no shell)"
        assert "shell" not in kwargs
        self.calls.append(cmd)
        dest = Path(cmd[cmd.index("-p") + 1])
        with zipfile.ZipFile(dest / "ML-EdgeIIoT-dataset.csv.zip", "w") as zf:
            zf.writestr("ML-EdgeIIoT-dataset.csv", "a,b\n1,2\n")
        return subprocess.CompletedProcess(
            cmd, self.returncode, "", "boom" if self.returncode else ""
        )


@pytest.fixture
def edge() -> DatasetCard:
    return get_dataset("edge_iiotset")


def _download(edge: DatasetCard, tmp_path: Path, **kw: Any):  # type: ignore[no-untyped-def]
    params: dict[str, Any] = {
        "accept_license": True,
        "repo_root": tmp_path / "repo",
        "runner": FakeKaggleCLI(),
        "fetch_metadata": _meta(),
        "env": FAKE_ENV,
        "kaggle_executable": "kaggle",
        "files": ["Edge-IIoTset dataset/Selected dataset for ML and DL/ML-EdgeIIoT-dataset.csv"],
    }
    params.update(kw)
    return download_kaggle_dataset(edge, tmp_path / "repo" / "data" / "raw" / "edge", **params)


def test_credentials_detection(tmp_path: Path) -> None:
    assert credentials_available(FAKE_ENV, home=tmp_path)
    assert credentials_available({"KAGGLE_API_TOKEN": "x"}, home=tmp_path)
    assert not credentials_available({}, home=tmp_path)
    (tmp_path / ".kaggle").mkdir()
    (tmp_path / ".kaggle" / "kaggle.json").write_text("{}", encoding="utf-8")
    assert credentials_available({}, home=tmp_path)


def test_successful_download_records_provenance(edge: DatasetCard, tmp_path: Path) -> None:
    runner = FakeKaggleCLI()
    record = _download(edge, tmp_path, runner=runner)
    assert record.kaggle_license_at_download == "CC BY-NC-SA 4.0"
    assert record.license_accepted_by_user
    assert [f.path for f in record.downloaded] == ["ML-EdgeIIoT-dataset.csv.zip"]
    assert [f.path for f in record.extracted] == ["extracted/ML-EdgeIIoT-dataset.csv"]
    dest = tmp_path / "repo" / "data" / "raw" / "edge"
    saved = json.loads((dest / "acquisition.json").read_text(encoding="utf-8"))
    assert saved["kaggle_slug"] == edge.acquisition.kaggle.slug  # type: ignore[union-attr]
    cmd = runner.calls[0]
    assert cmd[:4] == ["kaggle", "datasets", "download", "-d"]
    assert "-f" in cmd
    # Credentials never appear in argv or in the provenance record.
    joined = " ".join(cmd) + json.dumps(saved)
    assert "not-a-real-key" not in joined


def test_license_must_be_accepted(edge: DatasetCard, tmp_path: Path) -> None:
    with pytest.raises(LicenseNotAcceptedError, match="CC BY-NC-SA"):
        _download(edge, tmp_path, accept_license=False)


def test_missing_credentials(
    edge: DatasetCard, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    with pytest.raises(CredentialsMissingError):
        _download(edge, tmp_path, env={})


def test_license_drift_aborts_before_download(edge: DatasetCard, tmp_path: Path) -> None:
    runner = FakeKaggleCLI()
    with pytest.raises(LicenseDriftError, match="MIT"):
        _download(edge, tmp_path, runner=runner, fetch_metadata=_meta("MIT"))
    assert runner.calls == []


def test_manual_datasets_cannot_use_kaggle(tmp_path: Path) -> None:
    with pytest.raises(KaggleError, match="no approved"):
        _download(get_dataset("ton_iot"), tmp_path)


def test_cli_failure_is_reported(edge: DatasetCard, tmp_path: Path) -> None:
    with pytest.raises(KaggleError, match="failed"):
        _download(edge, tmp_path, runner=FakeKaggleCLI(returncode=1))


def test_destination_must_be_under_data_inside_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    assert ensure_safe_destination(repo / "data" / "raw" / "x", repo)
    assert ensure_safe_destination(tmp_path / "elsewhere", repo)  # outside the repo is fine
    with pytest.raises(KaggleError, match="only data/"):
        ensure_safe_destination(repo / "src", repo)
