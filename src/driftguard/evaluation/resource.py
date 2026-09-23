"""Minimal resource metrics: training time and serialized model size.

The reference paper reports Model Size and Training Time alongside its classification
metrics, so both are captured here for RQ1 comparability. This is intentionally
narrow: peak RSS, CPU time, and latency/throughput percentiles are a separate,
larger measurement effort scheduled for M6 (docs/milestones.md) and are not
implemented here.
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Any


def timed_fit(pipeline: Any, x_train: Any, y_train: Any) -> float:
    """Fit ``pipeline`` in place and return the wall-clock training time in seconds."""
    start = time.perf_counter()
    pipeline.fit(x_train, y_train)
    return time.perf_counter() - start


def serialized_size_bytes(pipeline: Any) -> int:
    """Size of the fitted pipeline serialized with joblib, in bytes.

    Writes to a temporary file rather than estimating in memory, so the reported size
    matches exactly what ``driftguard.models.persistence.save_pipeline`` would write.
    """
    import joblib

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pipeline.joblib"
        joblib.dump(pipeline, path)
        return path.stat().st_size
