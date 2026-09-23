from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from driftguard.config import (
    DatasetConfig,
    ExperimentConfig,
    SyntheticConfig,
    load_experiment_config,
)

EXPERIMENT_CONFIGS = sorted((Path(__file__).parent.parent / "configs/experiments").glob("*.yaml"))


@pytest.mark.parametrize("path", EXPERIMENT_CONFIGS, ids=lambda p: p.name)
def test_all_committed_experiment_configs_validate(path: Path) -> None:
    config = load_experiment_config(path)
    assert config.models


def test_canonical_hash_is_stable_and_sensitive(repo_root: Path) -> None:
    path = repo_root / "configs/experiments/smoke-synthetic.yaml"
    a = load_experiment_config(path)
    b = load_experiment_config(path)
    assert a.canonical_hash() == b.canonical_hash()
    changed = ExperimentConfig.model_validate({**a.model_dump(), "seed": a.seed + 1})
    assert changed.canonical_hash() != a.canonical_hash()


def test_unknown_keys_are_rejected() -> None:
    with pytest.raises(ValidationError, match="Extra inputs"):
        DatasetConfig.model_validate(
            {"name": "x", "kind": "ton_iot", "label_column": "y", "unexpected": 1}
        )


def test_synthetic_block_required_iff_synthetic() -> None:
    with pytest.raises(ValidationError, match="synthetic"):
        DatasetConfig.model_validate({"name": "x", "kind": "synthetic", "label_column": "y"})


def test_label_cannot_be_dropped() -> None:
    synthetic = {"n_samples": 100, "class_proportions": {"a": 0.5, "b": 0.5}}
    with pytest.raises(ValidationError, match="label_column"):
        DatasetConfig.model_validate(
            {
                "name": "x",
                "kind": "synthetic",
                "label_column": "y",
                "drop_columns": ["y"],
                "synthetic": synthetic,
            }
        )


def test_registry_datasets_take_label_from_card() -> None:
    with pytest.raises(ValidationError, match="dataset card"):
        DatasetConfig.model_validate({"name": "x", "kind": "ton_iot", "label_column": "y"})
    assert DatasetConfig.model_validate({"name": "x", "kind": "ton_iot"}).is_registry


@pytest.mark.parametrize("proportions", [{"a": 1.0}, {"a": 0.5, "b": 0.4}, {"a": 1.2, "b": -0.2}])
def test_bad_class_proportions(proportions: dict[str, float]) -> None:
    with pytest.raises(ValidationError):
        SyntheticConfig(n_samples=100, class_proportions=proportions)


def test_chronological_split_requires_timestamp(tmp_path: Path) -> None:
    (tmp_path / "ds.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "x",
                "kind": "synthetic",
                "label_column": "label",
                "synthetic": {"n_samples": 100, "class_proportions": {"a": 0.5, "b": 0.5}},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "m.yaml").write_text("name: decision_tree\n", encoding="utf-8")
    (tmp_path / "exp.yaml").write_text(
        "name: bad\nseed: 1\ndataset: ds.yaml\nmodels: [m.yaml]\n"
        "split: {strategy: chronological, test_size: 0.2}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="timestamp_column"):
        load_experiment_config(tmp_path / "exp.yaml")


def test_inline_dataset_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "exp.yaml").write_text(
        "name: bad\nseed: 1\ndataset: {name: x}\nmodels: []\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="relative path"):
        load_experiment_config(tmp_path / "exp.yaml")
