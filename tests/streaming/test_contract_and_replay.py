"""Event contract and replay encoding (no broker)."""

from __future__ import annotations

import json
import math
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest

from driftguard.platform.bundle import LoadedBundle
from driftguard.streaming.contract import (
    MAX_PAYLOAD_BYTES,
    ContractViolationError,
    FeatureContract,
    alerts_topic,
    features_topic,
    parse_feature_message,
)
from driftguard.streaming.replay import (
    ReplaySource,
    encode_messages,
    held_out_source,
    replay,
    synthetic_source,
)


def _message(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema_version": "driftguard/v1",
        "event_id": str(uuid.uuid4()),
        "source": "replay",
        "evidence_tier": "synthetic_fixture",
        "dataset_sha256": "a" * 64,
        "replay_send_time_utc": datetime.now(UTC).isoformat(),
        "publisher_sequence": 0,
        "features": {"duration": 1.0, "proto": "tcp"},
    }
    base.update(overrides)
    return base


def _bytes(obj: object) -> bytes:
    return json.dumps(obj).encode()


def test_valid_message_parses() -> None:
    msg = parse_feature_message(_bytes(_message()))
    assert msg.features == {"duration": 1.0, "proto": "tcp"}
    assert msg.event_time_utc is None  # replay never invents an original event time


@pytest.mark.parametrize(
    ("payload", "category"),
    [
        (b"x" * (MAX_PAYLOAD_BYTES + 1), "oversized"),
        (b"{not json", "malformed"),
        (b"\xff\xfe", "malformed"),
        (b"[1, 2]", "malformed"),
        (b'{"features": {"duration": NaN}}', "malformed"),
        (_bytes(_message(label="dos")), "schema"),  # ground truth must never ride along
        (_bytes(_message(dataset_sha256=None)), "schema"),
        (_bytes(_message(event_id="not-a-uuid")), "schema"),
        (_bytes(_message(source="capture")), "schema"),
        (_bytes(_message(evidence_tier="lab_capture")), "schema"),
        (_bytes(_message(replay_send_time_utc="2026-09-23T10:00:00")), "schema"),
        (_bytes(_message(features={})), "schema"),
    ],
)
def test_invalid_payloads_are_rejected(payload: bytes, category: str) -> None:
    with pytest.raises(ContractViolationError) as info:
        parse_feature_message(payload)
    assert info.value.category == category


def test_capture_requires_lab_tier_and_capture_id() -> None:
    msg = _message(
        source="capture",
        evidence_tier="lab_capture",
        capture_id="lab-cap-1",
        dataset_sha256=None,
        replay_send_time_utc=None,
    )
    assert parse_feature_message(_bytes(msg)).capture_id == "lab-cap-1"


def test_feature_contract_checks_names_types_and_allows_missing() -> None:
    contract = FeatureContract(features=("duration", "proto"), numeric_features={"duration"})
    contract.check({"duration": None, "proto": None})
    for bad, category in [
        ({"duration": 1.0}, "feature_mismatch"),
        ({"duration": 1.0, "proto": "tcp", "extra": 1.0}, "feature_mismatch"),
        ({"duration": "1.0", "proto": "tcp"}, "invalid_value"),
        ({"duration": math.inf, "proto": "tcp"}, "invalid_value"),
        ({"duration": 1.0, "proto": "x" * 65}, "invalid_value"),
        ({"duration": 1.0, "proto": 3.0}, "invalid_value"),
    ]:
        with pytest.raises(ContractViolationError) as info:
            contract.check(bad)
        assert info.value.category == category
    same = FeatureContract(features=("duration", "proto"), numeric_features={"duration"})
    assert contract.sha256 == same.sha256
    with pytest.raises(ValueError, match="subset"):
        FeatureContract(features=("a",), numeric_features={"b"})


def test_topics_validate_identifiers() -> None:
    assert features_topic("synthetic", "lab-1") == "driftguard/v1/features/synthetic/lab-1"
    assert alerts_topic("lab-1") == "driftguard/v1/alerts/lab-1"
    for bad in ("", "Lab", "a/b", "#", "+", "x" * 40):
        with pytest.raises(ValueError):
            alerts_topic(bad)


def _source(rows: pd.DataFrame) -> ReplaySource:
    return ReplaySource(
        rows=rows,
        numeric_features=frozenset({"duration"}),
        dataset_sha256="b" * 64,
        evidence_tier="synthetic_fixture",
        description="test",
        feed="synthetic",
    )


def test_encoding_maps_missing_and_nonfinite_to_null_and_numbers_sequentially() -> None:
    rows = pd.DataFrame(
        {
            "duration": [1.5, float("nan"), float("inf"), "junk"],
            "proto": ["tcp", None, "udp", "icmp"],
        }
    )
    encoded = list(encode_messages(_source(rows), start_sequence=10))
    assert [seq for seq, _ in encoded] == [10, 11, 12, 13]
    parsed = [parse_feature_message(payload) for _, payload in encoded]
    assert [m.features["duration"] for m in parsed] == [1.5, None, None, None]
    assert parsed[1].features["proto"] is None
    assert len({m.event_id for m in parsed}) == 4
    assert all("label" not in json.loads(p) for _, p in encoded)


def test_replay_publishes_on_schedule_and_reports_imposed_timing() -> None:
    rows = pd.DataFrame({"duration": [1.0] * 30, "proto": ["tcp"] * 30})
    sent: list[bytes] = []
    stats = replay(_source(rows), sent.append, rate_per_s=200.0, max_events=20)
    assert stats["sent"] == len(sent) == 20
    assert stats["achieved_rate_per_s"] <= 200.0 * 1.05
    assert "not original event time" in stats["timing"]
    with pytest.raises(ValueError):
        replay(_source(rows), sent.append, rate_per_s=0)


def test_synthetic_source_matches_bundle_contract(bundle: LoadedBundle) -> None:
    src = synthetic_source(bundle.path, n=25)
    assert list(src.rows.columns) == bundle.metadata["features"]
    assert src.evidence_tier == "synthetic_fixture" and len(src.rows) == 25


def test_heldout_source_refuses_synthetic_runs(bundle_dir: Path) -> None:
    with pytest.raises(ValueError, match="real-data run"):
        held_out_source(bundle_dir)  # bundle dir holds the synthetic run's manifest


def test_generator_ignores_class_mapping_key_order() -> None:
    from driftguard.data.synthetic import generate_synthetic_flows
    from driftguard.smoke import frame_fingerprint

    forward = {"normal": 0.7, "dos": 0.15, "scan": 0.1, "injection": 0.05}
    backward = dict(reversed(list(forward.items())))
    a = generate_synthetic_flows(n_samples=300, seed=4, class_proportions=forward)
    b = generate_synthetic_flows(n_samples=300, seed=4, class_proportions=backward)
    assert frame_fingerprint(a) == frame_fingerprint(b)


def test_synthetic_replay_reproduces_the_recorded_test_partition(bundle: LoadedBundle) -> None:
    """Replayed rows must be the run's own held-out rows: predictions on them reproduce
    the accuracy recorded at training time (fresh-seed rows would not)."""
    from driftguard.config import ExperimentConfig
    from driftguard.experiments import load_dataset, prepare
    from driftguard.reporting.manifest import ExperimentManifest

    manifest = ExperimentManifest.model_validate_json((bundle.path / "manifest.json").read_text())
    config = ExperimentConfig.model_validate(manifest.config)
    y_test = prepare(load_dataset(config.dataset, config.seed), config).y_test
    src = synthetic_source(bundle.path)
    assert len(src.rows) == len(y_test) == manifest.protocol_details["n_test"]
    predicted = bundle.pipeline.predict(src.rows)
    accuracy = float((predicted == y_test.to_numpy()).mean())
    assert accuracy == pytest.approx(bundle.metadata["metrics"]["accuracy"])
