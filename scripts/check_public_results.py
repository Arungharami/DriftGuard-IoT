"""Build-time verification of every public result against its sanitized manifest bytes."""

from __future__ import annotations

import json
from pathlib import Path

from driftguard.reporting.provenance import sha256_file


def validate(portal: Path) -> int:
    entries = json.loads((portal / "src/data/results/index.json").read_text())["results"]
    for entry in entries:
        provenance = entry["provenance"]
        url = provenance.get("manifest_url", "")
        digest = provenance.get("manifest_sha256", "")
        if url != f"/manifests/{digest}.json" or len(digest) != 64:
            raise ValueError("every public result requires a content-addressed manifest")
        path = portal / "public" / url.lstrip("/")
        if sha256_file(path) != digest:
            raise ValueError("public manifest integrity failure")
        doc = json.loads(path.read_text())
        if (
            doc["kind"] != "research"
            or doc["synthetic_data"]
            or not doc["review"]["owner_approved"]
        ):
            raise ValueError("non-research or unapproved manifest")
        if doc["run_id"] != provenance["run_id"]:
            raise ValueError("result/manifest identity mismatch")
        for metric, value in entry["metrics"].items():
            if doc["models"][entry["model"]][metric] != value:
                raise ValueError("result/manifest metric mismatch")
    return len(entries)


if __name__ == "__main__":
    print(f"verified {validate(Path('apps/research-portal'))} public research entries")
