"""Typed experiment configuration.

An experiment YAML file references one dataset config and one or more model configs by
path (relative to the experiment file). ``load_experiment_config`` resolves those
references and validates the combined result, so every run is described by a single,
fully-specified ``ExperimentConfig`` whose canonical hash is recorded in the run manifest.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DatasetKind = Literal["synthetic", "ton_iot", "wustl_iiot_2021", "edge_iiotset"]
ModelName = Literal["decision_tree", "random_forest", "bagging", "stacking", "lightgbm"]
SplitStrategy = Literal["stratified_holdout", "chronological"]

# "reference" = best-effort reproduction of the settings confirmed in the reference
# paper's abstract (mutual-information feature selection; everything else the abstract
# does not state is left at this pipeline's own documented default, never guessed as a
# paper fact - see paper/methodology.md). "improved" = DriftGuard-IoT's own
# leakage-hardened pipeline, free to add steps (e.g. resampling, stricter duplicate
# exclusion) the reference paper may not use.
PreprocessingKind = Literal["reference", "improved"]
ResamplingStrategy = Literal["none", "smote", "random_undersample", "smote_then_undersample"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SyntheticDriftConfig(_Strict):
    """Covariate shift injected into synthetic data from ``onset_fraction`` onwards."""

    onset_fraction: float = Field(gt=0.0, lt=1.0)
    scale_multiplier: float = Field(gt=0.0)
    features: list[str] = Field(min_length=1)


class SyntheticConfig(_Strict):
    n_samples: int = Field(ge=50, le=5_000_000)
    class_proportions: dict[str, float]
    drift: SyntheticDriftConfig | None = None

    @field_validator("class_proportions")
    @classmethod
    def _proportions_valid(cls, value: dict[str, float]) -> dict[str, float]:
        if len(value) < 2:
            raise ValueError("at least two classes are required")
        if any(p <= 0 for p in value.values()):
            raise ValueError("class proportions must be positive")
        if not math.isclose(sum(value.values()), 1.0, abs_tol=1e-6):
            raise ValueError("class proportions must sum to 1")
        return value


class DatasetConfig(_Strict):
    name: str
    kind: DatasetKind
    label_column: str
    timestamp_column: str | None = None
    categorical_columns: list[str] = Field(default_factory=list)
    drop_columns: list[str] = Field(default_factory=list)
    synthetic: SyntheticConfig | None = None

    @model_validator(mode="after")
    def _synthetic_block_matches_kind(self) -> DatasetConfig:
        if (self.kind == "synthetic") != (self.synthetic is not None):
            raise ValueError("a `synthetic` block is required iff kind == 'synthetic'")
        if self.label_column in self.drop_columns:
            raise ValueError("label_column cannot also be dropped")
        return self


class ModelConfig(_Strict):
    name: ModelName
    params: dict[str, Any] = Field(default_factory=dict)


class SplitConfig(_Strict):
    strategy: SplitStrategy
    test_size: float = Field(gt=0.0, lt=1.0)


class FeatureSelectionConfig(_Strict):
    """Train-only mutual-information feature selection (docs/scientific-protocol.md §3.2-3.3)."""

    enabled: bool = False
    k: int | None = Field(default=None, ge=1, description="Top-k features by MI; None keeps all")


class ResamplingConfig(_Strict):
    """Train-only class-imbalance handling, applied after the train/test split (§3.2-3.3)."""

    strategy: ResamplingStrategy = "none"
    sampling_strategy: str | float = "auto"
    k_neighbors: int = Field(default=5, ge=1, description="SMOTE only; must be < smallest class")


class PreprocessingConfig(_Strict):
    kind: PreprocessingKind
    feature_selection: FeatureSelectionConfig = Field(default_factory=FeatureSelectionConfig)
    resampling: ResamplingConfig = Field(default_factory=ResamplingConfig)


class ExperimentConfig(_Strict):
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    seed: int = Field(ge=0)
    dataset: DatasetConfig
    models: list[ModelConfig] = Field(min_length=1)
    split: SplitConfig
    # Optional and defaulting to None (not a bare PreprocessingConfig default) so every
    # M0/M1 experiment config committed before this field existed keeps validating
    # unchanged; None is handled as "no feature selection, no resampling" wherever a
    # pipeline is built from this config.
    preprocessing: PreprocessingConfig | None = None

    @model_validator(mode="after")
    def _split_matches_dataset(self) -> ExperimentConfig:
        if self.split.strategy == "chronological" and self.dataset.timestamp_column is None:
            raise ValueError("chronological split requires dataset.timestamp_column")
        return self

    def canonical_hash(self) -> str:
        """SHA-256 of the canonical JSON form; identical configs give identical hashes."""
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a YAML mapping at top level")
    return data


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    """Load an experiment YAML file and resolve its dataset/model references."""
    path = Path(path)
    raw = _read_yaml(path)
    base = path.parent

    dataset_ref = raw.pop("dataset", None)
    model_refs = raw.pop("models", None)
    if not isinstance(dataset_ref, str):
        raise ValueError(f"{path}: `dataset` must be a relative path to a dataset config")
    if not isinstance(model_refs, list) or not all(isinstance(m, str) for m in model_refs):
        raise ValueError(f"{path}: `models` must be a list of relative paths to model configs")

    raw["dataset"] = _read_yaml(base / dataset_ref)
    raw["models"] = [_read_yaml(base / ref) for ref in model_refs]
    return ExperimentConfig.model_validate(raw)
