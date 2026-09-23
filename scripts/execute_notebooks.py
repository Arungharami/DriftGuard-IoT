"""Local notebook verification; outputs stay in ignored experiments, never the notebook source."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import nbformat
from nbclient import NotebookClient


def main() -> None:
    api: Any = nbformat
    root = Path(__file__).resolve().parents[1]
    for name in ("00_environment_setup", "01_data_validation", "04_drift_detection"):
        path = root / "notebooks" / f"{name}.ipynb"
        nb = api.read(path, as_version=4)
        NotebookClient(
            nb, timeout=180, kernel_name="python3", resources={"metadata": {"path": str(root)}}
        ).execute()
        print(f"{name}: executed locally")


if __name__ == "__main__":
    main()
