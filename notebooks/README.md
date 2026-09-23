# Notebooks (M7)

Planned Colab notebooks, each a thin wrapper that installs the package at a pinned commit
and calls `driftguard` functions. No algorithm is re-implemented in a notebook.

| Notebook | Purpose |
| --- | --- |
| `01_dataset_validation.ipynb` | Retrieve (user credentials), fingerprint, and validate schemas |
| `02_baseline_training.ipynb` | Train the five baselines from experiment configs |
| `03_cross_domain_evaluation.ipynb` | Chronological and cross-dataset evaluation |
| `04_drift_experiments.ipynb` | Drift detector and adaptation-policy simulations |
| `05_resource_benchmarking.ipynb` | Latency, memory and throughput measurements |

Every notebook supports a bounded development sample (`--dev-sample N`) before a full run,
writes run manifests, and checkpoints expensive steps to Google Drive. Committed
notebooks must be stripped of outputs.
