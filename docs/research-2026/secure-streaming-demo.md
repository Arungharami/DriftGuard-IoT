# Secure streaming demonstration: implementable specification (2026-09-23)
Status: DESIGN ONLY. No live MQTT, physical edge inference, real-traffic capture or energy measurement has been verified in this PR.

## 1. What the demonstration actually proves
Three evidence tiers are distinct:
- Tier A: **real dataset row replay** through a real MQTT broker, a real serialized model and a live dashboard. The rows come from an admitted file, but replay timing is imposed and NOT evidence of real-world temporal drift or live intrusion generation.
- Tier B: **local device telemetry** from a permitted ESP32/Raspberry Pi or simulator, over MQTT, optionally alongside the replay. Raw temperature/humidity data are NOT network-flow features. Unless a separately trained, approved fusion model exists, telemetry must never be passed as if it were an Edge-IIoTset IDS input.
- Tier C: **authorized lab network flow ingestion** from an isolated, passive lab sensor via a documented flow extractor producing the identical versioned feature contract. Require capture/session provenance, authentication, explicit permission and no production-network attack generation. This tier alone supports claims about real captured network traffic; physical edge benchmark claims require actual edge hardware.

## 2. Architecture and trust boundaries
Offline experiment -> admitted dataset fingerprint -> frozen validated preprocessing+model bundle -> signed/versioned manifest -> edge inference service.
Tier A: rate-limited CSV replay producer -> local MQTT v5 broker -> consumer/schema guard/deduplicator -> model inference -> alerts topic and append-only event store -> read-only FastAPI API/WebSocket -> Vercel research portal.
Tier B: ESP32 or Raspberry Pi -> separate telemetry topic -> telemetry chart (not IDS classification).
Tier C: authorized passive capture -> Zeek/Argus or other PRE-VALIDATED matching extraction -> flow topic -> same guarded inference pipeline.

No arbitrary public upload of CSVs, model pickles or packet captures. No browser connects directly to the private broker. Keep broker, inference service and event store private; expose only filtered and rate-limited aggregate views through authenticated backend routes. Model artifacts must load only from a hash-checked trusted source.

## 3. Proposed versioned event contract
Namespace: driftguard/v1. MQTT topics:
- driftguard/v1/features/edgeiiotset/{lab_device_id}
- driftguard/v1/telemetry/{lab_device_id}
- driftguard/v1/alerts/{lab_device_id}
- driftguard/v1/system/health

A feature message includes event_id (UUID), schema_version, source (replay or capture), dataset_sha256 for replay, capture_id if applicable, event_time_utc if actually known, replay_send_time_utc, publisher_sequence and exactly the approved model-visible feature names/units. Do NOT include a ground-truth class in the production prediction payload. Ground-truth labels, when available for offline scoring, travel only in a separately access-controlled evaluation sidecar joined by event_id.

An alert includes event_id, received_at_utc, model_sha256, preprocessing_sha256, decision (benign, known attack, or abstain if independently implemented), calibrated probability only if the model genuinely supports it, processing latency, deduplication status and simulation/evidence tier. Absent fields are null/not measured, never fabricated. Never put host IPs, MACs or raw payloads in a public page.

Configure broker credentials, per-client topic ACLs, TLS when traffic crosses machines, bounded message sizes, message rate limits, persistent sessions only where necessary and durable but bounded event storage. Prefer MQTT QoS 1 with consumer idempotency keyed by event_id; QoS 1 can redeliver. Document broker restart and disconnected consumer behavior. For stronger MQTT claims consult the OASIS MQTT 5.0 standard; for industrial network segmentation consult NIST SP 800-82 Rev. 3 (Rev. 4 is still a draft as of 2026-09-23).

## 4. Demonstration sequence
1. Validate official Edge-IIoTset file and record fingerprint; fit/select one frozen admitted baseline, or demonstrate a clearly NON-REPORTABLE synthetic fixture with explicit UI watermark until the real model exists.
2. Build a local-only Docker Compose profile: authenticated Mosquitto broker, replay producer, inference worker, event/metric recorder and FastAPI health service. Pin image digests and package versions before a tagged release.
3. Load 500--1000 held-out input rows for a smoke demo only, emit e.g. 1, 10 and 50 messages/sec on an isolated lab broker; time replay independently of original event time. Quantify the replay's selection bias and forbid using the demo subset for paper accuracy estimates.
4. Measure each event's send, broker receive (when available), inference start/end and dashboard delivery timestamps. For multi-host clocks, use NTP synchronization or explicitly restrict latency measurements to single-host monotonic clocks.
5. Show the Vercel dashboard: status and tier, throughput, attack distribution, live alerts, model/version/provenance, p50/p95/p99 inference and end-to-end latency, benign false-positive rate only if independent ground-truth labels exist, dropped/duplicate events, CPU/RSS, adaptation events and NOT MEASURED sections.
6. Introduce a controlled synthetic distribution-shift segment in replay only if labeled as *injected simulation* and separated from a genuine dataset chronological study. Validate alarms against predeclared injection boundaries; log false alarms in unshifted segments.
7. Repeat on named edge hardware if available (e.g. Raspberry Pi 5 or x86 mini-PC), recording CPU architecture, governor, temperature, memory, model loading/cold start, batch size, available threads and all package versions. No hardware -> NO EDGE HARDWARE RESULT.
8. Validate disconnect/reconnect, duplicate QoS 1 messages, corrupt payload, oversized payload, absent model, incompatible feature schema, unavailable HF service and API authentication. The system should fail closed, not invent predictions.

## 5. Tests and measurement definitions
Contract tests: JSON schema versions, unknown fields, feature order, missing features, physical units and privacy redaction.
Integration tests: Docker Compose start/health, producer->broker->worker->store->API->dashboard with synthetic fixtures. Run a minimal offline mode in CI; run external-container integration in a separate job when CI capabilities permit.
Security tests: broker rejects anonymous connections, topic ACL isolation, secrets absent from logs, authenticated portal-to-backend requests and hard limits on public requests.
Measurement: warm inference p50/p95/p99 after >=3 warmups and >=100 timed repetitions; cold-start separately, fixed batches and thread count. Broker-to-alert and send-to-dashboard latency require precisely defined clocks. Record sustained throughput and alerts lost/delayed under overload. Hardware energy requires an actual power-measurement instrument with baseline, sample rate and uncertainty.

## 6. Deployment and labeling policy
Public research portal may display a **secure read-only demo** plus reproducible prerecorded sanitized samples. Host the MQTT broker/inference worker on controlled backend infrastructure, not Vercel functions or an exposed public MQTT endpoint. The model card must disclose input features, dataset license, intended use, failure modes and simulated/live distinction. A Vercel deployment establishes website availability only; it does not certify cybersecurity protection or continuous real-time reliability.
