"""Export the dataset registry as the portal's versioned ``datasets.json``.

It holds provenance, license and schema metadata only, and never data, fingerprints of
private files or row-level content. A test keeps the committed portal copy in sync with
the registry.
"""

from __future__ import annotations

import json
from typing import Any

from driftguard.data.registry import load_registry

CATALOG_SCHEMA_VERSION = 1


def build_catalog() -> dict[str, Any]:
    datasets = []
    for card in sorted(load_registry().values(), key=lambda c: c.name.lower()):
        lic = card.license
        datasets.append(
            {
                "id": card.id,
                "name": card.name,
                "publisher": card.publisher,
                "homepage": str(card.homepage),
                "description": card.description,
                "license": {
                    "name": lic.name,
                    "source_url": str(lic.source_url),
                    "verified_on": lic.verified_on.isoformat() if lic.verified_on else None,
                    "academic_use": lic.academic_use,
                    "commercial_use": lic.commercial_use,
                    "raw_redistribution": lic.raw_redistribution,
                    "derived_artifact_redistribution": lic.derived_artifact_redistribution,
                    "attribution_required": lic.attribution_required,
                },
                "citations": [c.model_dump() for c in card.citations],
                "acquisition": {
                    "method": card.acquisition.method,
                    "url": str(card.acquisition.url),
                    "kaggle_slug": card.acquisition.kaggle.slug
                    if card.acquisition.kaggle
                    else None,
                },
                "tables": [
                    {
                        "id": t.id,
                        "filename": t.filename,
                        "schema_status": t.schema_status,
                        "n_columns": len(t.columns),
                        "n_candidate_features": len(t.feature_columns),
                        "n_private_columns": len(t.private_columns),
                        "label_column": t.label_column,
                        "attack_type_column": t.attack_type_column,
                        "timestamp_column": t.timestamp_column,
                        "fingerprint_recorded": t.sha256 is not None,
                    }
                    for t in card.tables
                ],
            }
        )
    return {"schema_version": CATALOG_SCHEMA_VERSION, "datasets": datasets}


def catalog_json() -> str:
    return json.dumps(build_catalog(), indent=2, ensure_ascii=False) + "\n"
