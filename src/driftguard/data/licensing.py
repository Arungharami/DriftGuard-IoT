"""License gates applied before any redistribution or publication.

The gate is deliberately conservative. Raw data is never redistributed by this project,
whatever the license. Derived artifacts (trained models, fitted preprocessing, derived
statistics) may be released only when every contributing dataset's card has a verified
license that explicitly permits it. With the current cards the answer is always "no" until
the team completes a license review and updates the cards in a reviewed PR.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal

from driftguard.data.registry import DatasetCard

ArtifactKind = Literal["raw_data", "derived_artifact"]


@dataclass(frozen=True)
class RedistributionDecision:
    allowed: bool
    reasons: list[str] = field(default_factory=list)


def redistribution_decision(
    cards: Iterable[DatasetCard], artifact_kind: ArtifactKind
) -> RedistributionDecision:
    reasons: list[str] = []
    cards = list(cards)
    if not cards:
        return RedistributionDecision(False, ["no source datasets declared"])
    if artifact_kind == "raw_data":
        return RedistributionDecision(
            False, ["project policy: raw datasets are never redistributed"]
        )
    for card in cards:
        lic = card.license
        if not lic.verified:
            reasons.append(f"{card.id}: license not verified")
        if lic.derived_artifact_redistribution != "permitted":
            reasons.append(
                f"{card.id}: derived-artifact redistribution is "
                f"'{lic.derived_artifact_redistribution}'"
            )
    return RedistributionDecision(allowed=not reasons, reasons=reasons)


def license_summary(card: DatasetCard) -> str:
    lic = card.license
    verified = f"verified {lic.verified_on}" if lic.verified else "NOT verified"
    return (
        f"{card.name}: {lic.name} ({verified}; source {lic.source_url}). "
        f"Academic use: {lic.academic_use}; commercial use: {lic.commercial_use}; "
        f"raw redistribution: {lic.raw_redistribution}; attribution required: "
        f"{lic.attribution_required}."
    )
