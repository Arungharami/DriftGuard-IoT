"""MQTT 5.0 transport (paho-mqtt 2.x) for the replay producer and inference worker.

Credentials come from the environment only and are never logged. QoS 1 is used for
features and alerts. QoS 1 may redeliver, so consumers deduplicate by ``event_id``. The
worker uses a persistent session (``clean_start=False`` plus a session expiry) so that
QoS 1 messages published while it is briefly disconnected are delivered on reconnect.
"""

from __future__ import annotations

import os
import ssl
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties

QOS = 1


class MqttConnectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class MqttSettings:
    host: str = "127.0.0.1"
    port: int = 1883
    username: str | None = None
    password: str | None = None
    client_id: str = "driftguard"
    tls_ca_file: Path | None = None
    session_expiry_s: int = 0
    keepalive_s: int = 30

    @classmethod
    def from_env(cls, role: str, **overrides: Any) -> MqttSettings:
        """Read ``DRIFTGUARD_MQTT_<ROLE>_USERNAME``/``_PASSWORD`` plus host/port/TLS."""
        prefix = f"DRIFTGUARD_MQTT_{role.upper()}_"
        ca = os.environ.get("DRIFTGUARD_MQTT_TLS_CA")
        values: dict[str, Any] = {
            "host": os.environ.get("DRIFTGUARD_MQTT_HOST", "127.0.0.1"),
            "port": int(os.environ.get("DRIFTGUARD_MQTT_PORT", "1883")),
            "username": os.environ.get(prefix + "USERNAME"),
            "password": os.environ.get(prefix + "PASSWORD"),
            "client_id": f"driftguard-{role}",
            "tls_ca_file": Path(ca) if ca else None,
        }
        values.update(overrides)
        return cls(**values)

    def __repr__(self) -> str:  # never print the password
        return (
            f"MqttSettings(host={self.host!r}, port={self.port}, username={self.username!r}, "
            f"client_id={self.client_id!r}, tls={self.tls_ca_file is not None})"
        )


def connect(
    settings: MqttSettings,
    *,
    on_message: Callable[[str, bytes], None] | None = None,
    subscriptions: tuple[str, ...] = (),
    timeout_s: float = 10.0,
) -> mqtt.Client:
    """Connect, start the network loop and wait for CONNACK (and SUBACK) or raise."""
    client = mqtt.Client(
        CallbackAPIVersion.VERSION2,
        client_id=settings.client_id,
        protocol=mqtt.MQTTv5,
    )
    if settings.username is not None:
        client.username_pw_set(settings.username, settings.password)
    if settings.tls_ca_file is not None:
        client.tls_set(ca_certs=str(settings.tls_ca_file), tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.reconnect_delay_set(min_delay=1, max_delay=10)
    connected, failure = threading.Event(), []

    def on_connect(c: mqtt.Client, _u: Any, _f: Any, reason: Any, _p: Any) -> None:
        if reason.is_failure:
            failure.append(str(reason))
            connected.set()
            return
        for topic in subscriptions:  # (re)subscribe after every reconnect
            c.subscribe(topic, qos=QOS)
        connected.set()

    refused: dict[int, str] = {}

    def on_publish(_c: mqtt.Client, _u: Any, mid: int, reason: Any, _p: Any) -> None:
        if reason.is_failure:  # MQTT 5 PUBACK with e.g. "Not authorized" (ACL)
            refused[mid] = str(reason)

    client.user_data_set({"refused": refused})
    client.on_connect = on_connect
    client.on_publish = on_publish
    if on_message is not None:
        client.on_message = lambda _c, _u, msg: on_message(msg.topic, msg.payload)
    props = Properties(PacketTypes.CONNECT)  # type: ignore[no-untyped-call]
    if settings.session_expiry_s:
        props.SessionExpiryInterval = settings.session_expiry_s
    client.connect(
        settings.host,
        settings.port,
        keepalive=settings.keepalive_s,
        clean_start=settings.session_expiry_s == 0,
        properties=props,
    )
    client.loop_start()
    if not connected.wait(timeout_s) or failure:
        client.loop_stop()
        client.disconnect()
        raise MqttConnectionError(failure[0] if failure else "connection timed out")
    return client


def publish_confirmed(
    client: mqtt.Client, topic: str, payload: bytes, timeout_s: float = 10.0
) -> None:
    """Publish with QoS 1 and wait for PUBACK; raise if the broker refuses."""
    info = client.publish(topic, payload, qos=QOS)
    info.wait_for_publish(timeout=timeout_s)
    if not info.is_published():
        raise MqttConnectionError(f"publish to {topic} not acknowledged")
    reason = client.user_data_get()["refused"].pop(info.mid, None)
    if reason is not None:
        raise MqttConnectionError(f"publish to {topic} refused: {reason}")
