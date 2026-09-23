"""Fresh-process resource measurement of a trusted local inference bundle."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def benchmark_bundle(bundle: Path) -> dict[str, Any]:
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    result = subprocess.run(  # noqa: S603 - fixed module argv, no shell
        [sys.executable, "-m", "driftguard.benchmark.isolated", str(bundle.resolve())],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )
    return json.loads(result.stdout)  # type: ignore[no-any-return]


def _worker(bundle: Path) -> dict[str, Any]:
    import platform
    import resource
    import time

    import numpy as np
    import pandas as pd

    from driftguard.m5.evaluation import benchmark_predict
    from driftguard.models.persistence import load_verified_pipeline

    meta = json.loads((bundle / "bundle.json").read_text())
    started = time.perf_counter()
    model = load_verified_pipeline(bundle / "pipeline.joblib", meta["sha256"])
    cold_load = time.perf_counter() - started
    features = meta["features"]
    # Public benchmark inputs contain no captured network fields/rows.
    sample = {name: 0.0 if name in meta["numeric_features"] else "unknown" for name in features}
    frame = pd.DataFrame([sample] * 32)
    timings = benchmark_predict(lambda _: model.predict(frame), np.zeros((32, 1)))
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    timings.update(
        {
            "peak_rss_bytes": int(rss if sys.platform == "darwin" else rss * 1024),
            "peak_rss": int(rss if sys.platform == "darwin" else rss * 1024),
            "peak_rss_note": "fresh process high-water RSS includes imports/load/inference",
            "model_size_bytes": (bundle / "pipeline.joblib").stat().st_size,
            "cold_load_seconds": cold_load,
            "platform": platform.platform(),
            "threads": 1,
            "input": "32 generated schema-only rows, not representative traffic",
        }
    )
    return timings


if __name__ == "__main__":
    print(json.dumps(_worker(Path(sys.argv[1])), allow_nan=False))
