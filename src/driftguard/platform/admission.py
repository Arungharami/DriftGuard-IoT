"""Verify local source files before research; never infer licenses from downloadability."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from driftguard.config import DatasetConfig
from driftguard.data.loader import find_table_file, read_table
from driftguard.data.quality import quality_report
from driftguard.data.registry import get_dataset
from driftguard.data.schema import validate_frame
from driftguard.reporting.provenance import sha256_file


class AdmissionBlockedError(ValueError):
    """A scientific or licensing prerequisite is missing."""


def admit_dataset(config: DatasetConfig, root: Path | None = None) -> dict[str, Any]:
    if not config.is_registry:
        return {"synthetic": True, "reportable": False, "status": "fixture"}
    card = get_dataset(config.kind)
    table = card.table(config.table)
    if not card.license.verified or card.license.academic_use != "permitted":
        raise AdmissionBlockedError(
            f"{card.id}: verified explicit academic-use permission required"
        )
    if table.schema_status != "confirmed" or not table.sha256:
        raise AdmissionBlockedError(
            f"{card.id}: confirmed schema and registry fingerprint required"
        )
    path = find_table_file(card.id, table, root)
    digest = sha256_file(path)
    if digest != table.sha256:
        raise AdmissionBlockedError(f"{card.id}: source SHA-256 mismatch")
    frame = read_table(path, table)
    schema = validate_frame(frame, table)
    if not schema.ok or not schema.order_matches or schema.type_violations:
        raise AdmissionBlockedError(f"{card.id}: actual schema/value validation failed")
    if table.n_rows is not None and len(frame) != table.n_rows:
        raise AdmissionBlockedError(f"{card.id}: registry row count mismatch")
    if frame[table.label_column].isna().any():
        raise AdmissionBlockedError(f"{card.id}: missing labels")
    quality = quality_report(frame, table, card.id)
    if quality.infinite_values_by_column or quality.conflicting_label_groups:
        raise AdmissionBlockedError(
            f"{card.id}: nonfinite values or conflicting feature-identical labels"
        )
    return {
        "synthetic": False,
        "status": "admitted_for_local_academic_use",
        "dataset": card.id,
        "table": table.id,
        "source_sha256": digest,
        "rows": len(frame),
        "license": card.license.model_dump(mode="json"),
        "card_sha256": hashlib.sha256(card.model_dump_json().encode()).hexdigest(),
        "quality": quality.model_dump(mode="json"),
    }
