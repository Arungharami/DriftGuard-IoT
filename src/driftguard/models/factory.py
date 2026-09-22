"""Estimator factory keyed by ``ModelConfig.name``.

Five reproduction baselines (M2), matching the reference paper's named model set:
Decision Tree, Random Forest, Bagging, DT/RF/MLP Stacking, LightGBM. The exact
per-model hyperparameters used in the paper could not be confirmed (IEEE Xplore full
text was inaccessible from this environment - see paper/methodology.md); every default
below is this project's own documented choice, overridable per-experiment via
``ModelConfig.params``, never presented as reproducing an unconfirmed paper setting.

The stacking ensemble's own architecture (which model is a base learner vs. the final/
meta estimator) is also not confirmed from the accessible abstract. "DT/RF/MLP
Stacking" is implemented as the conventional reading - DT and RF as base learners
feeding an MLP meta-learner - documented as an assumption, not a verified fact.
"""

from __future__ import annotations

from typing import Any

from lightgbm import LGBMClassifier
from sklearn.base import ClassifierMixin
from sklearn.ensemble import BaggingClassifier, RandomForestClassifier, StackingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier

from driftguard.config import ModelConfig

_SEED_IN_PARAMS_ERROR = "set the seed in the experiment config, not in model params"


def _reject_seed_in_params(params: dict[str, Any]) -> None:
    if "random_state" in params:
        raise ValueError(_SEED_IN_PARAMS_ERROR)


def _build_stacking(params: dict[str, Any], seed: int) -> StackingClassifier:
    remaining = dict(params)
    dt_params = remaining.pop("dt", {})
    rf_params = remaining.pop("rf", {})
    mlp_params = remaining.pop("mlp", {})
    cv = remaining.pop("cv", 5)
    for sub in (dt_params, rf_params, mlp_params):
        _reject_seed_in_params(sub)
    if remaining:
        raise ValueError(f"unknown stacking params: {sorted(remaining)}")

    estimators: list[tuple[str, ClassifierMixin]] = [
        ("dt", DecisionTreeClassifier(random_state=seed, **dt_params)),
        ("rf", RandomForestClassifier(random_state=seed, **rf_params)),
    ]
    final_estimator = MLPClassifier(random_state=seed, **mlp_params)
    return StackingClassifier(estimators=estimators, final_estimator=final_estimator, cv=cv)


def build_estimator(config: ModelConfig, seed: int) -> ClassifierMixin:
    _reject_seed_in_params(config.params)

    if config.name == "decision_tree":
        return DecisionTreeClassifier(random_state=seed, **config.params)
    if config.name == "random_forest":
        return RandomForestClassifier(random_state=seed, **config.params)
    if config.name == "bagging":
        # estimator=None lets scikit-learn default to a DecisionTreeClassifier, its own
        # documented default - not a paper-confirmed choice (see module docstring).
        return BaggingClassifier(random_state=seed, **config.params)
    if config.name == "stacking":
        return _build_stacking(config.params, seed)
    if config.name == "lightgbm":
        return LGBMClassifier(random_state=seed, **config.params)

    raise NotImplementedError(f"model {config.name!r} is not a registered ModelName")
