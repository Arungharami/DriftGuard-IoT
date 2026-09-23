"""Render manuscript tables only from evidence-verified portal entries."""

from __future__ import annotations

import json
from pathlib import Path

from check_public_results import validate


def main() -> None:
    portal = Path("apps/research-portal")
    count = validate(portal)
    index = json.loads((portal / "src/data/results/index.json").read_text())
    lines = ["# Verified research results", ""]
    if count == 0:
        lines += [
            "BLOCKED: no verified public research entries. No result figure is generated.",
            "",
        ]
    else:
        lines += ["| Dataset | Model | Macro-F1 | Manifest |", "| --- | --- | --- | --- |"]
        for entry in index["results"]:
            lines.append(
                f"| {entry['dataset']} | {entry['model']} | "
                f"{entry['metrics']['macro_f1']:.4f} | "
                f"{entry['provenance']['manifest_url']} |"
            )
    Path("paper/generated-results.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
