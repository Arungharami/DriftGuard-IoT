"""Preprocessing wrapped in a single pipeline.

Keeping every stateful step (encoding, scaling, feature selection, resampling) inside
one pipeline means ``fit`` can only ever see the data it is given (the training
partition - docs/scientific-protocol.md §3.2-3.3), and the fitted preprocessing is
persisted together with the model it feeds.

Adding a resampling step requires ``imblearn.pipeline.Pipeline`` in place of
``sklearn.pipeline.Pipeline``: only imblearn's version runs resampling during ``.fit``
and skips it during ``.transform``/``.predict``, which is what makes a resampler safe to
place in a pipeline at all (see preprocessing/resampling.py). When no resampler is
configured, a plain sklearn ``Pipeline`` is used, unchanged from M0/M1.
"""

from __future__ import annotations

from collections.abc import Sequence

from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.base import ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.feature_selection import SelectKBest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from driftguard.config import PreprocessingConfig
from driftguard.preprocessing.feature_selection import build_feature_selector
from driftguard.preprocessing.resampling import Resampler, build_resampler


def build_preprocessor(
    numeric_columns: Sequence[str], categorical_columns: Sequence[str]
) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), list(numeric_columns)),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                list(categorical_columns),
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def build_pipeline(
    numeric_columns: Sequence[str],
    categorical_columns: Sequence[str],
    estimator: ClassifierMixin,
    feature_selector: SelectKBest | None = None,
    resampler: Resampler | None = None,
) -> Pipeline | ImbPipeline:
    """Build the full preprocess -> [select] -> [resample] -> model pipeline.

    Order is fixed: encode/scale first (mutual information and every resampler here
    need numeric input), then feature selection (so a resampler only ever sees the
    already-selected feature set, keeping synthetic minority samples consistent with
    what the model actually trains on), then resampling, then the estimator. Returns a
    plain ``sklearn.pipeline.Pipeline`` when no resampler is given (byte-for-byte the
    M0/M1 pipeline shape) and an ``imblearn.pipeline.Pipeline`` only when one is.
    """
    steps: list[tuple[str, object]] = [
        ("preprocess", build_preprocessor(numeric_columns, categorical_columns))
    ]
    if feature_selector is not None:
        steps.append(("select", feature_selector))
    if resampler is not None:
        steps.append(("resample", resampler))
        steps.append(("model", estimator))
        return ImbPipeline(steps=steps)

    steps.append(("model", estimator))
    return Pipeline(steps=steps)


def build_pipeline_from_config(
    numeric_columns: Sequence[str],
    categorical_columns: Sequence[str],
    estimator: ClassifierMixin,
    preprocessing: PreprocessingConfig | None,
    seed: int,
) -> Pipeline | ImbPipeline:
    """``build_pipeline`` plus resolving ``feature_selector``/``resampler`` from config.

    ``preprocessing=None`` (every M0/M1 experiment config) is exactly "no feature
    selection, no resampling" - the same pipeline shape those configs always produced.
    """
    selector = (
        build_feature_selector(preprocessing.feature_selection, seed) if preprocessing else None
    )
    resampler = build_resampler(preprocessing.resampling, seed) if preprocessing else None
    return build_pipeline(numeric_columns, categorical_columns, estimator, selector, resampler)
