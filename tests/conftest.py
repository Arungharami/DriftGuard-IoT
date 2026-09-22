from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from driftguard.data.synthetic import generate_synthetic_flows

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIGS = REPO_ROOT / "configs"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def synthetic_flows() -> pd.DataFrame:
    return generate_synthetic_flows(n_samples=1500, seed=7)


@pytest.fixture(scope="session")
def drifted_flows() -> pd.DataFrame:
    return generate_synthetic_flows(
        n_samples=2000,
        seed=7,
        drift_onset_fraction=0.5,
        drift_scale_multiplier=4.0,
        drift_features=("src_bytes",),
    )
