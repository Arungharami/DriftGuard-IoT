"""Platform boundaries and integration, entirely synthetic and offline."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from river.drift import ADWIN
from sklearn.tree import DecisionTreeClassifier

from driftguard.config import ExperimentConfig, load_experiment_config
from driftguard.drift.assessment import assess_alarms
from driftguard.evaluation.uncertainty import calibration_metrics, stratified_f1_interval
from driftguard.inference.service import create_app
from driftguard.m5.evaluation import delayed_prequential
from driftguard.platform.admission import admit_dataset
from driftguard.platform.bundle import prepare_bundle
from driftguard.platform.campaign import CampaignConfig, run_campaign
from driftguard.platform.publication import PublicationReview, sanitized_export
from driftguard.platform.transfer import chronological_partition
from driftguard.reporting.provenance import sha256_file

ROOT = Path(__file__).resolve().parents[1]


def config():
    base = load_experiment_config(ROOT / "configs/experiments/m2-leakage_safe-synthetic.yaml")
    raw = base.model_dump()
    raw["dataset"]["synthetic"]["n_samples"] = 200
    raw["models"] = [{"name": "decision_tree"}]
    return ExperimentConfig.model_validate(raw)


@pytest.fixture(scope="module")
def campaign_run(tmp_path_factory):
    path = tmp_path_factory.mktemp("campaign")
    report = run_campaign(config(), path, CampaignConfig(seeds=[11, 23], bootstrap_repeats=100))
    return path, report


def test_campaign_has_bound_outputs_intervals_and_seed_variation(campaign_run):
    path, report = campaign_run
    assert len(report["cells"]) == 2
    assert all(cell["status"] == "complete" for cell in report["cells"])
    assert report["aggregate"]["decision_tree"]["completed_seeds"] == 2
    assert not report["reportable"]
    for cell in report["cells"]:
        assert cell["metrics"]["decision_tree"]["macro_f1_ci"]["level"] == 0.95
        assert (path / cell["manifest"]).exists()


def test_resume_verifies_artifacts_without_refitting(campaign_run, monkeypatch):
    import driftguard.platform.campaign as module

    path, report = campaign_run
    monkeypatch.setattr(module, "run_experiment", lambda *a, **k: pytest.fail("resume refitted"))
    resumed = run_campaign(config(), path, CampaignConfig(seeds=[11, 23], bootstrap_repeats=100))
    assert resumed["cells"] == report["cells"]


def test_resume_rejects_changed_config(campaign_run):
    path, _ = campaign_run
    with pytest.raises(ValueError, match="resume refused"):
        run_campaign(config(), path, CampaignConfig(seeds=[11, 24], bootstrap_repeats=100))


def test_campaign_lock_blocks_concurrent_writers(tmp_path):
    (tmp_path / ".campaign.lock").touch()
    with pytest.raises(FileExistsError):
        run_campaign(config(), tmp_path, CampaignConfig())


def test_corrupt_checkpoint_refuses_resume(tmp_path):
    run_campaign(config(), tmp_path, CampaignConfig(seeds=[1, 2], bootstrap_repeats=100))
    checkpoint = next(tmp_path.glob("*/checkpoint.json"))
    doc = json.loads(checkpoint.read_text())
    name = next(iter(doc["files"]))
    (checkpoint.parent / name).write_text("tampered")
    with pytest.raises(ValueError, match="integrity"):
        run_campaign(config(), tmp_path, CampaignConfig(seeds=[1, 2], bootstrap_repeats=100))


def test_research_admission_blocks_unlicensed_dataset():
    cfg = config().dataset.model_copy(update={"kind": "wustl_iiot_2021", "synthetic": None})
    with pytest.raises(ValueError, match="permission"):
        admit_dataset(cfg)


def test_calibration_known_answers_and_invalid_probs():
    result = calibration_metrics([0, 1], [[1, 0], [0, 1]], [0, 1])
    assert result["ece"] == result["multiclass_brier"] == 0
    with pytest.raises(ValueError):
        calibration_metrics([0], [[2, -1]], [0, 1])
    ci = stratified_f1_interval([0, 1], [0, 1], repeats=100, seed=0)
    assert ci["low"] == ci["high"] == 1


def test_chronological_group_leakage_and_unsorted_times_rejected():
    train, test = chronological_partition(
        [0, 1, 2, 3], ["a", "a", "b", "b"], train_end=1, test_start=2
    )
    assert train.tolist() == [0, 1] and test.tolist() == [2, 3]
    with pytest.raises(ValueError):
        chronological_partition([0, 1, 2, 3], ["a"] * 4, train_end=1, test_start=2)
    with pytest.raises(ValueError):
        chronological_partition([1, 0], ["a", "b"], train_end=0, test_start=1)


def test_adwin_detects_fixed_abrupt_error_change():
    detector = ADWIN()
    alarms = []
    for i, error in enumerate([0] * 1000 + [1] * 1000):
        detector.update(error)
        if detector.drift_detected:
            alarms.append(i)
    assert alarms and min(alarms) >= 1000
    summary = assess_alarms(alarms, [1000], horizon=500, stream_start=0, stream_end=1999)
    assert summary["missed_changes"] == 0 and summary["false_alarm_count"] == 0


def test_adwin_cannot_see_unreleased_labels():
    x = np.arange(100).reshape(-1, 1)
    kwargs = dict(
        estimator=DecisionTreeClassifier(),
        initial_x=x[:20],
        initial_y=np.tile([0, 1], 10),
        stream_x=x[20:],
        initial_time=np.arange(20),
        event_time=np.arange(20, 100),
        label_time=np.arange(20, 100) + 1000,
        policy="adwin",
    )
    a = delayed_prequential(stream_y=np.zeros(80), **kwargs)
    b = delayed_prequential(stream_y=np.ones(80), **kwargs)
    np.testing.assert_array_equal(a["predictions"], b["predictions"])
    assert a["alarms"] == a["updates"] == []


def test_bundle_service_and_release_boundary(campaign_run, tmp_path):
    path, report = campaign_run
    run = (path / report["cells"][0]["manifest"]).parent
    meta = prepare_bundle(run, "decision_tree", tmp_path / "bundle")
    assert not meta["publication_allowed"]
    client = TestClient(create_app(tmp_path / "bundle", api_key="fixture-key"))
    row = {name: 0.0 if name in meta["numeric_features"] else "tcp" for name in meta["features"]}
    assert client.post("/predict", json={"rows": [row]}).status_code == 401
    response = client.post(
        "/predict", json={"rows": [row]}, headers={"X-Inference-Key": "fixture-key"}
    )
    assert response.status_code == 200
    assert response.json()["synthetic_data"] is True
    assert (
        client.post(
            "/predict",
            json={"rows": [{"ip": "private"}]},
            headers={"X-Inference-Key": "fixture-key"},
        ).status_code
        == 422
    )
    assert TestClient(create_app()).post("/predict", json={"rows": [{}]}).status_code == 503
    review = PublicationReview(
        manifest_sha256=sha256_file(run / "manifest.json"),
        metrics_sha256=sha256_file(run / "metrics.json"),
        owner_approved=True,
        reviewer="fixture",
        approval_reference="https://github.com/Arungharami/DriftGuard-IoT/pull/0",
        independent_sampling_evidence="synthetic fixture must never pass publication gate",
    )
    with pytest.raises(ValueError, match="synthetic"):
        sanitized_export(run, review)
