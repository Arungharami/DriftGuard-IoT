"""Deterministic synthetic network-flow generator.

The generated data only *resembles* the shape of IoT flow records (numeric volume/timing
features, a protocol column, a timestamp and a multi-class label). It has no relationship
to TON_IoT, WUSTL-IIOT-2021 or Edge-IIoTset and must never be reported as a research
result. It exists so that tests and CI can exercise the full pipeline without real data.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

SYNTHETIC_ATTR = "driftguard_synthetic"

NUMERIC_FEATURES: tuple[str, ...] = (
    "duration",
    "src_bytes",
    "dst_bytes",
    "src_pkts",
    "dst_pkts",
    "mean_iat",
)
CATEGORICAL_FEATURES: tuple[str, ...] = ("proto",)
PROTOCOLS: tuple[str, ...] = ("tcp", "udp", "icmp")
TIMESTAMP_COLUMN = "timestamp"
LABEL_COLUMN = "label"

DEFAULT_CLASS_PROPORTIONS: Mapping[str, float] = {
    "normal": 0.70,
    "dos": 0.15,
    "scan": 0.10,
    "injection": 0.05,
}


def generate_synthetic_flows(
    n_samples: int,
    seed: int,
    class_proportions: Mapping[str, float] = DEFAULT_CLASS_PROPORTIONS,
    drift_onset_fraction: float | None = None,
    drift_scale_multiplier: float = 1.0,
    drift_features: Sequence[str] = (),
) -> pd.DataFrame:
    """Generate a labelled, time-ordered synthetic flow table.

    Each class draws its numeric features from a log-normal distribution with a
    class-specific location, so classes are learnable but overlap. Rows are ordered by
    timestamp. When ``drift_onset_fraction`` is given, the listed numeric features are
    multiplied by ``drift_scale_multiplier`` for all rows at or after that fraction of the
    timeline (pure covariate shift: labels are generated the same way before and after).
    """
    if n_samples < len(class_proportions):
        raise ValueError("n_samples must be at least the number of classes")
    unknown = set(drift_features) - set(NUMERIC_FEATURES)
    if unknown:
        raise ValueError(f"drift_features must be numeric features, got {sorted(unknown)}")

    rng = np.random.default_rng(seed)
    classes = list(class_proportions)
    probs = np.asarray([class_proportions[c] for c in classes], dtype=float)
    probs = probs / probs.sum()

    # Guarantee every class appears at least once so stratified splits are possible.
    labels_idx = np.concatenate(
        [np.arange(len(classes)), rng.choice(len(classes), size=n_samples - len(classes), p=probs)]
    )
    rng.shuffle(labels_idx)

    # Class-specific log-normal locations: one row per class, one column per feature.
    class_locs = rng.normal(loc=3.0, scale=1.2, size=(len(classes), len(NUMERIC_FEATURES)))
    numeric = rng.lognormal(mean=class_locs[labels_idx], sigma=0.8)

    proto_probs = rng.dirichlet(np.ones(len(PROTOCOLS)), size=len(classes))
    proto_idx = np.array([rng.choice(len(PROTOCOLS), p=proto_probs[k]) for k in labels_idx])

    gaps = rng.exponential(scale=0.05, size=n_samples)
    timestamps = pd.Timestamp("2020-01-01T00:00:00Z") + pd.to_timedelta(np.cumsum(gaps), unit="s")

    df = pd.DataFrame(numeric, columns=list(NUMERIC_FEATURES))
    df.insert(0, TIMESTAMP_COLUMN, timestamps)
    df["proto"] = np.asarray(PROTOCOLS)[proto_idx]
    df[LABEL_COLUMN] = np.asarray(classes)[labels_idx]

    if drift_onset_fraction is not None:
        if not 0.0 < drift_onset_fraction < 1.0:
            raise ValueError("drift_onset_fraction must be in (0, 1)")
        onset = int(n_samples * drift_onset_fraction)
        cols = list(drift_features)
        df.loc[onset:, cols] = df.loc[onset:, cols] * drift_scale_multiplier

    df.attrs[SYNTHETIC_ATTR] = True
    return df
