"""Preprocessing wrapped in a scikit-learn ``Pipeline``.

Keeping every stateful step inside one pipeline means ``fit`` can only ever see the data
it is given (the training partition), and the fitted preprocessing is persisted together
with the model it feeds.
"""

from __future__ import annotations

from collections.abc import Sequence

from sklearn.base import ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


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
) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocess", build_preprocessor(numeric_columns, categorical_columns)),
            ("model", estimator),
        ]
    )
