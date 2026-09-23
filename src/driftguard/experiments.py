"""M2 baseline experiment runner.

Loads a synthetic or registry dataset (optionally a bounded, stratified subset drawn
*before* any split), prepares partitions with the configured protocol, fits each model,
evaluates on the untouched test partition, persists each fitted pipeline (preprocessing
and model together) and writes a v2 manifest whose reportability is enforced.

Resource figures (fit and predict wall-clock time, artifact size) are measurements of
this run on the machine recorded in the manifest's ``environment``. They are not claims
about any other hardware, including edge devices.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from driftguard.config import DatasetConfig, ExperimentConfig, PreprocessingConfig
from driftguard.data.loader import find_table_file, read_table
from driftguard.data.registry import get_dataset
from driftguard.data.sampling import SubsetSpec, deterministic_sample
from driftguard.data.synthetic import generate_synthetic_flows
from driftguard.evaluation.metrics import classification_metrics
from driftguard.models.factory import build_estimator, describe_params
from driftguard.models.persistence import save_pipeline
from driftguard.preprocessing.leakage_audit import audit_leakage
from driftguard.preprocessing.paper_protocol import (
    KNOWN_DISCREPANCIES,
    PAPER_DOI,
    PAPER_LEAKAGE_RISKS,
    PAPER_PROTOCOLS,
    PaperDatasetProtocol,
)
from driftguard.preprocessing.protocols import (
    PreparedData,
    build_leakage_safe_pipeline,
    build_paper_faithful_pipeline,
    prepare_leakage_safe,
    prepare_paper_faithful,
)
from driftguard.reporting.manifest import (
    NON_REPORTABLE,
    DatasetProvenance,
    ExperimentManifest,
    ModelRecord,
)
from driftguard.reporting.provenance import environment_snapshot, sha256_file, utc_timestamp
from driftguard.smoke import frame_fingerprint

MEASUREMENT_NOTE = (
    "fit_seconds, predict_seconds and artifact_size_bytes were measured in this run on the "
    "machine described in `environment`; they are not claims about other hardware."
)
NUMERIC_DTYPES = frozenset({"int", "float", "bool"})


@dataclass
class LoadedDataset:
    frame: pd.DataFrame
    target: str
    numeric: list[str]
    categorical: list[str]
    provenance: DatasetProvenance
    synthetic: bool
    paper: PaperDatasetProtocol | None


def load_dataset(ds: DatasetConfig, seed: int, data_root: Path | None = None) -> LoadedDataset:
    if not ds.is_registry:
        return _load_synthetic(ds, seed)
    card = get_dataset(ds.kind)
    table = card.table(ds.table)
    path = find_table_file(card.id, table, data_root)
    source_sha = sha256_file(path)
    df = read_table(path, table)
    if ds.target == "attack_type":
        if table.attack_type_column is None:
            raise ValueError(f"{card.id}/{table.id} has no attack_type column")
        target = table.attack_type_column
    else:
        target = table.label_column
    if ds.row_limit is not None:
        df = deterministic_sample(
            df,
            SubsetSpec(
                n=ds.row_limit, seed=seed, stratify_column=target, min_per_class=ds.min_per_class
            ),
        )
    features = [c for c in table.feature_columns if c not in ds.drop_columns and c in df.columns]
    numeric = [c for c in features if table.column(c).dtype in NUMERIC_DTYPES]
    categorical = [c for c in features if c not in numeric]
    paper = PAPER_PROTOCOLS.get(card.id)
    return LoadedDataset(
        frame=df,
        target=target,
        numeric=numeric,
        categorical=categorical,
        provenance=DatasetProvenance(
            dataset_id=card.id,
            table_id=table.id,
            source_file=path.name,
            source_sha256=source_sha,
            sha256_matches_registry=None if table.sha256 is None else source_sha == table.sha256,
            row_limit=ds.row_limit,
            rows_loaded=len(df),
            target=target,
        ),
        synthetic=False,
        paper=paper if ds.target == "attack_type" else None,
    )


def _load_synthetic(ds: DatasetConfig, seed: int) -> LoadedDataset:
    syn = ds.synthetic
    if syn is None or ds.label_column is None:
        raise ValueError("synthetic dataset config is incomplete")
    df = generate_synthetic_flows(
        n_samples=syn.n_samples,
        seed=seed,
        class_proportions=syn.class_proportions,
        drift_onset_fraction=syn.drift.onset_fraction if syn.drift else None,
        drift_scale_multiplier=syn.drift.scale_multiplier if syn.drift else 1.0,
        drift_features=syn.drift.features if syn.drift else (),
    )
    non_features = {ds.label_column, *ds.drop_columns}
    if ds.timestamp_column:
        non_features.add(ds.timestamp_column)
    categorical = [c for c in ds.categorical_columns if c not in non_features]
    numeric = [c for c in df.columns if c not in non_features and c not in categorical]
    paper = PaperDatasetProtocol(
        dataset_id=f"synthetic:{ds.name}",
        target_column=ds.label_column,
        original_rows=len(df),
        model_ready_rows=len(df),
        pre_mi_drop=tuple(c for c in (ds.timestamp_column,) if c),
        reported_mi_removed=(),
        figure_mi_features=(),
        figure="n/a (synthetic)",
    )
    return LoadedDataset(
        frame=df,
        target=ds.label_column,
        numeric=numeric,
        categorical=categorical,
        provenance=DatasetProvenance(
            dataset_id=f"synthetic:{ds.name}",
            table_id=None,
            source_file=None,
            source_sha256=frame_fingerprint(df),
            sha256_matches_registry=None,
            row_limit=None,
            rows_loaded=len(df),
            target=ds.label_column,
        ),
        synthetic=True,
        paper=paper,
    )


def prepare(data: LoadedDataset, config: ExperimentConfig) -> PreparedData:
    cfg = config.preprocessing or PreprocessingConfig()
    if cfg.protocol == "paper_faithful":
        if data.paper is None:
            raise ValueError("paper_faithful requires the multi-class attack_type target")
        return prepare_paper_faithful(
            data.frame,
            protocol=data.paper,
            cfg=cfg,
            test_size=config.split.test_size,
            seed=config.seed,
        )
    if config.split.strategy != "stratified_holdout":
        raise ValueError("M2 baselines use stratified_holdout; chronological evaluation is M4")
    return prepare_leakage_safe(
        data.frame,
        target=data.target,
        numeric_columns=data.numeric,
        categorical_columns=data.categorical,
        test_size=config.split.test_size,
        seed=config.seed,
        deduplicate=cfg.deduplicate,
    )


def _pipeline_details(pipeline: Any, protocol: str) -> dict[str, Any]:
    if protocol != "leakage_safe":
        return {}
    steps = pipeline.named_steps
    mi = steps["mi"]
    details: dict[str, Any] = {
        "mi_fit_rows": mi.n_fit_rows_,
        "mi_score_rows": mi.n_score_rows_,
        "mi_selected_features": mi.selected_features_,
        "mi_scores_train": mi.scores_,
        "mi_fallback_used": mi.fallback_used_,
    }
    if "resample" in steps:
        rs = steps["resample"]
        details.update(
            resample_input_rows=rs.n_input_rows_,
            resample_output_rows=rs.n_output_rows_,
            resample_synthetic_rows=rs.n_synthetic_rows_,
        )
    return details


def run_experiment(
    config: ExperimentConfig,
    output_root: str | Path,
    *,
    kind: str = "development",
    data_root: Path | None = None,
    save_models: bool = True,
    bootstrap_repeats: int = 0,
) -> dict[str, Any]:
    cfg = config.preprocessing or PreprocessingConfig()
    if kind == "research" and config.dataset.is_registry:
        from driftguard.platform.admission import admit_dataset

        admit_dataset(config.dataset, data_root)
    data = load_dataset(config.dataset, config.seed, data_root)
    prepared = prepare(data, config)

    config_hash = config.canonical_hash()
    created_at = utc_timestamp()
    run_id = f"{config.name}-{created_at.replace(':', '').replace('-', '')}-{config_hash[:8]}"
    run_dir = Path(output_root) / run_id

    labels = sorted(set(prepared.y_train) | set(prepared.y_test), key=str)
    audit = audit_leakage(
        pd.concat([prepared.X_train, prepared.y_train], axis=1),
        pd.concat([prepared.X_test, prepared.y_test], axis=1),
        list(prepared.X_train.columns),
        str(prepared.y_train.name),
    ).to_dict()

    if kind == "research" and audit["cross_partition_duplicate_rows"]:
        raise ValueError("research blocked: feature-identical rows cross the split")

    records: list[ModelRecord] = []
    metrics: dict[str, Any] = {}
    for model_cfg in config.models:
        estimator = build_estimator(model_cfg, config.seed, config.n_jobs)
        pipeline = (
            build_leakage_safe_pipeline(
                prepared.numeric_columns, prepared.categorical_columns, estimator, cfg, config.seed
            )
            if prepared.protocol == "leakage_safe"
            else build_paper_faithful_pipeline(prepared.numeric_columns, estimator)
        )
        t0 = time.perf_counter()
        pipeline.fit(prepared.X_train, prepared.y_train)
        fit_s = time.perf_counter() - t0
        t0 = time.perf_counter()
        y_pred = pipeline.predict(prepared.X_test)
        predict_s = time.perf_counter() - t0
        proba = (
            pipeline.predict_proba(prepared.X_test) if hasattr(pipeline, "predict_proba") else None
        )
        metrics[model_cfg.name] = classification_metrics(
            prepared.y_test.tolist(),
            list(y_pred),
            labels,
            y_proba=np.asarray(proba) if proba is not None else None,
            proba_classes=list(pipeline.classes_) if proba is not None else None,
        )
        from driftguard.evaluation.uncertainty import calibration_metrics, stratified_f1_interval

        if bootstrap_repeats:
            metrics[model_cfg.name]["macro_f1_ci"] = stratified_f1_interval(
                prepared.y_test, y_pred, repeats=bootstrap_repeats, seed=config.seed
            )
        if proba is not None:
            metrics[model_cfg.name]["calibration"] = calibration_metrics(
                prepared.y_test, proba, pipeline.classes_
            )
        matrix = np.asarray(metrics[model_cfg.name]["confusion_matrix"]["matrix"])
        false_positives = matrix.sum(axis=0) - np.diag(matrix)
        negatives = matrix.sum() - matrix.sum(axis=1)
        metrics[model_cfg.name]["false_positive_rate_per_class"] = {
            str(label): float(fp / n) if n else None
            for label, fp, n in zip(labels, false_positives, negatives, strict=True)
        }
        artifact = run_dir / "models" / f"{model_cfg.name}.joblib"
        sha = save_pipeline(pipeline, artifact) if save_models else None
        records.append(
            ModelRecord(
                name=model_cfg.name,
                estimator=type(estimator).__name__,
                params=describe_params(estimator),
                fit_seconds=round(fit_s, 4),
                predict_seconds=round(predict_s, 4),
                artifact_path=str(artifact.relative_to(run_dir)) if save_models else None,
                artifact_sha256=sha,
                artifact_size_bytes=artifact.stat().st_size if save_models else None,
                preprocessing=_pipeline_details(pipeline, prepared.protocol),
            )
        )

    protocol_details: dict[str, Any] = {
        **_json_safe(prepared.details),
        "n_train": len(prepared.X_train),
        "n_test": len(prepared.X_test),
        "features_in": list(prepared.X_train.columns),
        "numeric_columns": prepared.numeric_columns,
        "categorical_columns": prepared.categorical_columns,
        "leakage_audit": audit,
    }
    if prepared.protocol == "paper_faithful":
        protocol_details["reference"] = {
            "doi": PAPER_DOI,
            "leakage_risks": list(PAPER_LEAKAGE_RISKS),
            "known_discrepancies": list(KNOWN_DISCREPANCIES),
        }
    manifest = ExperimentManifest(
        run_id=run_id,
        kind=kind,
        experiment=config.name,
        config_hash=config_hash,
        config=config.model_dump(mode="json"),
        seed=config.seed,
        created_at=created_at,
        synthetic_data=data.synthetic,
        protocol=prepared.protocol,
        protocol_details=protocol_details,
        dataset=data.provenance,
        models=records,
        measurement_note=MEASUREMENT_NOTE,
        environment=environment_snapshot(),
    )
    manifest.write(run_dir / "manifest.json")
    summary = {
        "run_id": run_id,
        "reportable": manifest.reportable,
        "reportability": manifest.reportability,
        "protocol": prepared.protocol,
        "dataset": data.provenance.dataset_id,
        "n_train": len(prepared.X_train),
        "n_test": len(prepared.X_test),
        "metrics": metrics,
    }
    (run_dir / "metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {**summary, "run_dir": str(run_dir), "manifest": manifest}


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, np.generic):
        return obj.item()
    return obj


__all__ = ["NON_REPORTABLE", "LoadedDataset", "load_dataset", "prepare", "run_experiment"]
