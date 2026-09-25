"""Integration against a real Mosquitto 2.x broker with generated credentials and ACLs.

Skipped when no ``mosquitto`` binary is installed. All traffic is SYNTHETIC fixture data
on a loopback listener. Nothing here is research evidence.
"""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from driftguard.platform.bundle import LoadedBundle
from driftguard.streaming.broker import (
    TlsFiles,
    find_mosquitto_tool,
    render_config,
    write_broker_files,
)
from driftguard.streaming.contract import FEATURE_SUBSCRIPTION, Alert, alerts_topic, features_topic
from driftguard.streaming.mqtt import MqttConnectionError, MqttSettings, connect, publish_confirmed
from driftguard.streaming.replay import encode_messages, replay, synthetic_source
from driftguard.streaming.store import EventStore
from driftguard.streaming.worker import InferenceWorker

try:
    MOSQUITTO = find_mosquitto_tool("mosquitto")
    find_mosquitto_tool("mosquitto_passwd")
except FileNotFoundError:
    MOSQUITTO = None

pytestmark = [
    pytest.mark.mqtt,
    pytest.mark.skipif(MOSQUITTO is None, reason="mosquitto binary not installed"),
]
TOPIC = features_topic("synthetic", "lab-test-01")


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait(predicate: Callable[[], bool], timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return predicate()


@dataclass
class Broker:
    conf: Path
    port: int
    creds: dict[str, str]
    process: subprocess.Popen[bytes] | None = None

    def start(self) -> None:
        assert MOSQUITTO is not None
        self.process = subprocess.Popen(  # noqa: S603
            [str(MOSQUITTO), "-c", str(self.conf)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ready = _wait(lambda: socket.socket().connect_ex(("127.0.0.1", self.port)) == 0, 10)
        assert ready, "broker did not start"

    def stop(self) -> None:
        if self.process is not None:
            self.process.terminate()
            self.process.wait(timeout=10)
            self.process = None

    def settings(self, role: str, **overrides: object) -> MqttSettings:
        base = MqttSettings(
            port=self.port,
            username=self.creds[f"DRIFTGUARD_MQTT_{role.upper()}_USERNAME"],
            password=self.creds[f"DRIFTGUARD_MQTT_{role.upper()}_PASSWORD"],
            client_id=f"test-{role}",
        )
        return replace(base, **overrides)  # type: ignore[arg-type]


@pytest.fixture
def broker(tmp_path: Path) -> Iterator[Broker]:
    port = _free_port()
    conf = write_broker_files(tmp_path / "broker", port=port)
    creds = dict(
        line.split("=", 1) for line in (conf.parent / "credentials.env").read_text().splitlines()
    )
    b = Broker(conf, port, creds)
    b.start()
    yield b
    b.stop()


@pytest.fixture
def running_worker(
    broker: Broker, bundle: LoadedBundle, tmp_path: Path
) -> Iterator[tuple[InferenceWorker, list[Alert]]]:
    store = EventStore(tmp_path / "events.sqlite3")
    worker = InferenceWorker(store, bundle)
    published: list[Alert] = []
    client = connect(
        broker.settings("worker", session_expiry_s=300),
        on_message=lambda topic, payload: worker.submit(payload, topic) and None,
        subscriptions=(FEATURE_SUBSCRIPTION,),
    )

    def publish(topic: str, alert: Alert) -> None:
        client.publish(alerts_topic(topic.rsplit("/", 1)[-1]), alert.model_dump_json(), qos=1)
        published.append(alert)

    stop = threading.Event()
    thread = threading.Thread(target=worker.run, args=(stop, publish), daemon=True)
    thread.start()
    time.sleep(0.3)  # SUBACK
    yield worker, published
    stop.set()
    thread.join(timeout=10)
    client.loop_stop()
    client.disconnect()
    store.close()


def _predicted(worker: InferenceWorker) -> int:
    return int(worker.store.summary()["events_by_status"].get("predicted", 0))


def test_generated_config_is_least_privilege(tmp_path: Path) -> None:
    text = render_config(tmp_path, port=1883)
    assert "allow_anonymous false" in text and "listener 1883 127.0.0.1" in text
    with pytest.raises(ValueError, match="TLS"):
        render_config(tmp_path, port=1883, bind="0.0.0.0")  # noqa: S104
    conf = write_broker_files(tmp_path / "b", port=1883)
    for name in ("passwords", "acl", "mosquitto.conf", "credentials.env"):
        assert (conf.parent / name).stat().st_mode & 0o077 == 0, name
    assert "DRIFTGUARD_MQTT_WORKER_PASSWORD" in (conf.parent / "credentials.env").read_text()


def test_anonymous_and_wrong_password_are_refused(broker: Broker) -> None:
    with pytest.raises(MqttConnectionError):
        connect(MqttSettings(port=broker.port, client_id="anon"), timeout_s=5)
    with pytest.raises(MqttConnectionError):
        connect(broker.settings("replay", password="wrong", client_id="bad"), timeout_s=5)  # noqa: S106


def test_acl_blocks_producer_from_alert_topic(broker: Broker) -> None:
    client = connect(broker.settings("replay"))
    try:
        publish_confirmed(client, TOPIC, b"{}")  # permitted topic
        with pytest.raises(MqttConnectionError, match="refused"):
            publish_confirmed(client, alerts_topic("lab-test-01"), b"{}")
    finally:
        client.loop_stop()
        client.disconnect()


def test_end_to_end_replay_through_broker(
    broker: Broker, bundle: LoadedBundle, running_worker: tuple[InferenceWorker, list[Alert]]
) -> None:
    worker, _published = running_worker
    received: list[dict[str, object]] = []
    monitor = connect(
        broker.settings("monitor"),
        on_message=lambda _t, p: received.append(json.loads(p)),
        subscriptions=(alerts_topic("lab-test-01"),),
    )
    producer = connect(broker.settings("replay"))
    try:
        time.sleep(0.3)
        stats = replay(
            synthetic_source(bundle.path, n=60),
            lambda payload: publish_confirmed(producer, TOPIC, payload),
            rate_per_s=100.0,
        )
        assert stats["sent"] == 60
        assert _wait(lambda: _predicted(worker) == 60 and len(received) == 60)
    finally:
        for c in (producer, monitor):
            c.loop_stop()
            c.disconnect()
    summary = worker.store.summary()
    assert summary["events_by_status"] == {"predicted": 60}
    assert summary["events_by_evidence_tier"] == {"synthetic_fixture": 60}
    assert summary["inference_ms"]["n"] == 60 and summary["end_to_end_ms"]["n"] == 60
    assert all(a["reportable"] is False and a["status"] == "predicted" for a in received)


def test_qos1_duplicate_and_oversized_payloads(
    broker: Broker, bundle: LoadedBundle, running_worker: tuple[InferenceWorker, list[Alert]]
) -> None:
    worker, _ = running_worker
    payload = next(encode_messages(synthetic_source(bundle.path, n=1)))[1]
    producer = connect(broker.settings("replay"))
    try:
        publish_confirmed(producer, TOPIC, payload)
        publish_confirmed(producer, TOPIC, payload)  # simulated redelivery
        publish_confirmed(producer, TOPIC, b"{not json")
        assert _wait(lambda: worker.store.summary()["counters"].get("rejected_malformed") == 1)
    finally:
        producer.loop_stop()
        producer.disconnect()
    oversized = connect(broker.settings("replay", client_id="test-big"))
    try:
        with pytest.raises(MqttConnectionError):
            publish_confirmed(oversized, TOPIC, b"x" * 40_000, timeout_s=3)
    finally:
        oversized.loop_stop()
        oversized.disconnect()
    time.sleep(0.3)
    summary = worker.store.summary()
    assert summary["events_by_status"] == {"predicted": 1}
    assert summary["counters"]["duplicates_suppressed"] == 1
    assert "rejected_oversized" not in summary["counters"]  # broker dropped it first


def test_persistent_session_delivers_messages_sent_while_worker_offline(
    broker: Broker, bundle: LoadedBundle, tmp_path: Path
) -> None:
    store = EventStore(tmp_path / "offline.sqlite3")
    worker = InferenceWorker(store, bundle)
    settings = broker.settings("worker", session_expiry_s=300, client_id="test-persistent")

    def receive(topic: str, payload: bytes) -> None:
        worker.submit(payload, topic)

    first = connect(settings, on_message=receive, subscriptions=(FEATURE_SUBSCRIPTION,))
    time.sleep(0.3)
    first.loop_stop()
    first.disconnect()  # session survives on the broker (expiry 300 s)
    producer = connect(broker.settings("replay"))
    for _, payload in encode_messages(synthetic_source(bundle.path, n=15)):
        publish_confirmed(producer, TOPIC, payload)
    producer.loop_stop()
    producer.disconnect()
    second = connect(settings, on_message=receive, subscriptions=(FEATURE_SUBSCRIPTION,))
    stop = threading.Event()
    thread = threading.Thread(target=worker.run, args=(stop,), daemon=True)
    thread.start()
    try:
        assert _wait(lambda: _predicted(worker) == 15)
    finally:
        stop.set()
        thread.join(timeout=10)
        second.loop_stop()
        second.disconnect()
        store.close()


def test_worker_recovers_after_broker_restart(
    broker: Broker, bundle: LoadedBundle, running_worker: tuple[InferenceWorker, list[Alert]]
) -> None:
    """Broker persistence keeps the worker's session and subscription across a restart,
    so messages published before the worker has reconnected are queued, not lost."""
    worker, _ = running_worker
    broker.stop()
    broker.start()
    producer = connect(broker.settings("replay"))
    try:
        for _, payload in encode_messages(synthetic_source(bundle.path, n=10)):
            publish_confirmed(producer, TOPIC, payload)
        assert _wait(lambda: _predicted(worker) == 10, 30)
    finally:
        producer.loop_stop()
        producer.disconnect()


def _self_signed_ca_and_server_cert(directory: Path) -> TlsFiles:
    """Throwaway test CA and a server certificate for 127.0.0.1 (never reused)."""
    directory.mkdir(parents=True, exist_ok=True)
    ca_key, ca_crt = directory / "ca.key", directory / "ca.crt"
    key, csr, crt = directory / "server.key", directory / "server.csr", directory / "server.crt"
    ext = directory / "san.ext"
    ext.write_text("subjectAltName=IP:127.0.0.1\n")
    run = lambda *args: subprocess.run(["openssl", *args], check=True, capture_output=True)  # noqa: E731, S603, S607
    run(
        "req",
        "-x509",
        "-newkey",
        "rsa:2048",
        "-nodes",
        "-days",
        "1",
        "-subj",
        "/CN=test-ca",
        "-keyout",
        str(ca_key),
        "-out",
        str(ca_crt),
    )
    run(
        "req",
        "-newkey",
        "rsa:2048",
        "-nodes",
        "-subj",
        "/CN=127.0.0.1",
        "-keyout",
        str(key),
        "-out",
        str(csr),
    )
    run(
        "x509",
        "-req",
        "-in",
        str(csr),
        "-CA",
        str(ca_crt),
        "-CAkey",
        str(ca_key),
        "-CAcreateserial",
        "-days",
        "1",
        "-extfile",
        str(ext),
        "-out",
        str(crt),
    )
    return TlsFiles(cafile=ca_crt, certfile=crt, keyfile=key)


@pytest.mark.skipif(shutil.which("openssl") is None, reason="openssl not installed")
def test_tls_listener_accepts_only_verified_tls_clients(tmp_path: Path) -> None:
    tls = _self_signed_ca_and_server_cert(tmp_path / "pki")
    port = _free_port()
    conf = write_broker_files(tmp_path / "broker", port=port, tls=tls)
    creds = dict(
        line.split("=", 1) for line in (conf.parent / "credentials.env").read_text().splitlines()
    )
    broker = Broker(conf, port, creds)
    broker.start()
    try:
        client = connect(broker.settings("replay", tls_ca_file=tls.cafile))
        publish_confirmed(client, TOPIC, b"{}")
        client.loop_stop()
        client.disconnect()
        with pytest.raises((MqttConnectionError, OSError)):  # plaintext to a TLS listener
            connect(broker.settings("replay", client_id="plain"), timeout_s=3)
        other = _self_signed_ca_and_server_cert(tmp_path / "other-pki")
        with pytest.raises((MqttConnectionError, OSError)):  # untrusted server certificate
            connect(broker.settings("replay", client_id="x", tls_ca_file=other.cafile), timeout_s=3)
    finally:
        broker.stop()
