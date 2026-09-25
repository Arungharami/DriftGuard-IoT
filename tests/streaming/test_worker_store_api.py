"""Worker, event store and read-only API behaviour without a broker."""

from __future__ import annotations

import dataclasses
import json
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from driftguard.platform.bundle import LoadedBundle
from driftguard.streaming.api import create_demo_api
from driftguard.streaming.contract import Alert
from driftguard.streaming.replay import encode_messages, synthetic_source
from driftguard.streaming.store import EventDeduplicator, EventStore
from driftguard.streaming.worker import InferenceWorker, OutputShiftMonitor


def _payloads(bundle: LoadedBundle, n: int, seed: int = 5) -> list[bytes]:
    src = synthetic_source(bundle.path, n=n)
    return [payload for _, payload in encode_messages(src)]


@pytest.fixture
def store(tmp_path: Path) -> EventStore:
    events = EventStore(tmp_path / "events.sqlite3")
    yield events
    events.close()


def test_prediction_alert_is_sanitised_and_downgraded_to_synthetic(
    bundle: LoadedBundle, store: EventStore
) -> None:
    worker = InferenceWorker(store, bundle)
    alert = worker.process(_payloads(bundle, 1)[0])
    assert alert is not None and alert.status == "predicted"
    assert alert.decision in bundle.metadata["labels"]
    assert alert.evidence_tier == "synthetic_fixture" and alert.reportable is False
    assert store.summary()["model_provenance"] == [
        {
            "model_sha256": bundle.model_sha256,
            "dataset_sha256": bundle.dataset_sha256,
            "synthetic": True,
        }
    ]
    assert alert.model_sha256 == bundle.model_sha256
    assert alert.inference_ms is not None and alert.inference_ms > 0
    assert alert.end_to_end_ms is not None and alert.end_to_end_ms >= 0
    dumped = alert.model_dump_json()
    assert not any(f'"{name}"' in dumped for name in bundle.metadata["features"])


def test_duplicates_are_suppressed_in_memory_and_across_restarts(
    bundle: LoadedBundle, store: EventStore
) -> None:
    payload = _payloads(bundle, 1)[0]
    worker = InferenceWorker(store, bundle)
    assert worker.process(payload).status == "predicted"  # type: ignore[union-attr]
    assert worker.process(payload).status == "duplicate"  # type: ignore[union-attr]
    restarted = InferenceWorker(store, bundle, deduplicator=EventDeduplicator(10))
    assert restarted.process(payload).status == "duplicate"  # type: ignore[union-attr]
    summary = store.summary()
    assert summary["events_by_status"] == {"predicted": 1}
    assert summary["counters"]["duplicates_suppressed"] == 2


def test_deduplicator_memory_is_bounded() -> None:
    import uuid

    dedup = EventDeduplicator(capacity=3)
    ids = [uuid.uuid4() for _ in range(5)]
    assert not any(dedup.is_duplicate(i) for i in ids)
    assert len(dedup._seen) == 3
    assert dedup.is_duplicate(ids[-1]) and not dedup.is_duplicate(ids[0])


def test_malformed_payloads_are_counted_not_stored(bundle: LoadedBundle, store: EventStore) -> None:
    worker = InferenceWorker(store, bundle)
    assert worker.process(b"{broken") is None
    assert worker.process(b"x" * 20000) is None
    summary = store.summary()
    assert summary["events_by_status"] == {}
    assert summary["counters"] == {"rejected_malformed": 1, "rejected_oversized": 1}


def test_contract_mismatch_is_rejected_without_prediction(
    bundle: LoadedBundle, store: EventStore
) -> None:
    msg = json.loads(_payloads(bundle, 1)[0])
    msg["features"].pop(bundle.metadata["features"][0])
    alert = InferenceWorker(store, bundle).process(json.dumps(msg).encode())
    assert alert is not None and alert.status == "rejected"
    assert alert.reason == "feature_mismatch" and alert.decision is None


def test_missing_model_fails_closed(bundle: LoadedBundle, store: EventStore) -> None:
    alert = InferenceWorker(store, None).process(_payloads(bundle, 1)[0])
    assert alert is not None and alert.status == "model_unavailable"
    assert alert.decision is None and alert.model_sha256 is None


def test_real_bundle_rejects_replay_from_a_different_dataset(
    bundle: LoadedBundle, store: EventStore
) -> None:
    real = dataclasses.replace(
        bundle, metadata={**bundle.metadata, "synthetic_data": False}, dataset_sha256="c" * 64
    )
    msg = json.loads(_payloads(bundle, 1)[0])
    msg["evidence_tier"] = "dataset_replay"
    alert = InferenceWorker(store, real).process(json.dumps(msg).encode())
    assert alert is not None and alert.status == "rejected" and alert.reason == "dataset_mismatch"
    msg["event_id"], msg["dataset_sha256"] = "7d0f5f36-3c1d-4d7a-9b87-1c1c1c1c1c1c", "c" * 64
    ok = InferenceWorker(store, real).process(json.dumps(msg).encode())
    assert ok is not None and ok.status == "predicted" and ok.evidence_tier == "dataset_replay"


def test_bounded_queue_and_rate_limit_drop_and_count(
    bundle: LoadedBundle, store: EventStore
) -> None:
    payloads = _payloads(bundle, 3)
    worker = InferenceWorker(store, bundle, queue_size=2)
    assert [worker.submit(p) for p in payloads] == [True, True, False]
    limited = InferenceWorker(store, bundle, rate_limit_per_s=1.0)
    assert [limited.submit(p) for p in payloads] == [True, False, False]
    counters = store.summary()["counters"]
    assert counters["dropped_queue_full"] == 1 and counters["dropped_rate_limited"] == 2


def test_run_loop_drains_queue_and_publishes_each_alert(
    bundle: LoadedBundle, store: EventStore
) -> None:
    worker = InferenceWorker(store, bundle)
    published: list[tuple[str, Alert]] = []
    for p in _payloads(bundle, 20):
        worker.submit(p, "driftguard/v1/features/synthetic/lab-1")
    stop = threading.Event()
    stop.set()  # drain what is queued, then exit
    worker.run(stop, lambda topic, alert: published.append((topic, alert)))
    assert len(published) == 20 and store.summary()["events_by_status"] == {"predicted": 20}
    assert {t for t, _ in published} == {"driftguard/v1/features/synthetic/lab-1"}


def test_output_monitor_flags_an_injected_output_shift(store: EventStore) -> None:
    monitor = OutputShiftMonitor("normal", delta=0.002)
    alarms = [monitor.update("normal") for _ in range(500)]
    assert not any(alarms)  # no false alarm on a stationary benign segment
    later = [monitor.update("dos") for _ in range(200)]
    assert any(later)


def test_summary_percentiles_and_sanitisation(bundle: LoadedBundle, store: EventStore) -> None:
    worker = InferenceWorker(store, bundle)
    for p in _payloads(bundle, 30):
        worker.process(p)
    summary = store.summary()
    lat = summary["inference_ms"]
    assert lat["n"] == 30 and lat["p50"] <= lat["p95"] <= lat["p99"]
    assert summary["reportable"] is False
    text = json.dumps(summary)
    assert not any(name in text for name in bundle.metadata["features"])


def test_store_retention_is_bounded(bundle: LoadedBundle, tmp_path: Path) -> None:
    events = EventStore(tmp_path / "small.sqlite3", max_events=5)
    worker = InferenceWorker(events, bundle)
    for p in _payloads(bundle, 12):
        worker.process(p)
    assert sum(events.summary()["events_by_status"].values()) == 5
    events.close()


def test_api_requires_configured_token_and_returns_aggregates_only(
    bundle: LoadedBundle, tmp_path: Path
) -> None:
    path = tmp_path / "api.sqlite3"
    events = EventStore(path)
    worker = InferenceWorker(events, bundle)
    for p in _payloads(bundle, 5):
        worker.process(p)
    unconfigured = TestClient(create_demo_api(path, token=None))
    assert unconfigured.get("/health").json() == {"status": "unavailable"}
    assert unconfigured.get("/v1/summary").status_code == 503
    client = TestClient(create_demo_api(path, token="s3cret-token", requests_per_s=1000))  # noqa: S106
    assert client.get("/v1/summary").status_code == 401
    assert client.get("/v1/summary", headers={"Authorization": "Bearer nope"}).status_code == 401
    auth = {"Authorization": "Bearer s3cret-token"}
    body = client.get("/v1/summary", headers=auth).json()
    assert body["events_by_status"] == {"predicted": 5} and "NON-REPORTABLE" in body["notice"]
    recent = client.get("/v1/events/recent?limit=3", headers=auth).json()["events"]
    assert len(recent) == 3 and "event_id" not in recent[0]
    assert client.get("/v1/events/recent?limit=500", headers=auth).status_code == 422
    for path_ in ("/docs", "/openapi.json"):
        assert client.get(path_).status_code == 404
    assert client.post("/v1/summary", headers=auth).status_code == 405
    events.close()


def test_api_rate_limit(tmp_path: Path) -> None:
    client = TestClient(create_demo_api(tmp_path / "r.sqlite3", token="t", requests_per_s=1))  # noqa: S106
    codes = [
        client.get("/v1/summary", headers={"Authorization": "Bearer t"}).status_code
        for _ in range(5)
    ]
    assert 429 in codes and codes[0] == 200


def test_provenance_and_replay_telemetry_survive_restart_without_private_fields(tmp_path):
    from driftguard.streaming.store import EventStore

    path = tmp_path / "telemetry.sqlite3"
    store = EventStore(path)
    store.record_replay(
        "a" * 64,
        {
            "sent": 2,
            "target_rate_per_s": 10.0,
            "achieved_rate_per_s": 9.0,
            "evidence_tier": "synthetic_fixture",
            "private": "do not expose",
        },
    )
    store.close()
    restarted = EventStore(path)
    replay = restarted.summary()["last_replay"]
    assert replay["dataset_sha256"] == "a" * 64
    assert replay["achieved_rate_per_s"] == 9.0
    assert replay["completed_at_utc"]
    assert "private" not in replay
    restarted.close()
