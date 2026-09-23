"""Validate notebook hygiene, required manuscript sections and public evidence links."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from check_public_results import validate


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    notebooks = sorted((root / "notebooks").glob("*.ipynb"))
    if len(notebooks) != 10:
        raise ValueError("ten workflow notebooks required")
    for path in notebooks:
        nb = json.loads(path.read_text())
        for cell in nb["cells"]:
            if cell["cell_type"] == "code":
                if cell["outputs"] or cell["execution_count"] is not None:
                    raise ValueError("public notebooks must not contain execution outputs")
                ast.parse("".join(cell["source"]))
        if (
            "run_step" not in path.read_text()
            or "colab.research.google.com" not in path.read_text()
        ):
            raise ValueError("notebook lacks package call or Colab link")
    manuscript = (root / "paper/manuscript.md").read_text()
    for section in (
        "Abstract",
        "Introduction",
        "Related Work",
        "Research Gap",
        "Proposed DriftGuard",
        "Datasets and Experimental",
        "Evaluation Protocol",
        "Results",
        "Cross-Domain",
        "Drift and Adaptation",
        "Explainability",
        "Resource Efficiency",
        "Ablation",
        "Threats to Validity",
        "Limitations",
        "Conclusion",
        "References",
    ):
        if section not in manuscript:
            raise ValueError(f"missing manuscript section: {section}")
    count = validate(root / "apps/research-portal")
    print(f"10 clean notebooks, manuscript structure and {count} public result manifests validated")


if __name__ == "__main__":
    main()
