# Reference paper: verified methodology

**Paper:** S. Ismail, S. Dandan, A. Qushou. *Intrusion Detection in IoT and IIoT: Comparing
Lightweight Machine Learning Techniques Using TON_IoT, WUSTL-IIOT-2021, and EdgeIIoTset
Datasets.* IEEE Access 13 (2025) 73468–73485. doi:10.1109/ACCESS.2025.3554083.
Open access under CC BY 4.0 (Crossref license record).

**Verified:** 2026-09-22, from the full-text PDF. Tables 4–8 and Figures 2–4 were read
from rendered page images. The PDF itself is not committed. Machine-readable facts are in
[`src/driftguard/preprocessing/paper_protocol.py`](../src/driftguard/preprocessing/paper_protocol.py).

## What the paper states

| Item | Paper | Location |
| --- | --- | --- |
| Task | Multi-class attack-type classification | Sec. I, Table 4 |
| Models | DT, RF, Bagging, Stacking, LightGBM | Sec. III-C |
| Stacking | DT and RF as base estimators, MLP as final estimator | Sec. III-C |
| Hyperparameters | **Not reported** | — |
| Encoding | scikit-learn `LabelEncoder` on remaining features | Sec. III-A-1 |
| Feature selection | Mutual information, features with score < 0.1 removed | Sec. III-A |
| Resampling | SMOTE for classes whose target exceeds their count, then `RandomUnderSampler`; `random_state=42`; targets keep class proportions at about 450,000 rows | Sec. III-B, Table 4 |
| Split | 70:30 train/test | Sec. III-B |
| Metrics | Precision, Recall, Micro-F1, Model Size, Training Time | Sec. IV, Table 7 |
| Cross-dataset | TON_IoT → WUSTL on 7 shared features, labels Normal/DoS/Backdoor | Sec. V, Table 8 |

## Dataset facts checked against the official files

| Dataset | Paper Table 4 (original) | Official file (2026-09-22) |
| --- | --- | --- |
| TON_IoT | 211,043 rows (Train_Test network subset) | **Not downloaded** (UNSW SharePoint requires Microsoft sign-in) |
| WUSTL-IIOT-2021 | 1,194,464 rows; Normal 1,107,448, DoS 78,305, Reconnaissance 8,240, Command Injection 259, Backdoor 212 | Identical row and class counts |
| Edge-IIoTset | 157,800 rows; 15 classes | Identical row and all 15 class counts (ML-EdgeIIoT table) |

This confirms that the paper used WUSTL's full table and Edge-IIoTset's `ML-EdgeIIoT-dataset.csv`.

## Where the text and the figures disagree

The implementation follows the figures, because they show what was actually computed:

1. **TON_IoT.** The text says `src_port` and `dst_port` were removed, but Fig. 2 plots MI for
   both (each near 1.0).
2. **WUSTL-IIOT-2021.** The text says `sIpId` and `dIpId` were removed (as the publisher
   instructs), but Fig. 3 includes them. The reported 20% dimensionality reduction
   (43 → 38 of 48 features) matches the figure. **Verified:** the 43 numeric non-label
   columns of the official file are exactly Fig. 3's features.
3. **Edge-IIoTset.** Table 5 lists `tcp.dstport`, `udp.port` and `icmp.transmit_timestamp`
   as removed before MI, yet Fig. 4 includes all three. **Verified:** the 42 numeric
   non-label columns of the full official ML table are exactly Fig. 4's features.
4. The paper's MI universe is therefore *numeric-dtype columns*: `LabelEncoder` was
   evidently not applied to the object columns that appear in no figure.

## Leakage risks in the paper's protocol

The order of Sec. III (feature selection, then resampling to about 450k "model-ready" rows,
then the 70:30 split) implies that:

- MI scores were computed on all rows, including future test rows.
- SMOTE and undersampling were applied before the split, so SMOTE-generated rows (and the
  real neighbours they were interpolated from) can appear in both partitions. The
  synthetic development runs confirm synthetic rows land in the test partition.
- No deduplication is performed. Edge-IIoTset's ML table has **814 exact duplicate rows**.
- Identifier-like fields are used as features: ports, and WUSTL's IP-ID fields, which the
  WUSTL publisher says expose the attack type.

**A leak the paper did not report (found 2026-09-22):** in Edge-IIoTset,
`dns.qry.name.len`, `mqtt.conack.flags` and `mqtt.protoname` hold `'0'` in every normal row
and `'0.0'` in every attack row (label purity 1.0). This is a CSV export artifact that
encodes the label. The paper's numeric-only MI universe happens to exclude these columns.
The leakage-safe protocol excludes them explicitly and canonicalises numeric-looking
categories.

## How this project uses these facts

- `paper_faithful` reproduces the paper's order of operations only to measure its
  effect. Its outputs are always `NON-REPORTABLE` as leakage-safe results.
- `leakage_safe` uses the same components (MI ≥ 0.1, proportional SMOTE and
  undersampling), with deduplication first, the split before any fitting, and every
  stateful step fitted on the training partition only.
