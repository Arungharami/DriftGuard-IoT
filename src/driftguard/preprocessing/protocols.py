"""The two preprocessing protocols.

``leakage_safe`` (this project's protocol):
    deduplicate on model-visible columns -> feature-group stratified split -> [fit on train only:
    numeric coercion, category canonicalisation, median imputation, ordinal encoding,
    zero-variance removal, MI selection, optional proportional resampling] -> model.
    Everything stateful lives in one persisted ``imblearn`` pipeline.

``paper_faithful`` (reproduction of Ismail et al. 2025, Sec. III):
    numeric columns -> MI selection on the *full* dataset -> proportional SMOTE +
    undersampling of the *full* dataset -> 70:30 split -> model. It is kept only to
    measure the effect of that ordering. Its outputs carry the leakage risks listed in
    ``paper_protocol.PAPER_LEAKAGE_RISKS`` and are never reportable as leakage-safe results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.base import ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OrdinalEncoder

from driftguard.config import PreprocessingConfig
from driftguard.preprocessing.paper_protocol import (
    PAPER_LEAKAGE_RISKS,
    RESAMPLE_RANDOM_STATE,
    PaperDatasetProtocol,
)
from driftguard.preprocessing.transformers import (
    CategoricalCanonicalizer,
    MutualInformationSelector,
    NumericCoercer,
    ProportionalResampler,
    proportional_resample,
)


@dataclass
class PreparedData:
    """Train/test partitions plus provenance of how they were produced."""

    protocol: str
    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    numeric_columns: list[str]
    categorical_columns: list[str]
    details: dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------------------------------- leakage-safe


def prepare_leakage_safe(
    df: pd.DataFrame,
    *,
    target: str,
    numeric_columns: list[str],
    categorical_columns: list[str],
    test_size: float,
    seed: int,
    deduplicate: bool,
) -> PreparedData:
    """Deduplicate, then split whole feature-identical groups. Nothing is fitted here.

    Rows sharing one model-visible feature vector (after exact deduplication, these are
    the conflicting-label rows) go to the same partition, so no test feature vector is
    ever seen in training. Groups are stratified by their majority label.
    """
    features = numeric_columns + categorical_columns
    visible = df[[*features, target]]
    n_in = len(visible)
    if deduplicate:
        visible = visible.drop_duplicates(keep="first")
    n_dedup = n_in - len(visible)

    # A 64-bit hash collision can only merge groups (keeping more rows together), never
    # separate identical vectors, so it cannot introduce cross-partition leakage.
    keys = pd.util.hash_pandas_object(visible[features], index=False).to_numpy()
    tally = (
        pd.DataFrame({"group": keys, "label": visible[target].to_numpy()})
        .value_counts(dropna=False)
        .rename("n")
        .reset_index()
    )
    tally["order"] = tally["label"].astype(str)
    tally = tally.sort_values(["group", "n", "order"], ascending=[True, False, True])
    majority = tally.drop_duplicates("group").set_index("group")["label"]
    group_sizes = tally.groupby("group")["n"].agg(["size", "sum"])
    conflicting = group_sizes[group_sizes["size"] > 1]

    stratify = majority if (majority.value_counts() >= 2).all() else None
    _, test_groups = train_test_split(
        majority.index.to_numpy(),
        test_size=test_size,
        random_state=seed,
        stratify=stratify,
        shuffle=True,
    )
    in_test = np.isin(keys, test_groups)
    train, test = visible[~in_test], visible[in_test]
    # Guard: zero by construction.
    cross = train[features].merge(test[features].drop_duplicates(), how="inner", on=features)
    if len(cross):
        raise RuntimeError("feature-group split produced cross-partition feature vectors")
    return PreparedData(
        protocol="leakage_safe",
        X_train=train[features],
        X_test=test[features],
        y_train=train[target],
        y_test=test[target],
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
        details={
            "rows_in": n_in,
            "duplicates_removed": n_dedup,
            "split_strategy": "feature_group_stratified_holdout",
            "stratified": stratify is not None,
            "feature_groups": len(majority),
            "conflicting_label_groups": len(conflicting),
            "conflicting_label_rows": int(conflicting["sum"].sum()),
            "cross_split_feature_duplicates": len(cross),
            "test_contains_synthetic_rows": False,
            "fit_scope": "train partition only",
        },
    )


def build_leakage_safe_pipeline(
    numeric_columns: list[str],
    categorical_columns: list[str],
    estimator: ClassifierMixin,
    cfg: PreprocessingConfig,
    seed: int,
) -> ImbPipeline:
    encode = ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="median", keep_empty_features=True), numeric_columns),
            (
                "cat",
                OrdinalEncoder(
                    handle_unknown="use_encoded_value", unknown_value=-1, encoded_missing_value=-2
                ),
                categorical_columns,
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    ).set_output(transform="pandas")
    steps: list[tuple[str, Any]] = [
        ("coerce", NumericCoercer(numeric_columns)),
        ("canonicalize", CategoricalCanonicalizer(categorical_columns)),
        ("encode", encode),
        ("variance", VarianceThreshold(0.0).set_output(transform="pandas")),
        (
            "mi",
            MutualInformationSelector(
                threshold=cfg.mi_threshold, max_samples=cfg.mi_max_samples, random_state=seed
            ),
        ),
    ]
    rs = cfg.resampling
    if rs.strategy == "paper_proportional":
        steps.append(
            (
                "resample",
                ProportionalResampler(
                    total=rs.total,
                    ratio=rs.ratio,
                    k_neighbors=rs.k_neighbors,
                    random_state=rs.random_state if rs.random_state is not None else seed,
                ),
            )
        )
    steps.append(("model", estimator))
    return ImbPipeline(steps)


# --------------------------------------------------------------------------- paper-faithful


def paper_mi_universe(df: pd.DataFrame, protocol: PaperDatasetProtocol) -> list[str]:
    """Numeric-dtype columns minus the paper's pre-MI drops and the target (see Figs. 2-4)."""
    excluded = {*protocol.pre_mi_drop, protocol.target_column}
    return [c for c in df.select_dtypes(include="number").columns if c not in excluded]


def prepare_paper_faithful(
    df: pd.DataFrame,
    *,
    protocol: PaperDatasetProtocol,
    cfg: PreprocessingConfig,
    test_size: float,
    seed: int,
) -> PreparedData:
    """Reproduce Sec. III: MI on all rows, resample all rows, then split (leaky by design)."""
    target = protocol.target_column
    universe = paper_mi_universe(df, protocol)
    X = df[universe].fillna(0.0)
    y = df[target]

    selector = MutualInformationSelector(
        threshold=cfg.mi_threshold,
        max_samples=cfg.mi_max_samples,
        random_state=RESAMPLE_RANDOM_STATE,
    ).fit(X, y)
    selected = selector.selected_features_
    X_sel = X[selected]

    rs = cfg.resampling
    synthetic = np.zeros(len(X_sel), dtype=bool)
    if rs.strategy == "paper_proportional":
        total = rs.total if rs.total is not None else round((rs.ratio or 1.0) * len(X_sel))
        X_sel, y, synthetic = proportional_resample(
            X_sel,
            y,
            total=int(total),
            random_state=rs.random_state if rs.random_state is not None else RESAMPLE_RANDOM_STATE,
            k_neighbors=rs.k_neighbors,
        )
    else:
        X_sel, y = X_sel.reset_index(drop=True), y.reset_index(drop=True)

    positions = np.arange(len(y))
    tr, te = train_test_split(positions, test_size=test_size, random_state=seed, shuffle=True)
    reported = set(protocol.reported_mi_removed)
    computed_removed = sorted(set(universe) - set(selected))
    return PreparedData(
        protocol="paper_faithful",
        X_train=X_sel.iloc[tr],
        X_test=X_sel.iloc[te],
        y_train=y.iloc[tr],
        y_test=y.iloc[te],
        numeric_columns=selected,
        categorical_columns=[],
        details={
            "rows_in": len(df),
            "rows_after_resampling": len(y),
            "mi_universe": universe,
            "mi_scores_full_data": selector.scores_,
            "selected_features": selected,
            "computed_mi_removed": computed_removed,
            "paper_reported_mi_removed": sorted(reported),
            "agreement_with_paper_removed": sorted(reported & set(computed_removed)),
            "synthetic_rows_total": int(synthetic.sum()),
            "synthetic_rows_in_test": int(synthetic[te].sum()),
            "test_contains_synthetic_rows": bool(synthetic[te].any()),
            "fit_scope": "MI and resampling fitted on the FULL dataset before the split",
            "leakage_risks": list(PAPER_LEAKAGE_RISKS),
        },
    )


def build_paper_faithful_pipeline(features: list[str], estimator: ClassifierMixin) -> Pipeline:
    """Column selection + model. The paper applies no further fitted preprocessing."""
    select = FunctionTransformer(
        _select_and_fill, kw_args={"columns": list(features)}, feature_names_out="one-to-one"
    )
    return Pipeline([("select", select), ("model", estimator)])


def _select_and_fill(X: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return X[columns].fillna(0.0)
