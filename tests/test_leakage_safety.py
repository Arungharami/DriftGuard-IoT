"""Guards for the split-before-fit protocol (docs/scientific-protocol.md §3)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.tree import DecisionTreeClassifier

from driftguard.data.synthetic import LABEL_COLUMN, NUMERIC_FEATURES, TIMESTAMP_COLUMN
from driftguard.preprocessing.pipeline import build_pipeline
from driftguard.preprocessing.split import Split, chronological_holdout, stratified_holdout


def test_stratified_holdout_is_disjoint_and_complete(synthetic_flows: pd.DataFrame) -> None:
    split = stratified_holdout(synthetic_flows, LABEL_COLUMN, test_size=0.25, seed=0)
    assert split.train.index.intersection(split.test.index).empty
    assert len(split.train) + len(split.test) == len(synthetic_flows)
    # Stratification keeps every class in both partitions.
    assert set(split.test[LABEL_COLUMN]) == set(synthetic_flows[LABEL_COLUMN])


def test_chronological_holdout_never_trains_on_the_future(synthetic_flows: pd.DataFrame) -> None:
    split = chronological_holdout(synthetic_flows, TIMESTAMP_COLUMN, test_size=0.3)
    assert split.train[TIMESTAMP_COLUMN].max() < split.test[TIMESTAMP_COLUMN].min()


def test_chronological_holdout_puts_timestamp_ties_in_test() -> None:
    df = pd.DataFrame({"t": [1, 2, 2, 2, 3], "y": list("aabab")})
    split = chronological_holdout(df, "t", test_size=0.5)
    assert split.train["t"].max() < split.test["t"].min()
    assert (split.test["t"] == 2).sum() == 3


def test_split_rejects_overlap(synthetic_flows: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="overlap"):
        Split(train=synthetic_flows.iloc[:10], test=synthetic_flows.iloc[5:15])


def test_scaler_statistics_come_from_train_only(synthetic_flows: pd.DataFrame) -> None:
    split = stratified_holdout(synthetic_flows, LABEL_COLUMN, test_size=0.3, seed=1)
    numeric = list(NUMERIC_FEATURES)
    pipe = build_pipeline(numeric, ["proto"], DecisionTreeClassifier(random_state=0))
    pipe.fit(split.train[[*numeric, "proto"]], split.train[LABEL_COLUMN])

    scaler = pipe.named_steps["preprocess"].named_transformers_["numeric"]
    np.testing.assert_allclose(scaler.mean_, split.train[numeric].mean().to_numpy())
    assert not np.allclose(scaler.mean_, synthetic_flows[numeric].mean().to_numpy())


def test_unseen_test_category_does_not_break_inference(synthetic_flows: pd.DataFrame) -> None:
    split = stratified_holdout(synthetic_flows, LABEL_COLUMN, test_size=0.3, seed=1)
    numeric = list(NUMERIC_FEATURES)
    pipe = build_pipeline(numeric, ["proto"], DecisionTreeClassifier(random_state=0))
    pipe.fit(split.train[[*numeric, "proto"]], split.train[LABEL_COLUMN])
    test = split.test[[*numeric, "proto"]].copy()
    test["proto"] = "never-seen"
    assert len(pipe.predict(test)) == len(test)
