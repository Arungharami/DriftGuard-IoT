"""Fail-closed dataset inventory. Passing this inventory alone never authorizes a run."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from driftguard.data.loader import find_table_file, read_header
from driftguard.data.registry import load_registry
from driftguard.data.schema import validate_header
from driftguard.reporting.provenance import sha256_file, utc_timestamp


def inventory(root: Path) -> dict[str, Any]:
    datasets = []
    for card in load_registry().values():
        table = card.table()
        blockers = []
        if not card.license.verified or card.license.academic_use != "permitted":
            blockers.append("explicit verified academic-use permission required")
        if table.schema_status != "confirmed":
            blockers.append("schema is not confirmed")
        if table.sha256 is None:
            blockers.append("no registry fingerprint")
        observed_hash = None
        # Do not inspect unlicensed data beyond checking whether a local path exists.
        try:
            path = find_table_file(card.id, table, root)
        except (FileNotFoundError, FileExistsError) as exc:
            blockers.append(str(exc))
        else:
            if card.license.verified and card.license.academic_use == "permitted":
                observed_hash = sha256_file(path)
                if observed_hash != table.sha256:
                    blockers.append("local file fingerprint mismatch")
                else:
                    report = validate_header(read_header(path), table)
                    if not report.ok or not report.order_matches:
                        blockers.append("local header does not match registry")
        datasets.append(
            {
                "dataset": card.id,
                "table": table.id,
                "license": card.license.name,
                "license_source": str(card.license.source_url),
                "license_verified_on": str(card.license.verified_on),
                "expected_sha256": table.sha256,
                "observed_sha256": observed_hash,
                "blockers": blockers,
                "inventory_passed": not blockers,
            }
        )
    return {
        "schema_version": 1,
        "generated_at": utc_timestamp(),
        "campaign_status": "blocked",
        "reportable": False,
        "datasets": datasets,
        "campaign_blockers": [
            "M3 research benchmarks and M4 validated alignment/splits are absent from audited refs",
            "No reviewed cross-dataset semantic contract is implemented",
            "No validated timestamp/session boundaries or attack-family ontology",
            "No real-data campaign runner or reviewed M5 detector/adaptation implementation",
        ],
    }
