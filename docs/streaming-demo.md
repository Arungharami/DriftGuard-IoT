# Tier-A MQTT replay demonstration

Implements the tier-A pipeline in `docs/research-2026/secure-streaming-demo.md` (draft PR
#14). **Status: implemented and tested with SYNTHETIC fixture data only.** No real model
exists yet: the Edge-IIoTset file has not been acquired. Nothing produced by this
demonstration is research evidence, and none of it may appear in the paper's results.

```
replay producer ──MQTT 5, QoS 1──▶ Mosquitto 2.x ──▶ inference worker ──▶ SQLite event store
(user: replay)     auth + ACL       (loopback/TLS)    (user: worker)          │
                                                      │ alerts (QoS 1)        ▼
                                                      ▼                  read-only API ──▶ portal
                                          monitor (user: monitor)      (bearer token)   (server-side)
```

## What each stage does

| Stage | Module | Behaviour |
| --- | --- | --- |
| Contract | `streaming/contract.py` | `driftguard/v1` messages: UUID `event_id`, `publisher_sequence`, `replay_send_time_utc`, dataset SHA-256, features only. Unknown fields (including any label) are rejected. Payloads over 16 KiB, invalid UTF-8/JSON, `NaN`/`Infinity` and naive timestamps are rejected |
| Producer | `streaming/replay.py` | Publishes held-out test rows of a verified run at a fixed imposed rate. Synthetic mode regenerates the bundle's own test partition and checks its fingerprint. Real mode verifies `split.json`, the admission gate and the dataset SHA-256 |
| Broker | `streaming/broker.py` | Anonymous access off. Per-role passwords (hashed by `mosquitto_passwd`) and deny-by-default topic ACLs. Packet-size limit. Loopback-only unless TLS files are given. Secrets written with mode 0600 to git-ignored `.local/` |
| Worker | `streaming/worker.py` | Non-blocking hand-off → bounded queue (overflow dropped and counted) → optional rate limit → contract check → event-id dedup (memory plus a unique key in the store) → hash-verified model → alert. With no bundle it records `model_unavailable` and makes no prediction |
| Monitor | `OutputShiftMonitor` | River ADWIN over the *predicted* attack indicator. Unsupervised output-distribution signal: **not** concept-drift ground truth, uncalibrated (`delta` 0.002) |
| Store/API | `streaming/store.py`, `streaming/api.py` | Aggregates only: counts, decisions, latency percentiles, model digest. No feature values, identifiers or payloads. Token required; 503 without a configured token; rate-limited; no docs/OpenAPI routes; no write endpoints |

Evidence tiers are carried on every alert. A synthetic model or synthetic rows always
downgrade the alert to `synthetic_fixture`. A real bundle rejects `dataset_replay`
messages whose dataset SHA-256 differs from its training data.

## Running it locally

```bash
pip install -e ".[streaming]" -c requirements/constraints-py311.txt   # plus Mosquitto 2.x
driftguard stream broker-config --port 18883        # .local/stream/broker/{mosquitto.conf,acl,passwords,credentials.env}
mosquitto -c .local/stream/broker/mosquitto.conf &
driftguard stream demo-bundle                        # SYNTHETIC model, publication_allowed=false
set -a; . .local/stream/broker/credentials.env; set +a
driftguard stream worker --bundle .local/stream/synthetic-bundle --benign-label normal &
driftguard stream replay --bundle .local/stream/synthetic-bundle --rate 50 --max-events 500
driftguard stream api --port 18765 &                  # GET /v1/summary with "Authorization: Bearer $DRIFTGUARD_DEMO_API_TOKEN"
```

Once an admitted real-data run exists, build its bundle with `prepare_bundle` and run
`driftguard stream replay --source heldout --run-dir <run>`. Replay stays blocked until
admission passes.

To go across machines, generate certificates and pass `--bind <address> --tls-ca --tls-cert
--tls-key`. The generator refuses a non-loopback listener without TLS.

## Measurement definitions

- `inference_ms`: `time.perf_counter()` around `pipeline.predict` for one row (batch size 1),
  after the model is loaded. It is a warm measurement on the machine running the worker.
- `end_to_end_ms`: the worker's UTC completion time minus the producer's `replay_send_time_utc`.
  It uses **one host's wall clock**, so it is valid only when producer and worker share a
  host. Across hosts it would need NTP-disciplined clocks and a stated error bound.
- The achieved replay rate is recorded by the producer. Replay timing is imposed and is
  never original event time; `event_time_utc` stays `null`.

Not measured (reported as absent, never estimated): cold start, CPU, RSS, broker-receive
time, dashboard delivery time, edge-hardware latency and energy.

## Tests

- `tests/streaming/test_contract_and_replay.py` and `test_worker_store_api.py`: contract
  rejection cases, dedup (in memory and across restarts), fail-closed behaviour, dataset
  mismatch, bounded queue, rate limits, retention, API authorisation, sanitisation, and
  regression tests for replay reproducing the recorded test partition.
- `tests/streaming/test_mqtt_integration.py` (marker `mqtt`) starts a real Mosquitto
  process. It covers:
  - rejection of anonymous clients and wrong passwords;
  - an ACL-refused publish;
  - end-to-end replay with alerts reaching a monitor client;
  - a QoS 1 duplicate;
  - a malformed payload;
  - broker rejection of an oversized packet;
  - persistent-session delivery while the worker is offline;
  - recovery after a broker restart;
  - a TLS listener with a verified CA, plaintext refusal and untrusted-CA refusal.

  CI runs these in the `mqtt` job and fails if they are skipped.

## Not implemented (explicitly)

- Tier B (physical ESP32/Raspberry Pi telemetry) and tier C (authorised lab flow capture).
- A Docker Compose profile. There was no container runtime to test one with, so none is shipped.
- Production streaming service hosting. The portal now integrates the read-only API
  at `/demo` via `/api/stream` and uses a labeled, sanitized synthetic recording offline.
  See `apps/research-portal/README.md` for server-only configuration.
- Any real-data replay, and any edge-device measurement.
