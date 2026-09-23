"""Explicit local/CI publication of reviewed artifacts; never called by normal CI."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

from driftguard.platform.bundle import prepare_bundle
from driftguard.platform.campaign import write_json
from driftguard.platform.publication import PublicationReview, sanitized_export


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    review = PublicationReview.model_validate_json(args.review.read_text())
    sanitized = sanitized_export(args.run, review)
    if not args.publish:
        print("Review and license gates pass; dry run only")
        return
    with tempfile.TemporaryDirectory() as temp:
        bundle = Path(temp) / "bundle"
        meta = prepare_bundle(args.run, args.model, bundle)
        # Replace private run manifest with a sanitized public manifest before upload.
        write_json(bundle / "manifest.json", sanitized)
        from driftguard.reporting.provenance import sha256_file

        meta["source_manifest_sha256"] = sha256_file(bundle / "manifest.json")
        meta["publication_allowed"] = True
        meta["release_blockers"] = []
        write_json(bundle / "bundle.json", meta)
        (bundle / "README.md").write_text(
            "# DriftGuard-IoT\n\nOwner-reviewed model artifact.\n\n"
            f"Version: `{meta['model_version']}`. Review: {review.approval_reference}.\n\n"
            "See manifest.json for dataset provenance and conditional evaluation metrics.\n"
            "Limitations: offline evaluation; no operational detection guarantee.\n"
        )
        HfApi().upload_folder(
            repo_id="arun-gharami/driftguard-iot",
            folder_path=bundle,
            allow_patterns=["pipeline.joblib", "manifest.json", "bundle.json", "README.md"],
            commit_message=f"Approved model {meta['model_version']}",
        )


if __name__ == "__main__":
    main()
