"""End-to-end smoke run on synthetic data.

Exercises config loading -> data generation -> split-before-fit -> pipeline fit ->
evaluation -> manifest writing. Outputs are tagged ``kind="smoke"`` and
``synthetic_data=True`` and are never valid research results.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from driftguard.config import ExperimentConfig
from driftguard.data.synthetic import generate_synthetic_flows
from driftguard.evaluation.metrics import classification_metrics
from driftguard.models.factory import build_estimator
from driftguard.preprocessing.pipeline import build_pipeline
from driftguard.preprocessing.split import Split, chronological_holdout, stratified_holdout
from driftguard.reporting.provenance import RunManifest, environment_snapshot, utc_timestamp

SMOKE_NOTICE = (
    "SMOKE TEST ON SYNTHETIC DATA. These numbers validate that the pipeline runs; they are "
    "not research results and must not be reported, plotted, or compared with the literature."
)


def frame_fingerprint(df: pd.DataFrame) -> str:
    """Order-sensitive SHA-256 over row hashes and column names."""
    digest = hashlib.sha256()
    digest.update("\x1f".join(map(str, df.columns)).encode("utf-8"))
    digest.update(pd.util.hash_pandas_object(df, index=True).to_numpy().tobytes())
    return digest.hexdigest()


def _split(df: pd.DataFrame, config: ExperimentConfig) -> Split:
    ds, sp = config.dataset, config.split
    if ds.label_column is None:
        raise ValueError("smoke datasets require label_column")
    if sp.strategy == "chronological" and ds.timestamp_column is not None:
        return chronological_holdout(df, ds.timestamp_column, sp.test_size)
    return stratified_holdout(df, ds.label_column, sp.test_size, config.seed)


def run_smoke(config: ExperimentConfig, output_root: str | Path) -> dict[str, Any]:
    ds = config.dataset
    if ds.kind != "synthetic" or ds.synthetic is None or ds.label_column is None:
        raise ValueError("the smoke run only accepts synthetic datasets")
    syn = ds.synthetic

    df = generate_synthetic_flows(
        n_samples=syn.n_samples,
        seed=config.seed,
        class_proportions=syn.class_proportions,
        drift_onset_fraction=syn.drift.onset_fraction if syn.drift else None,
        drift_scale_multiplier=syn.drift.scale_multiplier if syn.drift else 1.0,
        drift_features=syn.drift.features if syn.drift else (),
    )

    split = _split(df, config)

    non_features = {ds.label_column, *ds.drop_columns}
    if ds.timestamp_column is not None:
        non_features.add(ds.timestamp_column)
    categorical = [c for c in ds.categorical_columns if c not in non_features]
    numeric = [c for c in df.columns if c not in non_features and c not in categorical]
    features = numeric + categorical

    labels = sorted(df[ds.label_column].unique())
    x_train, y_train = split.train[features], split.train[ds.label_column]
    x_test, y_test = split.test[features], split.test[ds.label_column]

    results: dict[str, Any] = {}
    for model_cfg in config.models:
        pipeline = build_pipeline(numeric, categorical, build_estimator(model_cfg, config.seed))
        pipeline.fit(x_train, y_train)
        results[model_cfg.name] = classification_metrics(
            y_test.tolist(), pipeline.predict(x_test).tolist(), labels
        )

    config_hash = config.canonical_hash()
    created_at = utc_timestamp()
    run_id = f"{config.name}-{created_at.replace(':', '').replace('-', '')}-{config_hash[:8]}"
    run_dir = Path(output_root) / run_id

    manifest = RunManifest(
        run_id=run_id,
        kind="smoke",
        experiment=config.name,
        config_hash=config_hash,
        seed=config.seed,
        created_at=created_at,
        synthetic_data=True,
        data_fingerprints={f"synthetic:{ds.name}": frame_fingerprint(df)},
        environment=environment_snapshot(),
        notice=SMOKE_NOTICE,
    )
    manifest.write(run_dir / "manifest.json")

    summary = {
        "run_id": run_id,
        "kind": "smoke",
        "notice": SMOKE_NOTICE,
        "n_train": len(split.train),
        "n_test": len(split.test),
        "features": features,
        "metrics": results,
    }
    (run_dir / "metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary["run_dir"] = str(run_dir)
    return summary
