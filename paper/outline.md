# Manuscript outline (working)

Working title: *DriftGuard-IoT: Trustworthy, Drift-Aware and Resource-Efficient Intrusion
Detection Across IoT and IIoT Environments*

> Planning document. It contains no results. Figures and tables are generated only from
> verified experiment artifacts (research-kind manifests).

1. **Introduction.** The gap between static, random-split IDS benchmarks and deployment
   conditions (temporal drift, domain shift, constrained hardware). Contributions are
   phrased as questions (RQ1–RQ6) until results exist.
2. **Related work.** Lightweight ML for IoT/IIoT IDS, including the reference study.
   Concept-drift detection and adaptation. Cross-dataset IDS generalisation.
   Resource-aware IDS. Positioning is derived from `literature-matrix.md`.
3. **Datasets.** TON_IoT, WUSTL-IIOT-2021 and Edge-IIoTset: provenance, license,
   versions, fingerprints, class distributions, timestamp validity, aligned schema.
4. **Methodology.** Leakage-safe protocol, the reproduced baselines, the extension (drift
   detector and adaptation policy) and evaluation designs. See `methodology.md`.
5. **Experimental setup.** Hardware, software versions, seeds, hyperparameters and the
   experiment matrix (`experiment-matrix.md`).
6. **Results.**
   - 6.1 RQ1: in-distribution baselines.
   - 6.2 RQ2: chronological and cross-dataset evaluation; minority-class recall.
   - 6.3 RQ3: drift detector evaluation.
   - 6.4 RQ4: adaptation policy vs static and periodic retraining.
   - 6.5 RQ5: resource trade-offs.
   - 6.6 RQ6: feature stability and explanations.
7. **Discussion.** Includes the comparison with the reference paper's reported numbers,
   with any protocol differences stated explicitly.
8. **Limitations and threats to validity.** See `limitations.md`.
9. **Conclusion.**
10. **Reproducibility statement.** Code, configs, manifests and artifact links.
