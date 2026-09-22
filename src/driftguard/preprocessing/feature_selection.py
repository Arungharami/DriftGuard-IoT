"""Train-only mutual-information feature selection (docs/scientific-protocol.md §3.2-3.3).

``SelectKBest`` is a standard scikit-learn transformer: its ``fit`` computes MI scores
from whatever data it is given and its ``transform`` only applies the resulting column
mask. Placed inside a ``Pipeline`` that is itself fit only on the training partition
(the existing, tested split-before-fit contract - see tests/test_leakage_safety.py),
this guarantees the MI scores themselves are computed from training data only: the
selector never sees the test partition until ``transform`` at evaluation time, and
``transform`` does not recompute scores.
"""

from __future__ import annotations

from functools import partial

from sklearn.feature_selection import SelectKBest, mutual_info_classif

from driftguard.config import FeatureSelectionConfig


def build_feature_selector(config: FeatureSelectionConfig, seed: int) -> SelectKBest | None:
    """Returns a fittable selector, or ``None`` when feature selection is disabled.

    ``k`` defaults to ``"all"`` (score every feature but drop none) when not set, so
    enabling feature selection without a ``k`` reports MI scores without changing the
    feature set - useful for inspection before committing to a cut.
    """
    if not config.enabled:
        return None
    scorer = partial(mutual_info_classif, random_state=seed)
    return SelectKBest(score_func=scorer, k=config.k if config.k is not None else "all")
