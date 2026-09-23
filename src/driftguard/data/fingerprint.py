"""SHA-256 fingerprints of acquired files, safe archive extraction and verification.

A ``FingerprintManifest`` lists every file under a dataset's raw directory with its size
and SHA-256. It is written next to the data (``data/manifests/<id>.json``, git-ignored)
and compared against any fingerprints recorded in the dataset card. The card's
``sha256`` fields are filled in by a reviewed PR once the team has agreed on the
canonical file. They are never guessed.
"""

from __future__ import annotations

import zipfile
from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict

from driftguard.data.registry import DatasetCard
from driftguard.reporting.provenance import environment_snapshot, sha256_file, utc_timestamp

MAX_EXTRACTED_BYTES = 40 * 1024**3  # 40 GiB guard against decompression bombs
MAX_COMPRESSION_RATIO = 200


class FileFingerprint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str  # POSIX path relative to the dataset's raw directory
    size_bytes: int
    sha256: str


class FingerprintManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    created_at: str
    files: list[FileFingerprint]
    environment: dict[str, object]

    def by_name(self) -> dict[str, list[FileFingerprint]]:
        out: dict[str, list[FileFingerprint]] = {}
        for f in self.files:
            out.setdefault(PurePosixPath(f.path).name, []).append(f)
        return out


TableStatus = Literal["match", "mismatch", "unrecorded", "absent"]


class TableVerification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    table_id: str
    status: TableStatus
    observed_sha256: str | None
    recorded_sha256: str | None
    detail: str


def fingerprint_directory(dataset_id: str, directory: Path) -> FingerprintManifest:
    files = []
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        rel = path.relative_to(directory).as_posix()
        files.append(
            FileFingerprint(path=rel, size_bytes=path.stat().st_size, sha256=sha256_file(path))
        )
    return FingerprintManifest(
        dataset_id=dataset_id,
        created_at=utc_timestamp(),
        files=files,
        environment=environment_snapshot(),
    )


def verify_against_card(
    manifest: FingerprintManifest, card: DatasetCard
) -> list[TableVerification]:
    by_name = manifest.by_name()
    results = []
    for table in card.tables:
        found = by_name.get(table.filename, [])
        observed = found[0].sha256 if len(found) == 1 else None
        if not found:
            status: TableStatus = "absent"
            detail = f"{table.filename} not present"
        elif len(found) > 1:
            status, detail = "mismatch", f"{len(found)} files named {table.filename}"
        elif table.sha256 is None:
            status, detail = "unrecorded", "no reference fingerprint recorded in the card yet"
        elif observed == table.sha256:
            status, detail = "match", "fingerprint matches the card"
        else:
            status, detail = "mismatch", "fingerprint differs from the card"
        if found and table.size_bytes is not None and found[0].size_bytes != table.size_bytes:
            status = "mismatch"
            detail += f"; size {found[0].size_bytes} != recorded {table.size_bytes}"
        results.append(
            TableVerification(
                table_id=table.id,
                status=status,
                observed_sha256=observed,
                recorded_sha256=table.sha256,
                detail=detail,
            )
        )
    return results


class UnsafeArchiveError(ValueError):
    pass


def safe_extract_zip(archive: Path, destination: Path) -> list[Path]:
    """Extract ``archive`` into ``destination``, rejecting path traversal, absolute paths,
    symlinks and implausible decompression ratios. Returns the extracted file paths."""
    destination = destination.resolve()
    extracted: list[Path] = []
    with zipfile.ZipFile(archive) as zf:
        infos = zf.infolist()
        total = sum(i.file_size for i in infos)
        compressed = max(1, sum(i.compress_size for i in infos))
        if total > MAX_EXTRACTED_BYTES or total / compressed > MAX_COMPRESSION_RATIO:
            raise UnsafeArchiveError(f"{archive.name}: implausible extracted size {total}")
        for info in infos:
            name = info.filename
            if name.startswith(("/", "\\")) or ":" in PurePosixPath(name).parts[0]:
                raise UnsafeArchiveError(f"absolute path in archive: {name!r}")
            target = (destination / name).resolve()
            if not target.is_relative_to(destination):
                raise UnsafeArchiveError(f"path traversal in archive: {name!r}")
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise UnsafeArchiveError(f"symlink in archive: {name!r}")
        for info in infos:
            zf.extract(info, destination)
            if not info.is_dir():
                extracted.append((destination / info.filename).resolve())
    return extracted
