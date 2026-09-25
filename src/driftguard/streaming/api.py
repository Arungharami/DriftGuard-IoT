"""Read-only demo API over the event store (for the portal's server-side route only).

Returns sanitised aggregates: counts, decisions, latency percentiles and provenance
digests. It never returns feature values, addresses or payloads, and it has no write,
upload or model-loading endpoints. Every data endpoint requires a bearer token; without
a configured token the API reports itself unavailable instead of serving data openly.
"""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, Header, HTTPException

from driftguard.streaming.store import EventStore
from driftguard.streaming.worker import TokenBucket

NOTICE = (
    "NON-REPORTABLE live demonstration. Replay timing is imposed; end_to_end_ms uses one "
    "host's wall clock and is valid only when producer and worker share that host."
)


def create_demo_api(store_path: Path, *, token: str | None, requests_per_s: float = 5.0) -> FastAPI:
    app = FastAPI(
        title="DriftGuard-IoT demo (read-only)", docs_url=None, redoc_url=None, openapi_url=None
    )
    store = EventStore(store_path)
    limiter = TokenBucket(requests_per_s, burst=max(1, int(requests_per_s * 2)))

    def authorize(authorization: str | None) -> None:
        if not token:
            raise HTTPException(503, "demo API token not configured")
        supplied = (authorization or "").removeprefix("Bearer ").strip()
        if not supplied or not secrets.compare_digest(supplied, token):
            raise HTTPException(401, "authentication required")
        if not limiter.allow():
            raise HTTPException(429, "rate limit exceeded")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ready" if token else "unavailable"}

    @app.get("/v1/summary")
    def summary(authorization: Annotated[str | None, Header()] = None) -> dict[str, Any]:
        authorize(authorization)
        return {"notice": NOTICE, **store.summary()}

    @app.get("/v1/events/recent")
    def recent(
        authorization: Annotated[str | None, Header()] = None, limit: int = 50
    ) -> dict[str, Any]:
        authorize(authorization)
        if not 1 <= limit <= 200:
            raise HTTPException(422, "limit must be between 1 and 200")
        return {"notice": NOTICE, "events": store.recent(limit)}

    return app
