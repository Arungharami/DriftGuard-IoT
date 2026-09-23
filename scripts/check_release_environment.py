"""Fail closed unless a named GitHub Environment actually requires human review."""

from __future__ import annotations

import json
import os
import sys
import urllib.request


def main() -> None:
    environment = sys.argv[1]
    if environment not in {"model-release", "production", "preview", "research"}:
        raise ValueError("unknown protected environment")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if repo != "Arungharami/DriftGuard-IoT":
        raise ValueError("release repository mismatch")
    token = os.environ["GH_TOKEN"]
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/environments/{environment}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:  # noqa: S310 - fixed GitHub URL
        data = json.load(response)
    rules = data.get("protection_rules", [])
    if not any(
        rule.get("type") == "required_reviewers" and rule.get("reviewers") for rule in rules
    ):
        raise ValueError("environment has no required reviewers; release refused")
    print(f"{environment}: required reviewers configured")


if __name__ == "__main__":
    main()
