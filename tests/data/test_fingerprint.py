from __future__ import annotations

import hashlib
import stat
import zipfile
from pathlib import Path

import pytest

from driftguard.data.fingerprint import (
    UnsafeArchiveError,
    fingerprint_directory,
    safe_extract_zip,
    verify_against_card,
)
from driftguard.data.registry import get_dataset


def _card_with(sha: str | None, size: int | None = None):  # type: ignore[no-untyped-def]
    card = get_dataset("wustl_iiot_2021")
    table = card.table().model_copy(update={"sha256": sha, "size_bytes": size})
    return card.model_copy(update={"tables": [table]})


def test_fingerprint_directory_lists_files_with_hashes(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "wustl_iiot_2021.csv").write_bytes(b"a,b\n1,2\n")
    (tmp_path / "notes.txt").write_text("x", encoding="utf-8")
    manifest = fingerprint_directory("wustl_iiot_2021", tmp_path)
    paths = [f.path for f in manifest.files]
    assert paths == ["notes.txt", "sub/wustl_iiot_2021.csv"]
    assert manifest.files[1].sha256 == hashlib.sha256(b"a,b\n1,2\n").hexdigest()


def test_verification_statuses(tmp_path: Path) -> None:
    content = b"x,y\n"
    digest = hashlib.sha256(content).hexdigest()
    empty = fingerprint_directory("wustl_iiot_2021", tmp_path)
    assert verify_against_card(empty, _card_with(None))[0].status == "absent"

    (tmp_path / "wustl_iiot_2021.csv").write_bytes(content)
    manifest = fingerprint_directory("wustl_iiot_2021", tmp_path)
    assert verify_against_card(manifest, _card_with(None))[0].status == "unrecorded"
    assert verify_against_card(manifest, _card_with(digest))[0].status == "match"
    assert verify_against_card(manifest, _card_with("0" * 64))[0].status == "mismatch"
    sized = verify_against_card(manifest, _card_with(digest, size=999))[0]
    assert sized.status == "mismatch" and "size" in sized.detail


def _zip(path: Path, entries: dict[str, bytes], symlink: str | None = None) -> Path:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
        if symlink:
            info = zipfile.ZipInfo(symlink)
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            zf.writestr(info, "/etc/passwd")
    return path


def test_safe_extract_happy_path(tmp_path: Path) -> None:
    archive = _zip(tmp_path / "ok.zip", {"dir/a.csv": b"1,2\n", "b.txt": b"hi"})
    out = safe_extract_zip(archive, tmp_path / "out")
    assert sorted(p.name for p in out) == ["a.csv", "b.txt"]
    assert (tmp_path / "out" / "dir" / "a.csv").read_bytes() == b"1,2\n"


@pytest.mark.parametrize(
    "name", ["../escape.txt", "dir/../../escape.txt", "/abs.txt", "C:/win.txt"]
)
def test_safe_extract_rejects_traversal(tmp_path: Path, name: str) -> None:
    archive = _zip(tmp_path / "bad.zip", {name: b"x"})
    with pytest.raises(UnsafeArchiveError):
        safe_extract_zip(archive, tmp_path / "out")
    assert not (tmp_path / "escape.txt").exists()


def test_safe_extract_rejects_symlinks(tmp_path: Path) -> None:
    archive = _zip(tmp_path / "link.zip", {"a.txt": b"x"}, symlink="link")
    with pytest.raises(UnsafeArchiveError, match="symlink"):
        safe_extract_zip(archive, tmp_path / "out")


def test_safe_extract_rejects_decompression_bombs(tmp_path: Path) -> None:
    archive = _zip(tmp_path / "bomb.zip", {"zeros.bin": b"\0" * 5_000_000})
    with pytest.raises(UnsafeArchiveError, match="implausible"):
        safe_extract_zip(archive, tmp_path / "out")
