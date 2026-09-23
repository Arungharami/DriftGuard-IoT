# Datasets: acquisition, verification and quality workflow

All commands run from the repository root with the package installed. Data lives under
`data/` (git-ignored) or under `$DRIFTGUARD_DATA_ROOT`.

## Acquisition status (2026-09-22)

| Dataset | Status |
| --- | --- |
| WUSTL-IIOT-2021 | Official archive downloaded (106,192,911 bytes, as stated by the publisher); schema confirmed; SHA-256 recorded in the card |
| Edge-IIoTset | ML table downloaded via the adapter (82,184,390 bytes, as in Kaggle metadata); schema confirmed; SHA-256 recorded |
| TON_IoT | **Blocked:** the UNSW SharePoint link redirects to a Microsoft sign-in, so a team member must download `train_test_network.csv` in a browser |

## License and provenance summary (checked 2026-09-22)

| Dataset | Source checked | License / terms | Academic | Commercial | Raw redistribution | Acquisition |
| --- | --- | --- | --- | --- | --- | --- |
| TON_IoT | [UNSW project page](https://research.unsw.edu.au/projects/toniot-datasets) | Publisher terms: free academic use; commercial use by permission; cite 8 papers | Permitted | Permission required | Not stated (not granted) | Manual (UNSW SharePoint) |
| WUSTL-IIOT-2021 | [WUSTL dataset page](http://www.cse.wustl.edu/~jain/iiot2/index.html) | **No license stated**; citation requested | Not stated | Not stated | Not stated | Manual (`wustl_iiot_2021.zip`, 106,192,911 bytes per page) |
| Edge-IIoTset | [First-party Kaggle upload](https://www.kaggle.com/datasets/mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot) | CC BY-NC-SA 4.0 (Kaggle license field; owner is the lead author) | Permitted | Prohibited (NC) | Permitted with conditions (BY-NC-SA) | Kaggle adapter |

`driftguard data show <id>` prints the verbatim terms excerpt and the required citations.
By project policy **raw data is never redistributed**, and trained or derived artifacts
are blocked by `driftguard.data.licensing.redistribution_decision` until a license
review marks them as permitted (see ADR 0002).

## 1. Acquire

```bash
driftguard data list
driftguard data show ton_iot                 # terms, citations, instructions
```

- **Edge-IIoTset (Kaggle).** Configure your own Kaggle credentials outside the repository
  (`~/.kaggle/kaggle.json`, or `KAGGLE_USERNAME`/`KAGGLE_KEY`), then:

  ```bash
  pip install -e ".[kaggle]"
  driftguard data check-license edge_iiotset     # live license check vs registry
  driftguard data download edge_iiotset --accept-license   # ML table only (~82 MB)
  ```

- **TON_IoT (manual).** Download the Train_Test network CSV from the UNSW page and save it
  under `data/raw/ton_iot/`.
- **WUSTL-IIOT-2021 (manual).** Download `wustl_iiot_2021.zip` from the WUSTL page into
  `data/raw/wustl_iiot_2021/`.

Do not use the Kaggle re-uploads of TON_IoT or WUSTL-IIOT-2021. They are not first-party
and several carry license labels the uploaders cannot grant.

## 2. Fingerprint

```bash
driftguard data fingerprint wustl_iiot_2021   # safely extracts .zip, hashes every file
```

This writes `data/manifests/<id>.json` and reports each table as
`match | mismatch | unrecorded | absent`. The first time, every table is `unrecorded`. To
make a fingerprint canonical, open a PR that sets the table's `sha256` in its card, with
the manifest and the download date in the PR description.

## 3. Validate the schema

```bash
driftguard data validate ton_iot --nrows 10000
pytest -m real_data            # header check for every downloaded table
```

Schemas are **provisional** until this passes against the real file. Once it passes, set
`schema_status: confirmed` in the card through a PR. On a mismatch, fix the card's column
list to match the real header. Never rename columns in the data.

## 4. Quality report

```bash
driftguard data quality edge_iiotset --nrows 200000   # bounded dev read
driftguard data quality edge_iiotset                  # full table
```

It writes `data/reports/<id>__<table>.{json,md}`. Reports are descriptive and git-ignored,
and they must not be published without reviewing them for private values.

## 5. Development subsets

```bash
driftguard data sample wustl_iiot_2021 --n 50000 --seed 20260922 --min-per-class 50
```

The subset is written to `data/subsets/<id>/<subset_id>/` with a manifest (source SHA-256,
parameters, class counts, subset SHA-256). Subsets are for development only. Research
runs use the full tables.
