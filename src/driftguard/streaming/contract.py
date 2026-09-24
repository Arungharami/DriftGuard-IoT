"""Versioned MQTT event contract (``driftguard/v1``) for the tier-A replay demonstration.

Implements section 3 of ``docs/research-2026/secure-streaming-demo.md``. A feature message
carries model-visible features only: ground-truth labels never travel in prediction
payloads. Every absent measurement is ``None`` (not measured), never a guessed value.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

SCHEMA_VERSION = "driftguard/v1"
MAX_PAYLOAD_BYTES = 16 * 1024
MAX_FEATURES = 256
MAX_CATEGORY_CHARS = 64
DEVICE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
SHA256 = r"^[0-9a-f]{64}$"

HEALTH_TOPIC = f"{SCHEMA_VERSION}/system/health"
FEATURE_SUBSCRIPTION = f"{SCHEMA_VERSION}/features/+/+"

# synthetic_fixture: generated rows (never research evidence). dataset_replay: rows of an
# admitted dataset replayed at imposed rates. lab_capture: authorised passive lab flows.
EvidenceTier = Literal["synthetic_fixture", "dataset_replay", "lab_capture"]
AlertStatus = Literal["predicted", "rejected", "duplicate", "model_unavailable"]


class ContractViolationError(ValueError):
    """A payload that must be rejected without prediction."""

    def __init__(self, category: str, detail: str = "") -> None:
        super().__init__(f"{category}: {detail}" if detail else category)
        self.category = category


def _device(device_id: str) -> str:
    if not DEVICE_ID.fullmatch(device_id):
        raise ValueError(f"invalid lab device id {device_id!r}")
    return device_id


def features_topic(feed: str, device_id: str) -> str:
    """``feed`` names the feature contract, e.g. ``edgeiiotset`` or ``synthetic``."""
    return f"{SCHEMA_VERSION}/features/{_device(feed)}/{_device(device_id)}"


def alerts_topic(device_id: str) -> str:
    return f"{SCHEMA_VERSION}/alerts/{_device(device_id)}"


class FeatureMessage(BaseModel):
    """One replayed or captured feature vector. Unknown fields (e.g. a label) are rejected."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["driftguard/v1"]
    event_id: UUID
    source: Literal["replay", "capture"]
    evidence_tier: EvidenceTier
    dataset_sha256: str | None = Field(default=None, pattern=SHA256)
    capture_id: str | None = Field(default=None, max_length=64)
    event_time_utc: datetime | None = None
    replay_send_time_utc: datetime | None = None
    publisher_sequence: int = Field(ge=0)
    # None = missing value (imputed by the frozen pipeline); JSON has no NaN.
    features: dict[str, float | str | None] = Field(min_length=1, max_length=MAX_FEATURES)

    @model_validator(mode="after")
    def provenance_matches_source(self) -> FeatureMessage:
        if self.source == "replay":
            if self.evidence_tier == "lab_capture":
                raise ValueError("replayed rows cannot claim lab_capture evidence")
            if self.dataset_sha256 is None or self.replay_send_time_utc is None:
                raise ValueError("replay requires dataset_sha256 and replay_send_time_utc")
        elif self.evidence_tier != "lab_capture" or self.capture_id is None:
            raise ValueError("capture requires lab_capture tier and capture_id")
        for when in (self.event_time_utc, self.replay_send_time_utc):
            if when is not None and when.utcoffset() is None:
                raise ValueError("timestamps must be timezone-aware UTC")
        return self


def parse_feature_message(payload: bytes) -> FeatureMessage:
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ContractViolationError("oversized", f"{len(payload)} > {MAX_PAYLOAD_BYTES} bytes")
    try:
        raw = json.loads(payload.decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ContractViolationError("malformed", type(exc).__name__) from exc
    if not isinstance(raw, dict):
        raise ContractViolationError("malformed", "payload is not a JSON object")
    try:
        return FeatureMessage.model_validate(raw)
    except ValidationError as exc:
        fields = sorted({".".join(map(str, e["loc"])) for e in exc.errors()})
        raise ContractViolationError("schema", ", ".join(fields)[:200]) from exc


def _reject_constant(name: str) -> float:
    raise ValueError(f"non-finite JSON constant {name}")


class FeatureContract(BaseModel):
    """The exact model-visible inference inputs of one frozen bundle."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    features: tuple[str, ...] = Field(min_length=1)
    numeric_features: frozenset[str]

    @model_validator(mode="after")
    def consistent(self) -> FeatureContract:
        if len(set(self.features)) != len(self.features):
            raise ValueError("duplicate feature names")
        if not self.numeric_features <= set(self.features):
            raise ValueError("numeric features must be a subset of features")
        return self

    @property
    def sha256(self) -> str:
        body = json.dumps(
            {"features": list(self.features), "numeric": sorted(self.numeric_features)},
            sort_keys=True,
        )
        return hashlib.sha256(body.encode()).hexdigest()

    def check(self, features: dict[str, float | str | None]) -> None:
        if set(features) != set(self.features):
            missing = sorted(set(self.features) - set(features))[:5]
            extra = sorted(set(features) - set(self.features))[:5]
            raise ContractViolationError(
                "feature_mismatch", f"missing={missing} unexpected={extra}"
            )
        for name in self.features:
            value = features[name]
            if value is None:
                continue
            if name in self.numeric_features:
                if isinstance(value, str) or not math.isfinite(value):
                    raise ContractViolationError("invalid_value", f"{name} must be a finite number")
            elif not isinstance(value, str) or len(value) > MAX_CATEGORY_CHARS:
                raise ContractViolationError("invalid_value", f"{name} must be a short string")


class Alert(BaseModel):
    """Worker output. Carries no feature values, addresses or payload content."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["driftguard/v1"] = "driftguard/v1"
    event_id: UUID | None
    publisher_sequence: int | None
    received_at_utc: datetime
    status: AlertStatus
    decision: str | None = None
    reason: str | None = None
    evidence_tier: EvidenceTier | None
    model_sha256: str | None = None
    contract_sha256: str | None = None
    inference_ms: float | None = None
    end_to_end_ms: float | None = None
    reportable: Literal[False] = False
