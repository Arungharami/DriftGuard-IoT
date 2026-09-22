"""Estimator factory for the five reference baselines.

Verified against the reference paper (Ismail et al. 2025, Sec. III-C, read 2026-09-22):
Decision Tree, Random Forest, Bagging, Stacking with DT and RF as base estimators and an
MLP as the final estimator, and LightGBM. The paper reports **no hyperparameters**, so
the defaults here are the library defaults (an assumption, recorded in every manifest),
overridable per model config. Seeds always come from the experiment config;
``random_state`` in model params is rejected so a run is reproducible from its manifest.
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
_STACKING_KEYS = frozenset({"dt", "rf", "mlp", "cv", "stack_method", "passthrough"})


def _reject_seed_in_params(params: dict[str, Any]) -> None:
    if "random_state" in params:
        raise ValueError(_SEED_IN_PARAMS_ERROR)


def _build_stacking(params: dict[str, Any], seed: int, n_jobs: int) -> StackingClassifier:
    unknown = set(params) - _STACKING_KEYS
    if unknown:
        raise ValueError(f"unknown stacking params: {sorted(unknown)}")
    dt_params = dict(params.get("dt") or {})
    rf_params = dict(params.get("rf") or {})
    mlp_params = dict(params.get("mlp") or {})
    for sub in (dt_params, rf_params, mlp_params):
        _reject_seed_in_params(sub)
    rf_params.setdefault("n_jobs", n_jobs)
    extra = {k: params[k] for k in ("stack_method", "passthrough") if k in params}
    return StackingClassifier(
        estimators=[
            ("dt", DecisionTreeClassifier(random_state=seed, **dt_params)),
            ("rf", RandomForestClassifier(random_state=seed, **rf_params)),
        ],
        final_estimator=MLPClassifier(random_state=seed, **mlp_params),
        cv=params.get("cv", 5),
        n_jobs=n_jobs,
        **extra,
    )


def build_estimator(config: ModelConfig, seed: int, n_jobs: int = 1) -> ClassifierMixin:
    params = dict(config.params)
    _reject_seed_in_params(params)

    if config.name == "decision_tree":
        return DecisionTreeClassifier(random_state=seed, **params)
    if config.name == "random_forest":
        params.setdefault("n_jobs", n_jobs)
        return RandomForestClassifier(random_state=seed, **params)
    if config.name == "bagging":
        # estimator=None: scikit-learn's default base estimator is a DecisionTreeClassifier.
        # The paper does not state Bagging's base estimator.
        params.setdefault("n_jobs", n_jobs)
        return BaggingClassifier(random_state=seed, **params)
    if config.name == "stacking":
        return _build_stacking(params, seed, n_jobs)
    if config.name == "lightgbm":
        params.setdefault("n_jobs", n_jobs)
        params.setdefault("verbose", -1)  # silence stdout logging; not a modelling choice
        params.setdefault("deterministic", True)
        params.setdefault("force_row_wise", True)
        return LGBMClassifier(random_state=seed, **params)
    raise NotImplementedError(f"model {config.name!r} is not a registered ModelName")


def describe_params(estimator: ClassifierMixin) -> dict[str, Any]:
    """JSON-safe snapshot of an estimator's full parameter set, for the run manifest."""
    out: dict[str, Any] = {}
    for key, value in sorted(estimator.get_params(deep=True).items()):
        if isinstance(value, bool | int | float | str) or value is None:
            out[key] = value
        elif isinstance(value, (list, tuple)) and all(
            isinstance(v, bool | int | float | str) for v in value
        ):
            out[key] = list(value)
        else:
            out[key] = type(value).__name__
    return out
