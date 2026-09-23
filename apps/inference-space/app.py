"""Prepared Docker Space. No model is downloaded or exposed automatically."""

import os
from pathlib import Path

from driftguard.inference.service import create_app

bundle_path = os.environ.get("DRIFTGUARD_BUNDLE_DIR")
app = create_app(
    Path(bundle_path) if bundle_path else None, api_key=os.environ.get("INFERENCE_API_KEY")
)
