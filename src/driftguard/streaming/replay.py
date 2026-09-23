"""Tier-A replay producer: feature rows -> ``driftguard/v1`` messages at an imposed rate.

Replay timing is imposed by this producer. ``replay_send_time_utc`` is the send time,
never the original event time, which stays ``None`` unless the source records it.
Labels are never included. Dataset replay is restricted to the held-out test rows of a
verified run, so demo predictions never re-score training rows.
"""

from __future__ import annotations

import json
import math
import time
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from driftguard.reporting.manifest import ExperimentManifest
from driftguard.reporting.provenance import sha256_file
from driftguard.streaming.contract import EvidenceTier


@dataclass(frozen=True)
class ReplaySource:
    rows: pd.DataFrame  # model-visible features only
    numeric_features: frozenset[str]
    dataset_sha256: str
    evidence_tier: EvidenceTier
    description: str
    feed: str  # topic segment naming the feature contract


def _clean(value: Any, numeric: bool) -> float | str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if numeric:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None  # the frozen pipeline coerces unparsable numerics to missing too
        return number if math.isfinite(number) else None
    return str(value)


def encode_messages(
    source: ReplaySource, *, start_sequence: int = 0, clock: Callable[[], datetime] | None = None
) -> Iterator[tuple[int, bytes]]:
    now = clock or (lambda: datetime.now(UTC))
    columns = list(source.rows.columns)
    for offset, values in enumerate(source.rows.itertuples(index=False, name=None)):
        sequence = start_sequence + offset
        message = {
            "schema_version": "driftguard/v1",
            "event_id": str(uuid.uuid4()),
            "source": "replay",
            "evidence_tier": source.evidence_tier,
            "dataset_sha256": source.dataset_sha256,
            "capture_id": None,
            "event_time_utc": None,
            "replay_send_time_utc": now().isoformat(),
            "publisher_sequence": sequence,
            "features": {
                c: _clean(v, c in source.numeric_features)
                for c, v in zip(columns, values, strict=True)
            },
        }
        yield sequence, json.dumps(message, allow_nan=False).encode("utf-8")


def replay(
    source: ReplaySource,
    publish: Callable[[bytes], None],
    *,
    rate_per_s: float,
    max_events: int | None = None,
) -> dict[str, Any]:
    """Publish at a fixed schedule (monotonic clock); returns achieved-rate statistics."""
    if rate_per_s <= 0:
        raise ValueError("rate must be positive")
    interval, sent = 1.0 / rate_per_s, 0
    started = time.monotonic()
    for sequence, payload in encode_messages(source):
        if max_events is not None and sent >= max_events:
            break
        delay = started + sequence * interval - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        publish(payload)
        sent += 1
    elapsed = time.monotonic() - started
    return {
        "sent": sent,
        "target_rate_per_s": rate_per_s,
        "achieved_rate_per_s": sent / elapsed if elapsed > 0 else None,
        "evidence_tier": source.evidence_tier,
        "timing": "imposed replay schedule; not original event time",
    }


def synthetic_source(bundle_dir: Path, *, n: int | None = None) -> ReplaySource:
    """Held-out test rows of the bundle's SYNTHETIC run, regenerated deterministically.

    The fixture generator draws class distributions per (seed, size), so rows from any
    other seed would come from a different synthetic world. Rows are therefore rebuilt
    from the run's own config and verified against its recorded fixture fingerprint.
    """
    from driftguard.config import ExperimentConfig
    from driftguard.experiments import load_dataset, prepare

    manifest = ExperimentManifest.model_validate_json((bundle_dir / "manifest.json").read_text())
    if not manifest.synthetic_data:
        raise ValueError("synthetic replay requires a synthetic-fixture bundle")
    config = ExperimentConfig.model_validate(manifest.config)
    data = load_dataset(config.dataset, config.seed)
    if data.provenance.source_sha256 != manifest.dataset.source_sha256:
        raise ValueError("regenerated fixture differs from the run's recorded fingerprint")
    test = prepare(data, config).X_test
    rows = test[manifest.protocol_details["features_in"]].head(n)
    return ReplaySource(
        rows=rows,
        numeric_features=frozenset(manifest.protocol_details["numeric_columns"]),
        dataset_sha256=manifest.dataset.source_sha256,
        evidence_tier="synthetic_fixture",
        description=f"held-out rows of synthetic run {manifest.run_id} (NON-REPORTABLE)",
        feed="synthetic",
    )


def held_out_source(run_dir: Path, *, data_root: Path | None = None) -> ReplaySource:
    """Test-partition rows of a verified real-data run, after dataset admission."""
    from driftguard.config import ExperimentConfig
    from driftguard.experiments import load_dataset
    from driftguard.platform.admission import admit_dataset

    manifest = ExperimentManifest.model_validate_json((run_dir / "manifest.json").read_text())
    if manifest.synthetic_data:
        raise ValueError("dataset replay requires a real-data run; use the synthetic source")
    record = manifest.protocol_details.get("split_record")
    if not record or sha256_file(run_dir / record["file"]) != record["file_sha256"]:
        raise ValueError("split.json missing or its SHA-256 differs from the manifest")
    config = ExperimentConfig.model_validate(manifest.config)
    evidence = admit_dataset(config.dataset, data_root)
    if evidence["source_sha256"] != manifest.dataset.source_sha256:
        raise ValueError("admitted file differs from the run's dataset fingerprint")
    data = load_dataset(config.dataset, config.seed, data_root)
    test_index = json.loads((run_dir / record["file"]).read_text())["test_index"]
    by_label = {str(i): i for i in data.frame.index}
    rows = data.frame.loc[
        [by_label[i] for i in test_index], manifest.protocol_details["features_in"]
    ]
    return ReplaySource(
        rows=rows,
        numeric_features=frozenset(manifest.protocol_details["numeric_columns"]),
        dataset_sha256=manifest.dataset.source_sha256,
        evidence_tier="dataset_replay",
        description=f"held-out rows of run {manifest.run_id}",
        feed=manifest.dataset.dataset_id.replace("_", ""),
    )
