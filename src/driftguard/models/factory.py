"""Estimator factory keyed by ``ModelConfig.name``.

M0 implements only the Decision Tree, which the smoke test needs. The remaining
baselines are registered names in the config schema and are implemented in M2.
"""

from __future__ import annotations

from sklearn.base import ClassifierMixin
from sklearn.tree import DecisionTreeClassifier

from driftguard.config import ModelConfig


def build_estimator(config: ModelConfig, seed: int) -> ClassifierMixin:
    if config.name == "decision_tree":
        if "random_state" in config.params:
            raise ValueError("set the seed in the experiment config, not in model params")
        return DecisionTreeClassifier(random_state=seed, **config.params)
    raise NotImplementedError(f"model {config.name!r} is scheduled for milestone M2")
