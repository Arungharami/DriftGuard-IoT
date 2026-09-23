"""``driftguard stream``: tier-A MQTT replay demonstration commands."""

from __future__ import annotations

import json
import signal
import threading
import time
from pathlib import Path
from typing import Annotated

import typer

stream_app = typer.Typer(
    help="Tier-A MQTT replay demo (synthetic fixture mode is NON-REPORTABLE).",
    no_args_is_help=True,
)

DEFAULT_DIR = Path(".local/stream")


@stream_app.command("broker-config")
def broker_config(
    out_dir: Annotated[Path, typer.Option(help="Git-ignored directory")] = DEFAULT_DIR / "broker",
    port: Annotated[int, typer.Option(min=1, max=65535)] = 1883,
    bind: Annotated[str, typer.Option(help="Non-loopback addresses require TLS")] = "127.0.0.1",
    tls_ca: Annotated[Path | None, typer.Option(exists=True, dir_okay=False)] = None,
    tls_cert: Annotated[Path | None, typer.Option(exists=True, dir_okay=False)] = None,
    tls_key: Annotated[Path | None, typer.Option(exists=True, dir_okay=False)] = None,
) -> None:
    """Write Mosquitto config, ACLs, hashed passwords and a 0600 credentials.env."""
    from driftguard.streaming.broker import TlsFiles, write_broker_files

    given = [tls_ca, tls_cert, tls_key]
    if any(given) and not all(given):
        raise typer.BadParameter("TLS needs --tls-ca, --tls-cert and --tls-key together")
    tls = TlsFiles(tls_ca, tls_cert, tls_key) if tls_ca and tls_cert and tls_key else None
    try:
        conf = write_broker_files(out_dir, port=port, bind=bind, tls=tls)
    except (ValueError, FileNotFoundError) as exc:
        typer.echo(f"ERROR: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"broker config: {conf}")
    typer.echo(f"credentials (mode 0600, never commit): {conf.parent / 'credentials.env'}")


@stream_app.command("demo-bundle")
def demo_bundle(
    out_dir: Annotated[Path, typer.Option()] = DEFAULT_DIR / "synthetic-bundle",
    config: Annotated[Path, typer.Option(exists=True, dir_okay=False)] = Path(
        "configs/experiments/stream-demo-synthetic.yaml"
    ),
) -> None:
    """Train the SYNTHETIC-fixture demo model and package it as a local verified bundle."""
    from driftguard.config import load_experiment_config
    from driftguard.experiments import run_experiment
    from driftguard.platform.bundle import prepare_bundle

    experiment = load_experiment_config(config)
    if experiment.dataset.is_registry:
        raise typer.BadParameter("demo-bundle is for synthetic configs; use a verified run")
    result = run_experiment(experiment, out_dir.parent / "synthetic-runs")
    meta = prepare_bundle(Path(result["run_dir"]), experiment.models[0].name, out_dir)
    typer.echo(f"bundle {meta['model_version']} at {out_dir} (synthetic_data=True, NON-REPORTABLE)")


@stream_app.command()
def worker(
    bundle: Annotated[
        Path | None, typer.Option(help="Verified bundle; omit to fail closed")
    ] = None,
    store: Annotated[Path, typer.Option()] = DEFAULT_DIR / "events.sqlite3",
    queue_size: Annotated[int, typer.Option(min=1)] = 1000,
    rate_limit: Annotated[float | None, typer.Option(help="Max accepted messages/s")] = None,
    benign_label: Annotated[str | None, typer.Option(help="Enables the output monitor")] = None,
    max_seconds: Annotated[float | None, typer.Option(help="Stop after N seconds")] = None,
) -> None:
    """Subscribe to feature topics, infer, store and publish alerts (QoS 1)."""
    from driftguard.platform.bundle import load_bundle
    from driftguard.streaming.contract import (
        FEATURE_SUBSCRIPTION,
        HEALTH_TOPIC,
        Alert,
        alerts_topic,
    )
    from driftguard.streaming.mqtt import MqttSettings, connect
    from driftguard.streaming.store import EventStore
    from driftguard.streaming.worker import InferenceWorker, OutputShiftMonitor

    loaded = load_bundle(bundle) if bundle else None
    events = EventStore(store)
    engine = InferenceWorker(
        events,
        loaded,
        monitor=OutputShiftMonitor(benign_label) if benign_label else None,
        queue_size=queue_size,
        rate_limit_per_s=rate_limit,
    )

    def receive(topic: str, payload: bytes) -> None:
        engine.submit(payload, topic)

    client = connect(
        MqttSettings.from_env("worker", session_expiry_s=3600),
        on_message=receive,
        subscriptions=(FEATURE_SUBSCRIPTION,),
    )

    def publish(topic: str, alert: Alert) -> None:
        device = topic.rsplit("/", 1)[-1] or "unknown"
        client.publish(alerts_topic(device), alert.model_dump_json(), qos=1)

    health = {
        "status": "ready" if loaded else "model_unavailable",
        "model_sha256": loaded.model_sha256 if loaded else None,
        "synthetic_model": loaded.synthetic if loaded else None,
    }
    client.publish(HEALTH_TOPIC, json.dumps(health), qos=1, retain=True)
    stop = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    if max_seconds:
        threading.Timer(max_seconds, stop.set).start()
    typer.echo(f"worker running ({health['status']}); Ctrl-C to stop")
    try:
        engine.run(stop, publish)
    finally:
        client.loop_stop()
        client.disconnect()
        typer.echo(json.dumps(events.summary(), indent=2, default=str))
        events.close()


@stream_app.command()
def replay(
    bundle: Annotated[Path, typer.Option(exists=True, file_okay=False)],
    source: Annotated[str, typer.Option(help="synthetic | heldout")] = "synthetic",
    run_dir: Annotated[Path | None, typer.Option(help="Verified real run (heldout)")] = None,
    rate: Annotated[float, typer.Option(min=0.1, max=1000)] = 10.0,
    max_events: Annotated[int, typer.Option(min=1)] = 500,
    device: Annotated[str, typer.Option()] = "lab-replay-01",
) -> None:
    """Publish feature messages at a fixed imposed rate (never original event time)."""
    from driftguard.streaming.contract import features_topic
    from driftguard.streaming.mqtt import MqttSettings, connect, publish_confirmed
    from driftguard.streaming.replay import held_out_source, synthetic_source
    from driftguard.streaming.replay import replay as run_replay

    if source == "synthetic":
        src = synthetic_source(bundle, n=max_events)
        feed = src.feed
    elif source == "heldout" and run_dir is not None:
        src = held_out_source(run_dir)
        feed = src.feed
    else:
        raise typer.BadParameter("use --source synthetic, or --source heldout --run-dir RUN")
    topic = features_topic(feed, device)
    client = connect(MqttSettings.from_env("replay"))
    try:
        stats = run_replay(
            src,
            lambda payload: publish_confirmed(client, topic, payload),
            rate_per_s=rate,
            max_events=max_events,
        )
    finally:
        time.sleep(0.2)
        client.loop_stop()
        client.disconnect()
    typer.echo(json.dumps({"source": src.description, **stats}, indent=2))


@stream_app.command()
def api(
    store: Annotated[Path, typer.Option()] = DEFAULT_DIR / "events.sqlite3",
    host: Annotated[str, typer.Option()] = "127.0.0.1",
    port: Annotated[int, typer.Option()] = 8765,
) -> None:
    """Serve the read-only summary API (token from DRIFTGUARD_DEMO_API_TOKEN)."""
    import os

    import uvicorn

    from driftguard.streaming.api import create_demo_api

    app = create_demo_api(store, token=os.environ.get("DRIFTGUARD_DEMO_API_TOKEN"))
    uvicorn.run(app, host=host, port=port, log_level="warning")
