"""Evaluate alarms against independently specified change windows, never inferred labels."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import pairwise
from typing import Any


def assess_alarms(
    alarms: Sequence[float],
    changes: Sequence[float],
    *,
    horizon: float,
    stream_start: float,
    stream_end: float,
) -> dict[str, Any]:
    import math

    if (
        not all(math.isfinite(v) for v in [*alarms, *changes, horizon, stream_start, stream_end])
        or horizon <= 0
        or stream_end <= stream_start
        or list(changes) != sorted(set(changes))
        or any(b - a <= horizon for a, b in pairwise(changes))
        or any(t < stream_start or t > stream_end for t in [*alarms, *changes])
    ):
        raise ValueError("invalid or overlapping change windows")
    delays = [min((a - c for a in alarms if c <= a <= c + horizon), default=None) for c in changes]
    false = sum(not any(c <= a <= c + horizon for c in changes) for a in alarms)
    return {
        "delays": delays,
        "missed_changes": sum(v is None for v in delays),
        "false_alarm_count": false,
        "false_alarms_per_time_unit": false / (stream_end - stream_start),
        "horizon": horizon,
        "truth_source": "externally supplied change windows",
    }
