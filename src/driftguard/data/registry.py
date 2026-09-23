"""Dataset registry: provenance, license terms, acquisition routes and table schemas.

Each dataset is described by a YAML *card* in ``driftguard/data/catalog/``. Cards record
only facts checked against a primary source (with the URL and date of the check).
Anything not yet checked is represented explicitly: ``sha256: null`` until a file has
been fingerprinted, ``schema_status: provisional`` until the column list has been
confirmed against a downloaded file header.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from functools import cache
from importlib.resources import files
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

UsePermission = Literal["permitted", "permission_required", "prohibited", "not_stated"]
Redistribution = Literal["permitted_with_conditions", "not_granted", "not_stated"]
DerivedRedistribution = Literal["permitted", "requires_review", "prohibited"]
ColumnDType = Literal["int", "float", "string", "category", "bool", "timestamp"]
ColumnRole = Literal[
    "feature",  # candidate model input
    "label",  # primary target
    "attack_type",  # multi-class attack family; leaks the binary label
    "timestamp",  # event time; never a raw model input
    "identifier",  # addresses, IDs; private and/or leaky
    "payload",  # free text derived from packet contents; private
]
PRIVATE_ROLES: frozenset[str] = frozenset({"identifier", "payload"})
NON_FEATURE_ROLES: frozenset[str] = frozenset(
    {"label", "attack_type", "timestamp", "identifier", "payload"}
)

_SHA256 = r"^[0-9a-f]{64}$"


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class LicenseInfo(_Frozen):
    name: str
    source_url: HttpUrl
    verified_on: dt.date | None
    terms_excerpt: str | None = None
    academic_use: UsePermission
    commercial_use: UsePermission
    raw_redistribution: Redistribution
    derived_artifact_redistribution: DerivedRedistribution
    attribution_required: bool
    notes: str = ""

    @property
    def verified(self) -> bool:
        return self.verified_on is not None


class Citation(_Frozen):
    text: str
    doi: str | None = None


class KaggleSource(_Frozen):
    slug: str = Field(pattern=r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
    first_party: bool
    approved: bool
    license_name: str
    version: int | None = None
    verified_on: dt.date
    notes: str = ""

    @model_validator(mode="after")
    def _only_first_party_can_be_approved(self) -> KaggleSource:
        if self.approved and not self.first_party:
            raise ValueError("only first-party Kaggle uploads may be approved")
        return self


class Acquisition(_Frozen):
    method: Literal["manual", "kaggle"]
    url: HttpUrl
    instructions: str
    kaggle: KaggleSource | None = None
    unapproved_mirrors: str = ""

    @model_validator(mode="after")
    def _kaggle_method_needs_approved_source(self) -> Acquisition:
        if self.method == "kaggle" and (self.kaggle is None or not self.kaggle.approved):
            raise ValueError("method 'kaggle' requires an approved first-party Kaggle source")
        return self


class ColumnSpec(_Frozen):
    name: str
    dtype: ColumnDType
    role: ColumnRole = "feature"
    optional: bool = False
    exclude_reason: str | None = None

    @property
    def private(self) -> bool:
        return self.role in PRIVATE_ROLES

    @property
    def is_feature(self) -> bool:
        return self.role == "feature" and self.exclude_reason is None


class TableSpec(_Frozen):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    filename: str
    relative_path: str | None = None
    description: str
    size_bytes: int | None = Field(default=None, ge=0)
    size_source: str | None = None
    sha256: str | None = Field(default=None, pattern=_SHA256)
    n_rows: int | None = Field(default=None, ge=0)
    archive_filename: str | None = None
    archive_sha256: str | None = Field(default=None, pattern=_SHA256)
    archive_size_bytes: int | None = Field(default=None, ge=0)
    verified_on: dt.date | None = None
    schema_status: Literal["provisional", "confirmed"]
    schema_source: str
    na_values: list[str] = Field(default_factory=list)
    columns: list[ColumnSpec] = Field(min_length=2)

    @model_validator(mode="after")
    def _roles_consistent(self) -> TableSpec:
        names = [c.name for c in self.columns]
        dupes = {n for n in names if names.count(n) > 1}
        if dupes:
            raise ValueError(f"duplicate column names: {sorted(dupes)}")
        if sum(c.role == "label" for c in self.columns) != 1:
            raise ValueError("exactly one column must have role 'label'")
        if sum(c.role == "timestamp" for c in self.columns) > 1:
            raise ValueError("at most one column may have role 'timestamp'")
        return self

    def column(self, name: str) -> ColumnSpec:
        for c in self.columns:
            if c.name == name:
                return c
        raise KeyError(name)

    @property
    def label_column(self) -> str:
        return next(c.name for c in self.columns if c.role == "label")

    @property
    def attack_type_column(self) -> str | None:
        return next((c.name for c in self.columns if c.role == "attack_type"), None)

    @property
    def timestamp_column(self) -> str | None:
        return next((c.name for c in self.columns if c.role == "timestamp"), None)

    @property
    def feature_columns(self) -> list[str]:
        return [c.name for c in self.columns if c.is_feature]

    @property
    def private_columns(self) -> list[str]:
        return [c.name for c in self.columns if c.private]

    @property
    def required_columns(self) -> list[str]:
        return [c.name for c in self.columns if not c.optional]


class DatasetCard(_Frozen):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    name: str
    publisher: str
    homepage: HttpUrl
    description: str
    license: LicenseInfo
    citations: list[Citation] = Field(min_length=1)
    acquisition: Acquisition
    tables: list[TableSpec] = Field(min_length=1)
    default_table: str

    @field_validator("tables")
    @classmethod
    def _unique_table_ids(cls, tables: list[TableSpec]) -> list[TableSpec]:
        ids = [t.id for t in tables]
        if len(set(ids)) != len(ids):
            raise ValueError("table ids must be unique")
        return tables

    @model_validator(mode="after")
    def _default_table_exists(self) -> DatasetCard:
        if self.default_table not in {t.id for t in self.tables}:
            raise ValueError(f"default_table {self.default_table!r} is not a table id")
        return self

    def table(self, table_id: str | None = None) -> TableSpec:
        wanted = table_id or self.default_table
        for t in self.tables:
            if t.id == wanted:
                return t
        raise KeyError(f"{self.id} has no table {wanted!r}")


class UnknownDatasetError(KeyError):
    pass


def _catalog_texts() -> Iterator[tuple[str, str]]:
    root = files("driftguard.data").joinpath("catalog")
    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        if entry.name.endswith(".yaml"):
            yield entry.name, entry.read_text(encoding="utf-8")


@cache
def load_registry() -> dict[str, DatasetCard]:
    """Load and validate every dataset card shipped with the package."""
    cards: dict[str, DatasetCard] = {}
    for filename, text in _catalog_texts():
        card = DatasetCard.model_validate(yaml.safe_load(text))
        if f"{card.id}.yaml" != filename:
            raise ValueError(f"{filename}: card id {card.id!r} must match its filename")
        cards[card.id] = card
    return cards


def get_dataset(dataset_id: str) -> DatasetCard:
    registry = load_registry()
    try:
        return registry[dataset_id]
    except KeyError:
        known = ", ".join(sorted(registry))
        raise UnknownDatasetError(f"unknown dataset {dataset_id!r}; known: {known}") from None
