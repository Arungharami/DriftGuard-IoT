"""Generate thin notebooks without execution outputs or data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import nbformat

from driftguard.platform.notebook_steps import STEPS

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "integration/platform-completion"
notebook_api: Any = nbformat


def main() -> None:
    links = [
        "# Google Colab notebooks",
        "",
        "Synthetic defaults; remote execution not claimed.",
        "",
    ]
    for i, step in enumerate(STEPS):
        name = f"{i:02d}_{step}.ipynb"
        url = f"https://colab.research.google.com/github/Arungharami/DriftGuard-IoT/blob/{BRANCH}/notebooks/{name}"
        nb = notebook_api.v4.new_notebook()
        nb.metadata["kernelspec"] = {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        }
        nb.cells = [
            notebook_api.v4.new_markdown_cell(
                f"# {i:02d} · {step.replace('_', ' ').title()}\n\n[Open in Colab]({url})\n\n"
                "**Synthetic software validation only.** No real dataset, token, "
                "or private trace is embedded. "
                "CPU is supported; the current tree pipelines do not require or c"
                "laim GPU acceleration.\n\n"
                "Run 00 setup first, or run the bootstrap cell below. For repeata"
                "bility replace REF with a "
                "reviewed commit SHA. Real data stays in private runtime storage."
                " Optional Drive mounting "
                "requires your Google authorization; never share notebooks contai"
                "ning private outputs."
            ),
            notebook_api.v4.new_code_cell(
                "from pathlib import Path\nimport subprocess, sys\n"
                f"REF = {BRANCH!r}  # pin a reviewed commit for research\n"
                "ROOT = Path.cwd()\n"
                "if not (ROOT / 'pyproject.toml').exists():\n"
                "    ROOT = Path('/content/DriftGuard-IoT')\n"
                "    if not ROOT.exists():\n"
                "        subprocess.run(['git', 'clone', 'https://github.com/Arun"
                "gharami/DriftGuard-IoT', str(ROOT)], check=True)\n"
                "        subprocess.run(['git', '-C', str(ROOT), 'checkout', REF], check=True)\n"
                "    subprocess.run([sys.executable, '-m', 'pip', 'install', '-e'"
                ", str(ROOT) + '[dev,explain,platform,notebooks]', '-c', str(ROOT"
                " / 'requirements/constraints-py311.txt')], check=True)\n"
                "# Existing checkouts are never reset or overwritten. Verify HEAD"
                " before a real run.\n"
                "OUTPUT = ROOT / 'experiments' / 'notebook-runs'\n"
                "# A private persistent Drive path may replace OUTPUT after your authorization."
            ),
            notebook_api.v4.new_code_cell(
                "from driftguard.platform.notebook_steps import run_step\n"
                f"result = run_step({step!r}, ROOT, output=OUTPUT)\nresult"
            ),
            notebook_api.v4.new_markdown_cell(
                "## Real campaign and recovery\n\n"
                "Use the package `campaign` CLI with a reviewed full-data config "
                "and explicit `--research`. "
                "Dataset admission must pass first. Per-model/per-seed checkpoint"
                "s verify code, config and "
                "file fingerprints; interrupted cells rerun, completed cells resu"
                "me. Bound `n_jobs`, tree "
                "counts, file size and campaign cell budget before starting; the "
                "full source table must fit RAM. "
                "Do not tune on target test labels. See `docs/platform-operations.md`.\n\n"
                "This notebook is not proof of a Colab-hosted run. Record runtime"
                ", commit, packages and "
                "output fingerprints for every authorized remote execution."
            ),
        ]
        notebook_api.write(nb, ROOT / "notebooks" / name)
        links.append(f"- [{name}]({url})")
    (ROOT / "notebooks/README.md").write_text("\n".join(links) + "\n")


if __name__ == "__main__":
    main()
