"""Optional Kaggle download adapter.

Safety properties:

* Only **approved first-party** Kaggle sources in the registry can be downloaded.
* The caller must explicitly accept the dataset license (``accept_license=True``).
* Before downloading, the live Kaggle license is compared with the license recorded in
  the card. A change aborts the download (license drift).
* Credentials are never read, printed or stored by this module. Their *presence* is
  checked (environment variables or the Kaggle config file), and the official ``kaggle``
  CLI reads them itself.
* Inside the repository, the destination must be under ``data/``, which is git-ignored.
* Downloaded archives are fingerprinted, then extracted with path-traversal protection.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from driftguard.data.fingerprint import FileFingerprint, safe_extract_zip
from driftguard.data.registry import DatasetCard, KaggleSource
from driftguard.reporting.provenance import sha256_file, utc_timestamp

KAGGLE_API = "https://www.kaggle.com/api/v1"
Runner = Callable[..., subprocess.CompletedProcess[str]]
MetadataFetcher = Callable[[str], Mapping[str, Any]]


class KaggleError(RuntimeError):
    pass


class LicenseNotAcceptedError(KaggleError):
    pass


class CredentialsMissingError(KaggleError):
    pass


class LicenseDriftError(KaggleError):
    pass


class AcquisitionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    source: str
    kaggle_slug: str
    kaggle_license_at_download: str
    license_accepted_by_user: bool
    retrieved_at: str
    requested_files: list[str]
    downloaded: list[FileFingerprint]
    extracted: list[FileFingerprint]


def credentials_available(env: Mapping[str, str] | None = None, home: Path | None = None) -> bool:
    """True if Kaggle credentials appear to be configured. Values are never read."""
    env = os.environ if env is None else env
    if env.get("KAGGLE_USERNAME") and env.get("KAGGLE_KEY"):
        return True
    if env.get("KAGGLE_API_TOKEN"):
        return True
    config_dir = Path(env["KAGGLE_CONFIG_DIR"]) if env.get("KAGGLE_CONFIG_DIR") else None
    home = home or Path.home()
    candidates = [p for p in (config_dir, home / ".kaggle", home / ".config" / "kaggle") if p]
    return any((c / "kaggle.json").is_file() or (c / "access_token").is_file() for c in candidates)


def fetch_public_metadata(slug: str) -> Mapping[str, Any]:
    """Public dataset metadata from the Kaggle API (no credentials required)."""
    url = f"{KAGGLE_API}/datasets/view/{slug}"
    with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310 - fixed https URL
        data: Mapping[str, Any] = json.load(response)
    return data


def check_license_drift(
    source: KaggleSource, fetch: MetadataFetcher = fetch_public_metadata
) -> str:
    """Return the live license name, raising ``LicenseDriftError`` if it changed."""
    meta = fetch(source.slug)
    live = str(meta.get("licenseName") or meta.get("licenseNameNullable") or "")
    if live != source.license_name:
        raise LicenseDriftError(
            f"Kaggle license for {source.slug} is now {live!r}, but the registry records "
            f"{source.license_name!r}. Re-review the license and update the dataset card."
        )
    return live


def ensure_safe_destination(dest: Path, repo_root: Path) -> Path:
    dest = dest.resolve()
    repo_root = repo_root.resolve()
    if dest.is_relative_to(repo_root) and not dest.is_relative_to(repo_root / "data"):
        raise KaggleError(
            f"refusing to download into {dest}: inside the repository only data/ is allowed "
            "(it is git-ignored)"
        )
    return dest


def download_kaggle_dataset(
    card: DatasetCard,
    dest: Path,
    *,
    accept_license: bool,
    repo_root: Path,
    files: Sequence[str] | None = None,
    runner: Runner = subprocess.run,
    fetch_metadata: MetadataFetcher = fetch_public_metadata,
    env: Mapping[str, str] | None = None,
    kaggle_executable: str | None = None,
    timeout_s: int = 6 * 3600,
) -> AcquisitionRecord:
    source = card.acquisition.kaggle
    if source is None or not source.approved or not source.first_party:
        raise KaggleError(f"{card.id} has no approved first-party Kaggle source")
    if not accept_license:
        raise LicenseNotAcceptedError(
            f"{card.name} is licensed under: {card.license.name}. "
            f"{card.license.terms_excerpt or ''} Re-run with --accept-license to confirm "
            "you will comply with these terms."
        )
    if not credentials_available(env):
        raise CredentialsMissingError(
            "Kaggle credentials not found. Set KAGGLE_USERNAME and KAGGLE_KEY (or place "
            "kaggle.json in ~/.kaggle/, outside this repository)."
        )
    exe = kaggle_executable or shutil.which("kaggle")
    if exe is None:
        raise KaggleError("kaggle CLI not found; install with `pip install -e .[kaggle]`")

    live_license = check_license_drift(source, fetch_metadata)
    dest = ensure_safe_destination(dest, repo_root)
    dest.mkdir(parents=True, exist_ok=True)

    requested = list(files or [])
    commands = (
        [
            [exe, "datasets", "download", "-d", source.slug, "-f", f, "-p", str(dest), "-q"]
            for f in requested
        ]
        if requested
        else [[exe, "datasets", "download", "-d", source.slug, "-p", str(dest), "-q"]]
    )
    before = {p.resolve() for p in dest.rglob("*") if p.is_file()}
    for cmd in commands:
        result = runner(cmd, capture_output=True, text=True, timeout=timeout_s, check=False)
        if result.returncode != 0:
            # stderr from the CLI does not contain credentials; include a bounded excerpt.
            raise KaggleError(
                f"kaggle download failed ({result.returncode}): {result.stderr[-500:]}"
            )

    new_files = sorted(p for p in dest.rglob("*") if p.is_file() and p.resolve() not in before)
    downloaded = [_fp(p, dest) for p in new_files]
    extracted: list[FileFingerprint] = []
    for archive in (p for p in new_files if p.suffix.lower() == ".zip"):
        for path in safe_extract_zip(archive, dest / "extracted"):
            extracted.append(_fp(path, dest))

    record = AcquisitionRecord(
        dataset_id=card.id,
        source="kaggle",
        kaggle_slug=source.slug,
        kaggle_license_at_download=live_license,
        license_accepted_by_user=True,
        retrieved_at=utc_timestamp(),
        requested_files=requested,
        downloaded=downloaded,
        extracted=extracted,
    )
    (dest / "acquisition.json").write_text(record.model_dump_json(indent=2), encoding="utf-8")
    return record


def _fp(path: Path, root: Path) -> FileFingerprint:
    return FileFingerprint(
        path=path.resolve().relative_to(root.resolve()).as_posix(),
        size_bytes=path.stat().st_size,
        sha256=sha256_file(path),
    )
