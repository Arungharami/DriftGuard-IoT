# Experiment run outputs

Each run writes to `experiments/runs/<run_id>/` with a `manifest.json` (config hash, seed,
data fingerprints, software environment) and its metrics. Contents of this directory are
git-ignored. Only runs whose manifest has `kind: "research"` may be promoted into the
versioned results consumed by the portal and the manuscript (see
[docs/scientific-protocol.md](../docs/scientific-protocol.md)).
