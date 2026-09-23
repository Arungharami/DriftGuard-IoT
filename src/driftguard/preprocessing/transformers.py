"""Preprocessing transformers and the paper's proportional resampler.

Stateless transformers (``NumericCoercer``, ``CategoricalCanonicalizer``) learn nothing
from data. Stateful steps (``MutualInformationSelector``, ``ProportionalResampler``) learn
only from what ``fit`` receives. In the leakage-safe pipeline that is the training
partition, and the resampler runs at fit time only (imbalanced-learn ``Pipeline``
semantics).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE, SMOTENC
from imblearn.under_sampling import RandomUnderSampler
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_selection import mutual_info_classif


class NumericCoercer(BaseEstimator, TransformerMixin):  # type: ignore[misc]
    """Coerce columns to float; unparseable values become NaN. Stateless."""

    def __init__(self, columns: Sequence[str] = ()) -> None:
        self.columns = columns

    def fit(self, X: pd.DataFrame, y: Any = None) -> NumericCoercer:
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        out = X.copy()
        for c in self.columns:
            if c in out.columns:
                out[c] = pd.to_numeric(out[c], errors="coerce").astype(float)
        return out

    def get_feature_names_out(self, input_features: Any = None) -> np.ndarray:
        return np.asarray(input_features if input_features is not None else [], dtype=object)


def canonical_category(value: object) -> str:
    """Map numerically equal spellings ('0', '0.0', '0x0') to one token. Missing -> '__missing__'.

    This removes formatting artifacts. In Edge-IIoTset, '0' vs '0.0' in some columns encodes
    the label (verified 2026-09-22).
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "__missing__"
    text = str(value).strip()
    if text == "" or text.lower() in {"nan", "-"}:
        return "__missing__"
    try:
        number = float(int(text, 16)) if text.lower().startswith("0x") else float(text)
    except ValueError:
        return text
    return repr(number)


class CategoricalCanonicalizer(BaseEstimator, TransformerMixin):  # type: ignore[misc]
    """Apply ``canonical_category`` to categorical columns. Stateless."""

    def __init__(self, columns: Sequence[str] = ()) -> None:
        self.columns = columns

    def fit(self, X: pd.DataFrame, y: Any = None) -> CategoricalCanonicalizer:
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        out = X.copy()
        for c in self.columns:
            if c in out.columns:
                out[c] = out[c].map(canonical_category)
        return out


def _stratified_positions(y: np.ndarray, max_samples: int, seed: int) -> np.ndarray:
    if len(y) <= max_samples:
        return np.arange(len(y))
    rng = np.random.default_rng(seed)
    classes, counts = np.unique(y, return_counts=True)
    take = np.maximum(1, np.floor(counts / len(y) * max_samples).astype(int))
    parts = [
        rng.choice(np.flatnonzero(y == c), size=min(k, n), replace=False)
        for c, k, n in zip(classes, take, counts, strict=True)
    ]
    return np.sort(np.concatenate(parts))


class MutualInformationSelector(BaseEstimator, TransformerMixin):  # type: ignore[misc]
    """Keep features whose mutual information with y is >= ``threshold``.

    Scores come from whatever ``fit`` receives, so the protocol decides whether that is
    the training partition (leakage-safe) or the whole dataset (paper-faithful). With
    ``max_samples``, MI is estimated on a stratified subsample of the fit data only. If no
    feature reaches the threshold, the single best feature is kept and
    ``fallback_used_`` is set.
    """

    def __init__(
        self, threshold: float = 0.1, max_samples: int | None = None, random_state: int = 0
    ) -> None:
        self.threshold = threshold
        self.max_samples = max_samples
        self.random_state = random_state

    def fit(self, X: pd.DataFrame, y: Any) -> MutualInformationSelector:
        frame = X if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        y_arr = np.asarray(y)
        pos = (
            _stratified_positions(y_arr, self.max_samples, self.random_state)
            if self.max_samples
            else np.arange(len(y_arr))
        )
        values = frame.iloc[pos].to_numpy(dtype=float)
        scores = mutual_info_classif(values, y_arr[pos], random_state=self.random_state)
        self.feature_names_in_ = np.asarray(frame.columns, dtype=object)
        self.scores_ = dict(zip(map(str, frame.columns), map(float, scores), strict=True))
        mask = scores >= self.threshold
        self.fallback_used_ = not mask.any()
        if self.fallback_used_:
            mask[int(np.argmax(scores))] = True
        self.support_ = mask
        self.n_fit_rows_ = len(y_arr)
        self.n_score_rows_ = len(pos)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        frame = (
            X if isinstance(X, pd.DataFrame) else pd.DataFrame(X, columns=self.feature_names_in_)
        )
        return frame.loc[:, self.selected_features_]

    @property
    def selected_features_(self) -> list[str]:
        return [
            str(c) for c, keep in zip(self.feature_names_in_, self.support_, strict=True) if keep
        ]

    def get_feature_names_out(self, input_features: Any = None) -> np.ndarray:
        return np.asarray(self.selected_features_, dtype=object)


def proportional_targets(counts: pd.Series, total: int) -> dict[Any, int]:
    """Per-class targets that keep class proportions at ``total`` rows (floor, >= 1)."""
    n = int(counts.sum())
    return {k: max(1, int(np.floor(total * int(v) / n))) for k, v in counts.items()}


def proportional_resample(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    total: int,
    random_state: int,
    k_neighbors: int = 5,
    categorical_columns: Sequence[str] = (),
) -> tuple[pd.DataFrame, pd.Series, np.ndarray]:
    """The reference study's two-step resampling (Sec. III-B).

    SMOTE raises classes whose target exceeds their count, then RandomUnderSampler lowers
    classes whose target is below their count. Returns (X, y, synthetic_mask), where the
    mask marks rows created by SMOTE. Classes with fewer than two rows cannot be
    oversampled and keep their original count.
    """
    X = X.reset_index(drop=True)
    y = pd.Series(np.asarray(y), name=getattr(y, "name", None))
    counts = y.value_counts()
    targets = proportional_targets(counts, total)
    synthetic = np.zeros(len(y), dtype=bool)

    up = {k: t for k, t in targets.items() if t > counts[k] and counts[k] >= 2}
    if up:
        k = max(1, min(k_neighbors, min(int(counts[c]) for c in up) - 1))
        cat_idx = [X.columns.get_loc(c) for c in categorical_columns if c in X.columns]
        smote: SMOTE | SMOTENC = (
            SMOTENC(
                categorical_features=cat_idx,
                sampling_strategy=up,
                k_neighbors=k,
                random_state=random_state,
            )
            if cat_idx
            else SMOTE(sampling_strategy=up, k_neighbors=k, random_state=random_state)
        )
        n_before = len(y)
        X, y = smote.fit_resample(X, y)
        synthetic = np.concatenate([synthetic, np.ones(len(y) - n_before, dtype=bool)])

    counts = pd.Series(np.asarray(y)).value_counts()
    down = {k: t for k, t in targets.items() if t < counts[k]}
    if down:
        rus = RandomUnderSampler(sampling_strategy=down, random_state=random_state)
        X, y = rus.fit_resample(X, y)
        synthetic = synthetic[rus.sample_indices_]
    return X.reset_index(drop=True), pd.Series(np.asarray(y), name=y.name), synthetic


class ProportionalResampler(BaseEstimator):  # type: ignore[misc]
    """imbalanced-learn-compatible sampler around ``proportional_resample``.

    Inside an ``imblearn.pipeline.Pipeline`` it runs during ``fit`` only; prediction and
    scoring never resample.
    """

    def __init__(
        self,
        total: int | None = None,
        ratio: float | None = None,
        k_neighbors: int = 5,
        random_state: int = 0,
        categorical_prefix: str = "cat__",
    ) -> None:
        self.total = total
        self.ratio = ratio
        self.k_neighbors = k_neighbors
        self.random_state = random_state
        self.categorical_prefix = categorical_prefix

    def fit_resample(self, X: pd.DataFrame, y: Any) -> tuple[pd.DataFrame, pd.Series]:
        frame = X if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        total = self.total if self.total is not None else round((self.ratio or 1.0) * len(frame))
        cats = [c for c in frame.columns if str(c).startswith(self.categorical_prefix)]
        X_res, y_res, synthetic = proportional_resample(
            frame,
            pd.Series(np.asarray(y)),
            total=int(total),
            random_state=self.random_state,
            k_neighbors=self.k_neighbors,
            categorical_columns=cats,
        )
        self.n_input_rows_ = len(frame)
        self.n_output_rows_ = len(X_res)
        self.n_synthetic_rows_ = int(synthetic.sum())
        return X_res, y_res
