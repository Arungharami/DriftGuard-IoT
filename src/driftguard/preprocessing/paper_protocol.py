"""The reference study's preprocessing protocol, as verified from its full text.

Source: Ismail, Dandan & Qushou, IEEE Access 13 (2025) 73468-73485,
doi:10.1109/ACCESS.2025.3554083 (CC BY 4.0), read 2026-09-22. Each fact below cites the
section, table or figure it comes from. Where the text and the figures disagree, the
figures are followed, because the figures show what was actually computed. Every such
disagreement is listed in ``KNOWN_DISCREPANCIES``.

The paper's order of operations leaks test information (see ``PAPER_LEAKAGE_RISKS``).
The ``paper_faithful`` protocol reproduces that order only so that its effect can be
measured. Its outputs are never reportable as leakage-safe results.
"""

from __future__ import annotations

from dataclasses import dataclass, field

PAPER_DOI = "10.1109/ACCESS.2025.3554083"
MI_THRESHOLD = 0.1  # Sec. III-A: "A threshold of 0.1 was selected for MI-based feature selection"
RESAMPLE_RANDOM_STATE = 42  # Sec. III-B: "a random_state of 42 was set for reproducibility"
TEST_SIZE = 0.30  # Sec. III-B: "A 70:30 train-test split was applied"
STACKING = "DT + RF base estimators, MLP final estimator"  # Sec. III-C


@dataclass(frozen=True)
class PaperDatasetProtocol:
    dataset_id: str
    target_column: str  # multi-class attack type (Table 4 class labels)
    original_rows: int  # Table 4 "Original Data / Total Size"
    model_ready_rows: int  # Table 4 "Model-Ready Data / Total Size"
    # Columns excluded before MI, beyond non-numeric columns (see ``mi_universe``).
    pre_mi_drop: tuple[str, ...]
    # Features the paper reports removing for MI < 0.1 (text / Table 6).
    reported_mi_removed: tuple[str, ...]
    # Features shown in the paper's MI figure (what MI was actually computed on).
    figure_mi_features: tuple[str, ...]
    figure: str
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def resample_ratio(self) -> float:
        """Model-ready size / original size. Used to scale bounded development runs."""
        return self.model_ready_rows / self.original_rows


TON_IOT = PaperDatasetProtocol(
    dataset_id="ton_iot",
    target_column="type",
    original_rows=211_043,
    model_ready_rows=449_996,
    pre_mi_drop=("ts", "label"),
    reported_mi_removed=(
        "dns_rcode",
        "missed_bytes",
        "http_status_code",
        "http_response_body_len",
        "http_request_body_len",
    ),
    figure_mi_features=(
        "src_ip_bytes",
        "dst_port",
        "dst_ip_bytes",
        "src_port",
        "duration",
        "src_bytes",
        "dst_bytes",
        "dst_pkts",
        "src_pkts",
        "dns_qtype",
        "dns_qclass",
        "dns_rcode",
        "missed_bytes",
        "http_status_code",
        "http_response_body_len",
        "http_request_body_len",
    ),
    figure="Fig. 2",
    notes=(
        "Text says src_ip, dst_ip, src_port and dst_port were removed, but Fig. 2 shows MI "
        "computed on src_port and dst_port (both near 1.0), so they were retained.",
        "MI universe = numeric columns minus ts and label, inferred from Fig. 2. It cannot "
        "be checked against the file until TON_IoT is downloaded.",
    ),
)

WUSTL_IIOT_2021 = PaperDatasetProtocol(
    dataset_id="wustl_iiot_2021",
    target_column="Traffic",
    original_rows=1_194_464,
    model_ready_rows=449_997,
    pre_mi_drop=("Target",),
    reported_mi_removed=("Mean", "Proto", "DstJitAct", "sTos", "sDSb"),
    figure_mi_features=(
        "sTtl",
        "pLoss",
        "dTtl",
        "SrcBytes",
        "TotBytes",
        "Load",
        "Dport",
        "SrcLoad",
        "SAppBytes",
        "TotAppByte",
        "SIntPkt",
        "Rate",
        "SrcRate",
        "TotPkts",
        "Dur",
        "Max",
        "Sum",
        "RunTime",
        "Min",
        "SrcPkts",
        "IdleTime",
        "DstPkts",
        "DstBytes",
        "SrcJitter",
        "DIntPkt",
        "Sport",
        "DstLoss",
        "DstRate",
        "DstLoad",
        "DAppBytes",
        "DstJitter",
        "TcpRtt",
        "SynAck",
        "dIpId",
        "sIpId",
        "Loss",
        "SrcLoss",
        "SrcJitAct",
        "Mean",
        "Proto",
        "DstJitAct",
        "sTos",
        "sDSb",
    ),
    figure="Fig. 3",
    notes=(
        "Text says StartTime, LastTime, SrcAddr, DstAddr, sIpId and dIpId were removed, as "
        "the publisher instructs. Fig. 3 nevertheless includes sIpId and dIpId, and the 20% "
        "dimensionality reduction (43 -> 38 of 48) is consistent with the figure, not the text.",
        "Verified 2026-09-22: the 43 numeric non-label columns of the official file are "
        "exactly the Fig. 3 features.",
    ),
)

EDGE_IIOTSET = PaperDatasetProtocol(
    dataset_id="edge_iiotset",
    target_column="Attack_type",
    original_rows=157_800,
    model_ready_rows=449_991,
    pre_mi_drop=("Attack_label",),
    reported_mi_removed=(  # Table 6 (28 entries as printed)
        "tcp.connection.rst",
        "http.response",
        "mqtt.msgtype",
        "mqtt.hdrflags",
        "tcp.connection.fin",
        "mqtt.len",
        "tcp.connection.synack",
        "dns.qry.name",
        "mqtt.topic_len",
        "mqtt.conflags",
        "arp.hw.size",
        "arp.opcode",
        "mqtt.conflag.cleansess",
        "mqtt.proto_len",
        "mqtt.ver",
        "udp.port",
        "udp.time_delta",
        "dns.qry.qu",
        "icmp.transmit_timestamp",
        "mbtcp.trans_id",
        "mqtt.msg_decoded_as",
        "http.tls_port",
        "icmp.unused",
        "dns.retransmission",
        "dns.qry.type",
        "mbtcp.len",
        "mbtcp.unit_id",
        "dns.retransmit_request_in",
    ),
    figure_mi_features=(
        "tcp.dstport",
        "tcp.ack",
        "tcp.ack_raw",
        "tcp.seq",
        "tcp.flags",
        "tcp.len",
        "tcp.checksum",
        "udp.stream",
        "tcp.flags.ack",
        "icmp.checksum",
        "icmp.seq_le",
        "http.content_length",
        "tcp.connection.syn",
        "tcp.connection.rst",
        "http.response",
        "mqtt.msgtype",
        "mqtt.hdrflags",
        "tcp.connection.fin",
        "mqtt.len",
        "dns.qry.name",
        "tcp.connection.synack",
        "mqtt.topic_len",
        "mqtt.conflags",
        "arp.hw.size",
        "arp.opcode",
        "mqtt.proto_len",
        "mqtt.conflag.cleansess",
        "mqtt.ver",
        "udp.port",
        "udp.time_delta",
        "dns.qry.qu",
        "icmp.transmit_timestamp",
        "mbtcp.trans_id",
        "dns.retransmit_request_in",
        "dns.retransmit_request",
        "mqtt.msg_decoded_as",
        "http.tls_port",
        "icmp.unused",
        "dns.retransmission",
        "dns.qry.type",
        "mbtcp.len",
        "mbtcp.unit_id",
    ),
    figure="Fig. 4",
    notes=(
        "Table 5 lists tcp.dstport, udp.port and icmp.transmit_timestamp as removed before "
        "MI, yet all three appear in Fig. 4.",
        "Verified 2026-09-22: the 42 numeric non-label columns of the full official ML table "
        "(pandas dtypes) are exactly the Fig. 4 features.",
    ),
)

PAPER_PROTOCOLS: dict[str, PaperDatasetProtocol] = {
    p.dataset_id: p for p in (TON_IOT, WUSTL_IIOT_2021, EDGE_IIOTSET)
}

# Section III order: feature selection (III-A) on the whole dataset, then resampling of the
# whole dataset to ~450k rows (III-B, Table 4 "model-ready"), then the 70:30 split.
PAPER_LEAKAGE_RISKS: tuple[str, ...] = (
    "MI feature selection is computed on the full dataset before the train/test split.",
    "SMOTE and RandomUnderSampler are applied to the full dataset before the split, so "
    "synthetic SMOTE samples, and the real neighbours they were interpolated from, can "
    "appear in both train and test partitions.",
    "Duplicates are not removed; Edge-IIoTset's ML table contains 814 exact duplicate rows "
    "(verified 2026-09-22), which can straddle the split.",
    "Identifier-like fields are used as features: ports (TON_IoT Fig. 2; Edge-IIoTset "
    "tcp.dstport) and IP-ID fields (WUSTL sIpId, dIpId), which the WUSTL publisher says "
    "expose the attack type.",
    "Hyperparameters are not reported; library defaults are assumed.",
)

KNOWN_DISCREPANCIES: tuple[str, ...] = tuple(
    note for p in PAPER_PROTOCOLS.values() for note in p.notes
)
