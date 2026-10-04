"""Invalid limits must never silently disable streaming backpressure."""

from __future__ import annotations

import math

import pytest

from driftguard.streaming.store import EventStore
from driftguard.streaming.worker import InferenceWorker, TokenBucket


@pytest.mark.parametrize("limit", [0, -1, False, 1.5])
def test_worker_rejects_unbounded_or_noninteger_queue(limit: int, tmp_path) -> None:
    store = EventStore(tmp_path / "events.sqlite3")
    try:
        with pytest.raises(ValueError, match="queue_size"):
            InferenceWorker(store, None, queue_size=limit)
    finally:
        store.close()


@pytest.mark.parametrize("rate", [0, -1, math.inf, math.nan])
def test_worker_rejects_invalid_rate(rate: float, tmp_path) -> None:
    store = EventStore(tmp_path / "events.sqlite3")
    try:
        with pytest.raises(ValueError, match="rate_limit_per_s"):
            InferenceWorker(store, None, rate_limit_per_s=rate)
    finally:
        store.close()


def test_token_bucket_rejects_invalid_rate_and_burst() -> None:
    with pytest.raises(ValueError, match="rate_per_s"):
        TokenBucket(math.nan, 1)
    with pytest.raises(ValueError, match="burst"):
        TokenBucket(1, 0)


def test_positive_queue_enforces_backpressure(tmp_path) -> None:
    store = EventStore(tmp_path / "events.sqlite3")
    try:
        worker = InferenceWorker(store, None, queue_size=1)
        assert worker.submit(b"first")
        assert not worker.submit(b"second")
        assert store.summary()["counters"]["dropped_queue_full"] == 1
    finally:
        store.close()
