"""All five M2 baselines: DT, RF, Bagging, DT/RF/MLP Stacking, LightGBM."""

from __future__ import annotations

import pandas as pd
import pytest
from sklearn.ensemble import BaggingClassifier, RandomForestClassifier, StackingClassifier
from sklearn.tree import DecisionTreeClassifier

from driftguard.config import ModelConfig
from driftguard.data.synthetic import LABEL_COLUMN, NUMERIC_FEATURES
from driftguard.models.factory import build_estimator
from driftguard.preprocessing.pipeline import build_pipeline
from driftguard.preprocessing.split import stratified_holdout

ALL_MODEL_NAMES = ["decision_tree", "random_forest", "bagging", "stacking", "lightgbm"]


@pytest.mark.parametrize("name", ALL_MODEL_NAMES)
def test_every_registered_model_builds_and_fits(name: str, synthetic_flows: pd.DataFrame) -> None:
    split = stratified_holdout(synthetic_flows, LABEL_COLUMN, test_size=0.3, seed=1)
    numeric = list(NUMERIC_FEATURES)
    params: dict = {"cv": 3, "dt": {}, "rf": {"n_estimators": 10}, "mlp": {"max_iter": 50}}
    config = ModelConfig(name=name, params=params if name == "stacking" else {})
    estimator = build_estimator(config, seed=0)
    pipe = build_pipeline(numeric, ["proto"], estimator)
    pipe.fit(split.train[[*numeric, "proto"]], split.train[LABEL_COLUMN])
    predictions = pipe.predict(split.test[[*numeric, "proto"]])
    assert len(predictions) == len(split.test)
    assert set(predictions) <= set(synthetic_flows[LABEL_COLUMN].unique())


@pytest.mark.parametrize("name", ALL_MODEL_NAMES)
def test_seed_must_not_be_set_in_top_level_model_params(name: str) -> None:
    with pytest.raises(ValueError, match="seed"):
        build_estimator(ModelConfig(name=name, params={"random_state": 1}), seed=0)


@pytest.mark.parametrize("name", ["dt", "rf", "mlp"])
def test_stacking_rejects_seed_in_sub_model_params(name: str) -> None:
    with pytest.raises(ValueError, match="seed"):
        build_estimator(ModelConfig(name="stacking", params={name: {"random_state": 1}}), seed=0)


def test_stacking_rejects_unknown_top_level_params() -> None:
    with pytest.raises(ValueError, match="unknown stacking params"):
        build_estimator(ModelConfig(name="stacking", params={"unknown_key": 1}), seed=0)


def test_same_seed_gives_identical_predictions() -> None:
    a = build_estimator(ModelConfig(name="random_forest", params={"n_estimators": 5}), seed=42)
    b = build_estimator(ModelConfig(name="random_forest", params={"n_estimators": 5}), seed=42)
    assert a.get_params()["random_state"] == b.get_params()["random_state"] == 42


def test_decision_tree_estimator_type() -> None:
    est = build_estimator(ModelConfig(name="decision_tree"), seed=0)
    assert isinstance(est, DecisionTreeClassifier)


def test_random_forest_estimator_type() -> None:
    est = build_estimator(ModelConfig(name="random_forest"), seed=0)
    assert isinstance(est, RandomForestClassifier)


def test_bagging_defaults_to_decision_tree_base_estimator() -> None:
    est = build_estimator(ModelConfig(name="bagging"), seed=0)
    assert isinstance(est, BaggingClassifier)
    # scikit-learn's own documented default when estimator=None - not asserted as a
    # reproduction of the reference paper's (unstated) choice.
    assert est.estimator is None


def test_stacking_uses_dt_and_rf_base_learners_with_mlp_meta() -> None:
    est = build_estimator(ModelConfig(name="stacking"), seed=0)
    assert isinstance(est, StackingClassifier)
    names = [name for name, _ in est.estimators]
    assert names == ["dt", "rf"]
    assert est.final_estimator.__class__.__name__ == "MLPClassifier"


def test_stacking_threads_the_seed_into_every_sub_model() -> None:
    est = build_estimator(ModelConfig(name="stacking"), seed=99)
    for _, sub in est.estimators:
        assert sub.get_params()["random_state"] == 99
    assert est.final_estimator.get_params()["random_state"] == 99
