"""Train-only class-imbalance handling (docs/scientific-protocol.md §3.2-3.3).

Resamplers from ``imbalanced-learn`` are only safe to place in a pipeline when that
pipeline is ``imblearn.pipeline.Pipeline`` (see preprocessing/pipeline.py): its
``fit_resample`` contract runs resampling steps during ``.fit`` only, and skips them
entirely during ``.transform``/``.predict``, so test-time rows are never resampled or
used to influence a resampler's fitted state. A plain ``sklearn.pipeline.Pipeline``
does not implement this and must never be used with a resampling step.
"""

from __future__ import annotations

from typing import TypeAlias, cast

from imblearn.combine import SMOTETomek
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler

from driftguard.config import ResamplingConfig

Resampler: TypeAlias = SMOTE | RandomUnderSampler | SMOTETomek


def build_resampler(config: ResamplingConfig, seed: int) -> Resampler | None:
    if config.strategy == "none":
        return None
    if config.strategy == "smote":
        return cast(
            "Resampler",
            SMOTE(
                random_state=seed,
                sampling_strategy=config.sampling_strategy,
                k_neighbors=config.k_neighbors,
            ),
        )
    if config.strategy == "random_undersample":
        return cast(
            "Resampler",
            RandomUnderSampler(random_state=seed, sampling_strategy=config.sampling_strategy),
        )
    if config.strategy == "smote_then_undersample":
        # SMOTETomek: SMOTE to oversample the minority class, then Tomek-link removal to
        # clean the resulting boundary - a single train-only step rather than two
        # sequential pipeline steps, so there is one resampler to reason about and test.
        smote = SMOTE(
            random_state=seed,
            sampling_strategy=config.sampling_strategy,
            k_neighbors=config.k_neighbors,
        )
        return cast("Resampler", SMOTETomek(random_state=seed, smote=smote))
    raise NotImplementedError(f"resampling strategy {config.strategy!r} is not registered")
