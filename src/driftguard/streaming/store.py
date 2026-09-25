"""Bounded, append-only event store and deduplication for the streaming worker.

SQLite in WAL mode lets a separate API process read while the worker writes. The event
id is the primary key, so a QoS 1 redelivery that slips past the in-memory cache (e.g.
after a worker restart) is still recorded only once.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from collections import OrderedDict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import numpy as np

from driftguard.streaming.contract import Alert

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE,
    publisher_sequence INTEGER,
    received_at_utc TEXT NOT NULL,
    status TEXT NOT NULL,
    decision TEXT,
    reason TEXT,
    evidence_tier TEXT,
    model_sha256 TEXT,
    inference_ms REAL,
    end_to_end_ms REAL
);
CREATE TABLE IF NOT EXISTS counters (name TEXT PRIMARY KEY, value INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS demo_metadata (name TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS monitor_alarms (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    detected_at_utc TEXT NOT NULL,
    observations INTEGER NOT NULL,
    detector TEXT NOT NULL
);
"""
PERCENTILES = (50, 95, 99)


class EventDeduplicator:
    """Remembers the most recent ``capacity`` event ids (bounded memory)."""

    def __init__(self, capacity: int = 100_000) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._seen: OrderedDict[UUID, None] = OrderedDict()

    def is_duplicate(self, event_id: UUID) -> bool:
        if event_id in self._seen:
            self._seen.move_to_end(event_id)
            return True
        self._seen[event_id] = None
        if len(self._seen) > self.capacity:
            self._seen.popitem(last=False)
        return False


class EventStore:
    def __init__(self, path: Path, *, max_events: int = 200_000) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.max_events = max_events
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript(SCHEMA)

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def record(self, alert: Alert) -> bool:
        """Insert an alert; returns False if its event id was already stored."""
        event_id = str(alert.event_id) if alert.event_id else None
        with self._lock:
            cur = self._db.execute(
                "INSERT OR IGNORE INTO events (event_id, publisher_sequence, received_at_utc,"
                " status, decision, reason, evidence_tier, model_sha256, inference_ms,"
                " end_to_end_ms) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    event_id,
                    alert.publisher_sequence,
                    alert.received_at_utc.isoformat(),
                    alert.status,
                    alert.decision,
                    alert.reason,
                    alert.evidence_tier,
                    alert.model_sha256,
                    alert.inference_ms,
                    alert.end_to_end_ms,
                ),
            )
            inserted = cur.rowcount == 1
            if inserted:
                self._db.execute(
                    "DELETE FROM events WHERE seq <= (SELECT MAX(seq) FROM events) - ?",
                    (self.max_events,),
                )
            return inserted

    def increment(self, name: str, by: int = 1) -> None:
        with self._lock:
            self._db.execute(
                "INSERT INTO counters VALUES (?, ?) "
                "ON CONFLICT(name) DO UPDATE SET value = value + excluded.value",
                (name, by),
            )

    def record_alarm(self, detected_at_utc: str, observations: int, detector: str) -> None:
        with self._lock:
            self._db.execute(
                "INSERT INTO monitor_alarms (detected_at_utc, observations, detector)"
                " VALUES (?,?,?)",
                (detected_at_utc, observations, detector),
            )

    def record_model_provenance(
        self, model_sha256: str, dataset_sha256: str, *, synthetic: bool
    ) -> None:
        """Keep only verified bundle fingerprints, never its paths or training rows."""
        self._metadata(
            f"model:{model_sha256}",
            {
                "model_sha256": model_sha256,
                "dataset_sha256": dataset_sha256,
                "synthetic": synthetic,
            },
        )

    def record_replay(self, dataset_sha256: str, stats: dict[str, Any]) -> None:
        """Explicit same-host producer opt-in: persist measured, completed replay stats."""
        self._metadata(
            "last_replay",
            {
                "completed_at_utc": datetime.now(UTC).isoformat(),
                "dataset_sha256": dataset_sha256,
                **{
                    key: stats[key]
                    for key in ("sent", "target_rate_per_s", "achieved_rate_per_s", "evidence_tier")
                },
            },
        )

    def _metadata(self, name: str, value: dict[str, Any]) -> None:
        with self._lock:
            self._db.execute(
                "INSERT INTO demo_metadata VALUES (?,?) "
                "ON CONFLICT(name) DO UPDATE SET value=excluded.value",
                (name, json.dumps(value, allow_nan=False)),
            )

    def summary(self) -> dict[str, Any]:
        """Sanitised aggregates only: no feature values, identifiers or payloads."""
        with self._lock:
            status = dict(self._db.execute("SELECT status, COUNT(*) FROM events GROUP BY 1"))
            decisions = dict(
                self._db.execute(
                    "SELECT decision, COUNT(*) FROM events WHERE status='predicted' GROUP BY 1"
                )
            )
            tiers = dict(self._db.execute("SELECT evidence_tier, COUNT(*) FROM events GROUP BY 1"))
            counters = dict(self._db.execute("SELECT name, value FROM counters"))
            inference = [
                r[0]
                for r in self._db.execute(
                    "SELECT inference_ms FROM events WHERE inference_ms IS NOT NULL"
                )
            ]
            e2e = [
                r[0]
                for r in self._db.execute(
                    "SELECT end_to_end_ms FROM events WHERE end_to_end_ms IS NOT NULL"
                )
            ]
            window = self._db.execute(
                "SELECT MIN(received_at_utc), MAX(received_at_utc), COUNT(*) FROM events"
                " WHERE status='predicted'"
            ).fetchone()
            alarms = self._db.execute("SELECT COUNT(*) FROM monitor_alarms").fetchone()[0]
            metadata = {
                name: json.loads(value)
                for name, value in self._db.execute("SELECT name, value FROM demo_metadata")
            }
            models = [
                r[0]
                for r in self._db.execute(
                    "SELECT DISTINCT model_sha256 FROM events WHERE model_sha256 IS NOT NULL"
                )
            ]
        return {
            "events_by_status": status,
            "predictions_by_decision": {str(k): v for k, v in decisions.items()},
            "events_by_evidence_tier": {str(k): v for k, v in tiers.items()},
            "counters": counters,
            "inference_ms": _percentiles(inference),
            "end_to_end_ms": _percentiles(e2e),
            "first_prediction_utc": window[0],
            "last_prediction_utc": window[1],
            "monitor_alarms": alarms,
            "model_sha256": models,
            "model_provenance": [
                metadata[f"model:{digest}"] for digest in models if f"model:{digest}" in metadata
            ],
            "last_replay": metadata.get("last_replay"),
            "reportable": False,
        }

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._db.execute(
                "SELECT publisher_sequence, received_at_utc, status, decision, reason,"
                " evidence_tier, inference_ms FROM events ORDER BY seq DESC LIMIT ?",
                (limit,),
            ).fetchall()
        keys = (
            "publisher_sequence",
            "received_at_utc",
            "status",
            "decision",
            "reason",
            "evidence_tier",
            "inference_ms",
        )
        return [dict(zip(keys, row, strict=True)) for row in rows]


def _percentiles(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, **{f"p{p}": None for p in PERCENTILES}}
    arr = np.asarray(values, dtype=float)
    return {"n": len(values), **{f"p{p}": float(np.percentile(arr, p)) for p in PERCENTILES}}
