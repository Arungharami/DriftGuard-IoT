"""Fitted-pipeline persistence (M2 exit criterion: "persisted pipelines")."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from driftguard.config import ModelConfig
from driftguard.data.synthetic import LABEL_COLUMN, NUMERIC_FEATURES
from driftguard.models.factory import build_estimator
from driftguard.models.persistence import load_pipeline, save_pipeline
from driftguard.preprocessing.pipeline import build_pipeline
from driftguard.preprocessing.split import stratified_holdout


def _fit_pipeline(synthetic_flows: pd.DataFrame):
    split = stratified_holdout(synthetic_flows, LABEL_COLUMN, test_size=0.3, seed=1)
    numeric = list(NUMERIC_FEATURES)
    estimator = build_estimator(ModelConfig(name="decision_tree", params={"max_depth": 6}), seed=0)
    pipe = build_pipeline(numeric, ["proto"], estimator)
    pipe.fit(split.train[[*numeric, "proto"]], split.train[LABEL_COLUMN])
    return pipe, split.test[[*numeric, "proto"]]


def test_save_pipeline_returns_the_real_file_sha256(
    tmp_path: Path, synthetic_flows: pd.DataFrame
) -> None:
    pipe, _ = _fit_pipeline(synthetic_flows)
    path = tmp_path / "pipeline.joblib"
    digest = save_pipeline(pipe, path)
    assert digest == hashlib.sha256(path.read_bytes()).hexdigest()


def test_loaded_pipeline_predicts_identically_to_the_original(
    tmp_path: Path, synthetic_flows: pd.DataFrame
) -> None:
    pipe, x_test = _fit_pipeline(synthetic_flows)
    path = tmp_path / "pipeline.joblib"
    save_pipeline(pipe, path)
    loaded = load_pipeline(path)
    np.testing.assert_array_equal(pipe.predict(x_test), loaded.predict(x_test))


def test_save_pipeline_creates_parent_directories(
    tmp_path: Path, synthetic_flows: pd.DataFrame
) -> None:
    pipe, _ = _fit_pipeline(synthetic_flows)
    path = tmp_path / "nested" / "dir" / "pipeline.joblib"
    save_pipeline(pipe, path)
    assert path.exists()
