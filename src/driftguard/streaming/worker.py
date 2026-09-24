"""Streaming inference worker: validate -> deduplicate -> bounded queue -> infer -> record.

Transport-independent so it is tested without a broker. The MQTT callback thread only
calls :meth:`InferenceWorker.submit`, which never blocks: when the bounded queue is full
the message is dropped and counted. Without a verified model bundle the worker fails
closed and records ``model_unavailable`` instead of inventing predictions.
"""

from __future__ import annotations

import queue
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from driftguard.platform.bundle import LoadedBundle
from driftguard.streaming.contract import (
    Alert,
    ContractViolationError,
    EvidenceTier,
    FeatureContract,
    FeatureMessage,
    parse_feature_message,
)
from driftguard.streaming.store import EventDeduplicator, EventStore


class OutputShiftMonitor:
    """ADWIN over the model's predicted-attack indicator (River implementation).

    It needs no labels and flags a change in the *output* distribution. That is neither
    concept-drift ground truth nor a validated detector: ``delta`` must be calibrated on
    development data before any alarm is interpreted.
    """

    name = "adwin_output_attack_rate"

    def __init__(self, benign_label: str, *, delta: float = 0.002) -> None:
        from river.drift import ADWIN

        self.benign_label = benign_label
        self.delta = delta
        self._adwin = ADWIN(delta=delta)  # type: ignore[no-untyped-call]
        self.observations = 0

    def update(self, decision: str) -> bool:
        self.observations += 1
        self._adwin.update(float(decision != self.benign_label))  # type: ignore[no-untyped-call]
        return bool(self._adwin.drift_detected)


class TokenBucket:
    def __init__(self, rate_per_s: float, burst: int) -> None:
        self.rate, self.capacity = rate_per_s, float(burst)
        self.tokens, self.updated = float(burst), time.monotonic()

    def allow(self) -> bool:
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
        self.updated = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


@dataclass(frozen=True)
class _Received:
    topic: str
    payload: bytes
    received_at: datetime


class InferenceWorker:
    def __init__(
        self,
        store: EventStore,
        bundle: LoadedBundle | None,
        *,
        monitor: OutputShiftMonitor | None = None,
        deduplicator: EventDeduplicator | None = None,
        queue_size: int = 1000,
        rate_limit_per_s: float | None = None,
    ) -> None:
        self.store = store
        self.bundle = bundle
        self.contract = (
            FeatureContract(
                features=tuple(bundle.metadata["features"]),
                numeric_features=frozenset(bundle.metadata["numeric_features"]),
            )
            if bundle
            else None
        )
        self.monitor = monitor
        self.dedup = deduplicator or EventDeduplicator()
        self.queue: queue.Queue[_Received] = queue.Queue(maxsize=queue_size)
        self.limiter = (
            TokenBucket(rate_limit_per_s, max(1, int(rate_limit_per_s)))
            if (rate_limit_per_s)
            else None
        )

    # ------------------------------------------------------------------ ingestion
    def submit(self, payload: bytes, topic: str = "") -> bool:
        """Non-blocking hand-off from the transport thread."""
        if self.limiter and not self.limiter.allow():
            self.store.increment("dropped_rate_limited")
            return False
        try:
            self.queue.put_nowait(_Received(topic, payload, datetime.now(UTC)))
        except queue.Full:
            self.store.increment("dropped_queue_full")
            return False
        return True

    def run(
        self, stop: threading.Event, publish: Callable[[str, Alert], None] | None = None
    ) -> None:
        while not stop.is_set() or not self.queue.empty():
            try:
                item = self.queue.get(timeout=0.1)
            except queue.Empty:
                continue
            alert = self.process(item.payload, item.received_at)
            if alert is not None and publish is not None and alert.status != "duplicate":
                publish(item.topic, alert)
            self.queue.task_done()

    # ------------------------------------------------------------------ processing
    def process(self, payload: bytes, received_at: datetime | None = None) -> Alert | None:
        received_at = received_at or datetime.now(UTC)
        try:
            message = parse_feature_message(payload)
        except ContractViolationError as exc:
            # No trustworthy event id: count, never store payload content.
            self.store.increment(f"rejected_{exc.category}")
            return None
        if self.dedup.is_duplicate(message.event_id):
            self.store.increment("duplicates_suppressed")
            return self._alert(message, received_at, "duplicate", reason="event_id seen")
        alert = self._evaluate(message, received_at)
        if not self.store.record(alert):
            self.store.increment("duplicates_suppressed")
            return alert.model_copy(update={"status": "duplicate"})
        if alert.status == "rejected":
            self.store.increment(f"rejected_{alert.reason}")
        if alert.decision is not None and self.monitor and self.monitor.update(alert.decision):
            self.store.record_alarm(
                datetime.now(UTC).isoformat(), self.monitor.observations, self.monitor.name
            )
        return alert

    def _evaluate(self, message: FeatureMessage, received_at: datetime) -> Alert:
        if self.bundle is None or self.contract is None:
            return self._alert(
                message, received_at, "model_unavailable", reason="no verified model bundle"
            )
        try:
            self.contract.check(message.features)
        except ContractViolationError as exc:
            return self._alert(message, received_at, "rejected", reason=exc.category)
        if (
            not self.bundle.synthetic
            and message.evidence_tier == "dataset_replay"
            and message.dataset_sha256 != self.bundle.dataset_sha256
        ):
            return self._alert(message, received_at, "rejected", reason="dataset_mismatch")
        frame = pd.DataFrame([message.features], columns=list(self.contract.features))
        started = time.perf_counter()
        try:
            decision = str(self.bundle.pipeline.predict(frame)[0])
        except (ValueError, TypeError):
            return self._alert(message, received_at, "rejected", reason="model_input_error")
        inference_ms = (time.perf_counter() - started) * 1000.0
        return self._alert(
            message, received_at, "predicted", decision=decision, inference_ms=inference_ms
        )

    def _alert(
        self, message: FeatureMessage, received_at: datetime, status: Any, **extra: Any
    ) -> Alert:
        done = datetime.now(UTC)
        e2e = None
        if status == "predicted" and message.replay_send_time_utc is not None:
            # Wall-clock difference: meaningful only when producer and worker share a host.
            e2e = (done - message.replay_send_time_utc).total_seconds() * 1000.0
        return Alert(
            event_id=message.event_id,
            publisher_sequence=message.publisher_sequence,
            received_at_utc=received_at,
            status=status,
            evidence_tier=self._tier(message.evidence_tier),
            model_sha256=self.bundle.model_sha256 if self.bundle else None,
            contract_sha256=self.contract.sha256 if self.contract else None,
            end_to_end_ms=e2e,
            **extra,
        )

    def _tier(self, claimed: EvidenceTier) -> EvidenceTier:
        """A synthetic model or synthetic rows always downgrade the evidence tier."""
        if self.bundle is not None and self.bundle.synthetic:
            return "synthetic_fixture"
        return claimed
