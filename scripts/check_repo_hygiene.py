"""Block accidental commits of datasets, serialized artifacts, credentials, and large files.

Usage:
    python scripts/check_repo_hygiene.py            # check every git-tracked file
    python scripts/check_repo_hygiene.py FILE...    # check specific files (pre-commit)

Exits non-zero and lists each violation if any file breaks the policy in
SECURITY.md. The policy is deliberately conservative: move a legitimately needed file
to an allowed location (e.g. ``tests/fixtures/``) rather than weakening the rules.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

MAX_FILE_BYTES = 2 * 1024 * 1024

ARCHIVE_SUFFIXES = frozenset({".zip", ".7z", ".rar", ".tar", ".gz", ".tgz", ".bz2", ".xz"})
CAPTURE_SUFFIXES = frozenset({".pcap", ".pcapng", ".cap", ".log"})
DATA_SUFFIXES = frozenset({".csv", ".tsv", ".parquet", ".feather", ".arrow", ".h5", ".hdf5"})
ARTIFACT_SUFFIXES = frozenset(
    {".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".safetensors", ".ckpt", ".npy", ".npz"}
)
CREDENTIAL_NAMES = frozenset({"kaggle.json", ".netrc", "credentials.json", "id_rsa", "id_ed25519"})
CREDENTIAL_SUFFIXES = frozenset({".pem", ".key", ".p12", ".pfx"})

# Small tabular fixtures are allowed only here.
DATA_ALLOWED_PREFIXES: tuple[str, ...] = ("tests/fixtures/",)
ENV_ALLOWED_NAMES = frozenset({".env.example"})


@dataclass(frozen=True)
class Violation:
    path: str
    reason: str


def classify(path: str, size_bytes: int | None = None) -> str | None:
    """Return a violation reason for a repo-relative POSIX path, or None if allowed."""
    p = PurePosixPath(path)
    name = p.name.lower()
    suffix = p.suffix.lower()

    if name.startswith(".env") and name not in ENV_ALLOWED_NAMES:
        return "environment file (may contain secrets)"
    if name in CREDENTIAL_NAMES or suffix in CREDENTIAL_SUFFIXES:
        return "credential or private key file"
    if suffix in ARCHIVE_SUFFIXES:
        return "archive (original dataset archives must not be committed)"
    if suffix in CAPTURE_SUFFIXES:
        return "packet capture or raw log trace"
    if suffix in ARTIFACT_SUFFIXES:
        return "serialized model/array artifact (publish via the approved release path instead)"
    if suffix in DATA_SUFFIXES and not path.startswith(DATA_ALLOWED_PREFIXES):
        return f"tabular data outside {', '.join(DATA_ALLOWED_PREFIXES)}"
    if size_bytes is not None and size_bytes > MAX_FILE_BYTES:
        return f"file larger than {MAX_FILE_BYTES // (1024 * 1024)} MiB"
    return None


def find_violations(paths: Iterable[str], root: Path) -> list[Violation]:
    violations = []
    for raw in paths:
        rel = raw.replace("\\", "/")
        full = root / rel
        size = full.stat().st_size if full.is_file() else None
        reason = classify(rel, size)
        if reason is not None:
            violations.append(Violation(rel, reason))
    return violations


def tracked_files(root: Path) -> list[str]:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git executable not found")
    result = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [git, "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        capture_output=True,
        check=True,
    )
    return [p for p in result.stdout.decode("utf-8").split("\0") if p]


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    paths = argv or tracked_files(root)
    violations = find_violations(paths, root)
    for v in violations:
        print(f"BLOCKED  {v.path}: {v.reason}", file=sys.stderr)
    if violations:
        print(
            f"\n{len(violations)} file(s) violate the repository hygiene policy.", file=sys.stderr
        )
        return 1
    print(f"hygiene OK ({len(paths)} files checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
