# DriftGuard-IoT: Drift-Aware, Delayed-Label Intrusion Detection for Resource-Constrained IoT Edge Gateways

Arun Kumar Gharami, Shefatha Rabbany and Ankith Gajam — CNT 6167-001 Internet of Things, Florida Atlantic University

## Abstract

Machine-learning intrusion detection systems for the Internet of Things are usually trained and tested on a single static capture, yet deployed traffic changes over time and true labels reach the gateway only after a delay. This paper presents DriftGuard-IoT, an open-source platform that extends five lightweight baselines (Decision Tree, Random Forest, Bagging, Stacking and LightGBM) with a strict delayed-label evaluation protocol, an ADWIN drift monitor that sees only released labels, and a windowed retraining policy. We evaluate five adaptation policies across three classifiers, two drift types and five seeds in a controlled simulation of 150 streams and 900,000 predictions, and we design the ESP32 sensor node that produces the traffic, including its circuit, operating point and battery life. Concept drift reduced every frozen model from about 0.92 to 0.25 macro-F1. ADWIN detected it in all 15 concept-drift streams with a median delay of 140 flows, 100 of which were the label delay. Retraining on the most recent 1,000 labels after an alarm recovered 86 to 92 % of the gain of periodic retraining while using 3 to 11 % of its retraining time; plain ADWIN with full-history refits recovered only 48 to 66 %. A fixed error threshold matched periodic retraining under severe drift but missed mild covariate drift. Gateway inference energy was negligible, whereas the sensor node's reporting interval set its battery life at 21 to 103 days. All results are reproducible from a single Google Colab notebook.

*Keywords:* Internet of Things, intrusion detection, concept drift, ADWIN, delayed labels, edge computing, LightGBM, ESP32.

## I. Introduction

The Internet of Things has moved a great deal of sensing and control out of the data center and onto small, battery-powered devices. A typical industrial IoT (IIoT) cell now contains dozens of microcontroller nodes that report temperature, vibration or power readings over Wi-Fi to a local gateway, which forwards the data to a cloud service. These nodes are attractive targets. They run lightweight firmware, they are rarely patched, and once compromised they can be enlisted into botnets such as Mirai, which turned hundreds of thousands of cameras and routers into a denial-of-service platform [17]. Because the end devices are too small to defend themselves, the practical place to detect attacks is the edge gateway that already sees all of their traffic.

Machine-learning intrusion detection systems (IDS) are the usual answer, and lightweight tree ensembles have done well on public IoT benchmarks. Ismail, Dandan and Qushou compared Decision Tree, Random Forest, Bagging, Stacking and LightGBM classifiers on TON_IoT, WUSTL-IIoT-2021 and Edge-IIoTset and reported very high accuracy with modest computational cost [1]. Results of this kind, however, are almost always measured on a random train/test split of a single capture. That set-up quietly assumes the future looks like the past. In a deployed network it does not: firmware updates change packet sizes, new devices join, normal workloads shift with production schedules, and attackers change tools. Statistically, the input distribution P(x), the class-conditional relationship P(y|x), or both, change over time. This is concept drift [13], [14], and it is one of the main reasons that IDS models which look excellent in the lab degrade in operation [15], [16].

A second practical problem is that true labels arrive late. A security analyst may confirm that a burst of traffic was a scan hours after it happened, if at all. Many drift-adaptation methods are nonetheless evaluated as if the label for each sample were available immediately after prediction. That assumption inflates their apparent benefit, because the model can react to a change before any real operator would know about it [19]. A third problem is cost. The gateway is itself an embedded computer with a power budget, so a detector that retrains every few seconds may not be affordable.

This paper addresses those three issues together. We built DriftGuard-IoT, an open-source research platform [22] that reuses the five baselines of [1] and adds a delayed-label evaluation protocol, an ADWIN drift monitor [5] that watches only errors whose labels have actually been released, and a windowed retraining policy. We then evaluate the platform in a controlled simulation that injects known covariate and concept drift into a synthetic IoT flow stream, so that the true change point is known and detection delay can be measured exactly. We also ground the work physically: we design the ESP32 sensor node that produces the traffic, calculate its electrical operating point and battery life, and estimate the traffic load and inference energy at the gateway.

The main contributions are:

1. A leakage-safe, delayed-label prequential protocol in which every prediction is made before any label from the same instant is revealed, and refitting uses only labels released strictly earlier.
2. A comparison of four adaptation policies (frozen, periodic, error-threshold and ADWIN) plus a windowed ADWIN variant, across three classifiers, two drift types and five random seeds, with paired block-bootstrap confidence intervals.
3. A finding that ADWIN detects concept drift within about 40 flows of label release but recovers little unless retraining discards stale history; the windowed variant recovers 86 to 92 % of the periodic gain at 3 to 11 % of its retraining time, while a fixed error threshold misses mild drift entirely.
4. A hardware and resource analysis linking the sensor-node circuit, the gateway traffic budget and measured model latency, packaged as a reproducible Google Colab notebook.

The rest of the paper is organized as follows. Section II surveys related work. Section III describes the system model, including the architecture, the sensor-node circuit and the origin of the benchmark datasets. Section IV presents the proposed method. Section V describes the simulation set-up and the Colab notebook. Section VI reports and discusses the results. Section VII covers limitations and threats to validity, and Section VIII summarizes and concludes.

## II. Literature Survey

### A. Lightweight intrusion detection for IoT and IIoT

Public datasets have shaped most IoT IDS research. TON_IoT, collected at UNSW Canberra, combines telemetry, operating-system and network records from a layered IoT/IIoT testbed [4]. Edge-IIoTset, released by Ferrag et al., provides packet-level captures from a seven-layer testbed with fourteen attack types and was designed for both centralized and federated learning [3]. WUSTL-IIoT-2021 was captured on an industrial testbed at Washington University in St. Louis. On these datasets, Ismail et al. [1] showed that classical tree models and LightGBM [10] reach high accuracy while remaining far cheaper than deep networks, which makes them a sensible choice for a gateway. Kitsune [18] took a different route, using an ensemble of small autoencoders that learns online without labels. Both lines of work, however, report performance on a fixed capture. Sommer and Paxson [15] warned more than a decade ago that anomaly detectors built this way often fail in a real network, and Arp et al. [16] later catalogued common pitfalls such as data snooping, spurious correlations and inappropriate random splits.

### B. Concept drift detection and adaptation

The concept-drift literature distinguishes changes in P(x) (covariate or virtual drift) from changes in P(y|x) (real drift), and abrupt from gradual change [13], [14]. Detectors either monitor the input distribution or monitor the model's error rate. ADWIN [5] belongs to the second family. It keeps a variable-length window of a monitored statistic and drops older data whenever two sub-windows differ by more than a Hoeffding-style bound controlled by a confidence parameter δ. It has few parameters and a formal false-positive guarantee, which is why it is widely used and is implemented in the River library [8]. For IoT data streams specifically, Yang and Shami proposed an optimized adaptive and sliding windowing (OASW) framework around LightGBM [2], and Yang, Manias and Shami proposed PWPAE, a performance-weighted ensemble of adaptive learners [6]. Wu et al. [7] study online ensembles with drift-aware components for IoT anomaly detection, and Xu et al. [12] combine drift detection, interpretation and adaptation. A 2025 review by Øren et al. [11] stresses that adaptation has a real computational price on constrained devices and should be measured on the hardware where it will run.

### C. Delayed labels and evaluation protocol

Most of the studies above evaluate prequentially (test, then train on each sample) with labels revealed immediately. Žliobaitė [19] showed that when labels arrive late, some changes cannot be detected at all until enough labelled evidence accumulates, and that the delay should be part of the evaluation. In a security setting, labels come from analysts or incident reports and the delay can be long. Few IoT IDS studies model this explicitly.

### D. Explainability

SHAP [9] attributes a prediction to its input features using Shapley values, and TreeSHAP computes them exactly and quickly for tree ensembles. Monitoring how attributions change between windows is one way to describe what a drift did to the model, though attribution changes are not causal explanations of an attack.

### E. Gap addressed by this work

The combination of a lightweight model with drift adaptation is not new [2], [6], and neither is explainable adaptation [12]. What this paper adds is narrower and, we think, more useful to a practitioner: a strict delayed-label protocol applied consistently to every policy, so that frozen, periodic and drift-triggered models see exactly the same supervision; paired statistical comparisons across seeds; and an explicit accounting of retraining cost next to the hardware it would run on.

## III. System Model

### A. Three-tier architecture

We model a small IIoT cell with three tiers (Fig. 1). In the perception tier, battery-powered ESP32 nodes sample a DHT22 temperature and humidity sensor and their own battery voltage. In the network tier, each node publishes a short MQTT message over Wi-Fi to a broker on the gateway. In the edge-gateway tier, DriftGuard turns each connection into a flow record, classifies it with a tree-based model, and raises an alert for any predicted attack. Ground-truth labels for past flows reach the gateway later, from an analyst or an incident system. Only those released labels feed the ADWIN monitor, and only an ADWIN alarm triggers a refit.


{{figure:fig_architecture|Fig. 1. DriftGuard-IoT architecture. Solid arrows carry data; the dashed arrow is the drift alarm that triggers windowed retraining.}}

### B. Sensor-node circuit and electrical analysis

Fig. 2 shows the sensor node that generates the traffic the IDS protects; component values use typical figures from the ESP32 and MCP1700 datasheets [20], [21]. A single 18650 Li-ion cell (3.0 to 4.2 V, 2600 mAh) feeds an MCP1700 low-dropout regulator that supplies a 3.3 V rail, decoupled by a 10 µF capacitor. A 100 kΩ / 100 kΩ divider lets the ESP32 measure its own battery voltage on ADC pin GPIO34. The DHT22 data line uses a 10 kΩ pull-up to 3.3 V and connects to GPIO4. A red status LED on GPIO2 signals each transmission.


{{figure:fig_circuit|Fig. 2. ESP32 sensor-node schematic. The blue trace is the battery-sense divider; the red trace is the DHT22 data line.}}

The component values follow from Ohm's law and the divider rule. The LED current-limiting resistor for a 2.0 V forward drop and a 10 mA target is:

```latex
R_{LED} = \frac{V_{3V3} - V_F}{I_{LED}} = \frac{3.3 - 2.0}{0.010} = 130\ \Omega
```

We use the next standard E12 value, 150 Ω, which gives 8.7 mA and dissipates 11.3 mW in the resistor. The divider output at full charge is:

```latex
V_{ADC} = V_{BAT}\,\frac{R_2}{R_1 + R_2} = 4.2 \times \frac{100\,k}{200\,k} = 2.1\ \text{V}
```

That stays below the roughly 2.45 V usable ADC range at 11 dB attenuation, falls to 1.5 V at the 3.0 V cut-off, and costs a constant 21 µA. One 12-bit ADC step corresponds to about 1.2 mV of battery voltage. The regulator needs at least 3.3 + 0.178 = 3.48 V at its input, so the node should stop transmitting once the cell drops below about 3.5 V.

Battery life depends on duty cycle. If the node wakes every T = 60 s, spends 2 s sampling and publishing at about 121.5 mA (Wi-Fi transmit plus sensor), and sleeps at about 32.6 µA otherwise (deep sleep, divider and regulator quiescent current), the average current is:

```latex
\begin{aligned} \bar{I} &= \frac{I_{on}\,t_{on} + I_{sleep}\,(T - t_{on})}{T} \\ &= \frac{121.5\,\text{mA} \times 2 + 0.0326\,\text{mA} \times 58}{60} = 4.08\ \text{mA} \end{aligned}
```

With 80 % usable capacity, life = 0.8 × 2600 mAh / 4.08 mA ≈ 510 h, or about 21 days. Reporting every 5 minutes instead lowers the average current to 0.84 mA and stretches life to about 103 days. Each report costs about 0.9 J. Table I summarizes the operating point.

{{widget:battery}}

*Table I. Calculated electrical operating point of the sensor node.*

| Quantity | Value |
| --- | --- |
| LED resistor (ideal / chosen) | 130 Ω / 150 Ω |
| LED current | 8.7 mA |
| ADC voltage at 4.2 V / 3.0 V battery | 2.10 V / 1.50 V |
| Divider standing current | 21 µA |
| Minimum regulator input | 3.48 V |
| Average current, 60 s reporting | 4.08 mA |
| Battery life, 60 s reporting | 21.2 days |
| Battery life, 5 min reporting | 102.9 days |
| Energy per report | 0.90 J |
| Bytes per report (64 B payload + headers) | 120 B |
| Gateway load, 50 nodes at 60 s | 0.83 reports/s, 800 bit/s |

The last two rows matter for the IDS. Fifty nodes reporting once a minute produce less than one message per second at the gateway, so even the slowest model we measure in Section VI has a large margin. The real constraint is the gateway's energy and the cost of retraining, not per-flow latency. A Raspberry Pi 4 class gateway drawing about 3.4 W uses roughly 82 Wh per day before any model work.

### C. Origin of the benchmark datasets

The three public datasets that motivate this work were recorded on different testbeds on different continents (Fig. 3). TON_IoT comes from UNSW Canberra, about 15,260 km from our site in Boca Raton; WUSTL-IIoT-2021 from St. Louis, about 1,665 km away; and Edge-IIoTset from authors at the University of Guelma, Algeria (about 8,100 km) and De Montfort University, UK (about 6,980 km). Distances are great-circle values computed with the haversine formula in the Colab notebook. The geography is a reminder that a model trained on one lab's devices, firmware and traffic mix is being asked to work on someone else's. Moving between them is a domain shift, which is the large-scale version of the drift studied here.


{{figure:fig_map|Fig. 3. Origin of the three IoT/IIoT benchmark datasets and the study site at Florida Atlantic University. Arrows indicate the direction of a cross-domain transfer to a new deployment.}}

## IV. Proposed Method

### A. Problem statement

Let a stream of flows (x_t, y_t) arrive at the gateway, where x_t is a feature vector and y_t ∈ {normal, dos, scan, injection} is its class. The gateway must output a prediction ŷ_t when the flow arrives. The true label y_t becomes available only at a later release time r_t = t + Δ. At some unknown time τ the data-generating process changes. The goal is to keep the macro-averaged F1 score high after τ while limiting the number and cost of retraining operations, using only labels whose release time has already passed.

### B. Delayed-label prequential protocol

DriftGuard groups flows that share a timestamp into a tick. At each tick it first predicts every flow in that tick with the current model. Only then does it consider supervision, and only labels whose event time and release time are both strictly earlier than the current tick are eligible. This rule is enforced in code by the delayed_prequential function: a label is usable at tick t only if r_i < t. Before the stream begins, the function also checks that no feature-identical row appears in both the initial training set and the stream, so duplicates cannot leak a label across the boundary. Every refit clones the whole preprocessing-plus-model pipeline from scratch, so no fitted state from a previous model carries over.

### C. Adaptation policies

All policies start from the same model, fitted on the same initial data, and receive the same released labels. They differ only in when and on what they refit.

1. **Frozen.** Never refits. This is the usual lab set-up and the lower bound.
2. **Periodic.** Refits on all released data each time P = 500 new labels have been released, whether or not anything changed. This is the simple operational baseline.
3. **Error-threshold.** Refits when the error rate over the latest 200 released labels exceeds 30 %. This is a naive drift trigger with a hand-set threshold.
4. **ADWIN.** Feeds each released prediction error (0 or 1) once into an ADWIN detector [5] with δ = 0.002, and refits on all released data when the detector signals a change.
5. **ADWIN-window (proposed).** Same trigger as ADWIN, but the refit uses only the most recent W = 1000 released rows.

The reason for policy 5 is simple. After a concept change, old labels describe a relationship between features and classes that no longer holds. If a refit uses every label ever seen, the old concept still dominates the training set for a long time, and the new model can be little better than the frozen one. Limiting the refit to a recent window lets the model forget. The window must be large enough to contain every class, including the 5 % minority class; 1000 rows gives about 50 injection examples.

### D. ADWIN in brief

ADWIN maintains a window W of recent error values. For every split of W into an older part W0 and a newer part W1, with sizes n0 and n1 and means μ0 and μ1, it declares a change and drops W0 when:

```latex
|\hat{\mu}_0 - \hat{\mu}_1| > \epsilon_{cut}, \qquad \epsilon_{cut} = \sqrt{\frac{1}{2m}\ln\frac{4|W|}{\delta}}, \qquad m = \frac{1}{1/n_0 + 1/n_1}
```

A smaller δ means fewer false alarms but slower detection. Because DriftGuard feeds ADWIN only released errors, its detection delay is at least the label delay Δ.

### E. Statistical comparison

For each adaptive policy we compare its post-drift predictions with those of the frozen model on the same flows. We use a paired circular moving-block bootstrap of the macro-F1 difference with a block length of 100 flows and 500 replicates, which preserves short-range time dependence in the stream. We then repeat the whole experiment over five random seeds and report the mean and standard deviation across seeds, since the bootstrap interval alone does not capture training variability.

## V. Simulation Set-up

### A. Why a controlled simulation

To measure detection delay and false alarms honestly, the evaluator must know exactly when the drift happened, and that knowledge must not come from the detector itself. Public IoT captures do not come with independently verified change points, and their licences and acquisition steps were still being cleared for our repository at the time of writing. We therefore evaluate DriftGuard on streams from the repository's own synthetic flow generator, where the change point is set by design. The results describe how the policies behave under known drift; they are not claims about accuracy on TON_IoT, WUSTL-IIoT-2021 or Edge-IIoTset.

### B. Data generator

Each stream contains six log-normally distributed numeric flow features (duration, source and destination bytes, source and destination packets, mean inter-arrival time) and a categorical protocol (TCP, UDP or ICMP). Classes follow a realistic imbalance: 70 % normal, 15 % DoS, 10 % scan and 5 % injection. Each class has its own feature locations, so the classes overlap but are learnable. Numeric features are log-transformed and the protocol is one-hot encoded, giving nine model inputs. Every run uses 1,000 initial labelled flows, a 200-flow gap, and a 6,000-flow evaluation stream. The drift begins at the stream's midpoint (flow 3,000). We study two scenarios:

- **Covariate drift.** From the onset, source bytes and mean inter-arrival time are multiplied by 3, as if a firmware update changed message sizes and timing. Labels are generated exactly as before, so P(x) changes but the class rule does not.
- **Concept drift.** From the onset, flows come from a generator with different class-conditional distributions, while class proportions stay the same. P(y|x) changes, as when attackers switch tools and normal traffic also changes.

### C. Timing and models

Flows arrive in ticks of 20, and each label is released Δ = 5 ticks (100 flows) after its flow. We test Decision Tree, Random Forest and LightGBM with library defaults, as in [1], each built through DriftGuard's model factory. Every combination of 2 scenarios × 3 models × 5 policies is run with five seeds (11, 22, 33, 44, 55), giving 150 streams and 900,000 predictions. Drift alarms are scored against the known onset with a 60-tick (1,200-flow) detection horizon; an alarm outside that horizon counts as false.

### D. Resource and robustness measurements

For all five baselines of [1] (adding Bagging and DT/RF-to-MLP Stacking), we record fit time, pickled model size, warm single-flow and 256-flow batch latency (p50 and p95 over 100 to 200 repeats after 3 warm-up calls), and throughput. As a robustness check we add uniform noise of up to ±5 % of each feature's training interquartile range to 2,000 stream flows and count how many predictions change. For explainability we compute TreeSHAP values for the DoS class of a LightGBM model before and after each drift and measure the Jaccard overlap of the top-3 features. All timing used one CPU thread on a 2-vCPU Intel Xeon (2.1 GHz) cloud instance with 8 GB of RAM, Python 3.11, scikit-learn and LightGBM 4.

### E. Reproducibility and the Colab notebook

Every number in Section VI is produced by one Google Colab notebook, DriftGuard_paper_calculations.ipynb. It installs DriftGuard-IoT from GitHub, runs the stream experiments, the resource benchmark and the SHAP analysis, draws the circuit with schemdraw, computes the electrical values in Table I, draws the map with GeoPandas, and writes all tables and figures. The full run takes roughly 25 to 35 minutes on a free Colab CPU runtime; a QUICK flag runs one seed in a few minutes.

## VI. Results and Discussion

### A. Effect of drift on a frozen model

Before the change point, the frozen models reached a mean macro-F1 of 0.878 (Decision Tree), 0.934 (Random Forest) and 0.934 (LightGBM). Covariate drift cost them between 5 and 11 points: post-drift macro-F1 fell to 0.771, 0.880 and 0.878. Concept drift was far more damaging. All three frozen models collapsed to about 0.25 macro-F1, barely above guessing across four classes (Fig. 4). The ensembles were more robust to rescaled features than the single tree, but no model choice protects against a change in the class rule. This is the core argument for adaptation: a model that scored 0.93 in the lab can be close to useless a few thousand flows after an abrupt change.


{{figure:fig_f1_post|Fig. 4. Post-drift macro-F1 (mean ± SD over five seeds) for each adaptation policy, model and drift type.}}

### B. Comparison of adaptation policies

Table II averages the three models. Under concept drift, every adaptive policy beat the frozen model, and the paired block-bootstrap 95 % interval of the gain excluded zero in all 60 policy-by-model-by-seed comparisons. Periodic retraining gave the highest mean post-drift macro-F1 (0.638), with the error-threshold trigger close behind (0.627). Plain ADWIN reached only 0.474. The windowed ADWIN variant reached 0.591, a gain of 0.341 over frozen against 0.388 for periodic.

*Table II. Post-drift results averaged over three models and five seeds (15 streams per row). Gain is macro-F1 minus the frozen model on the same flows.*

| Drift | Policy | Post-drift macro-F1 | Gain vs. frozen | Refits per stream | Retraining time per stream (s) |
| --- | --- | --- | --- | --- | --- |
| Concept | Frozen | 0.250 ± 0.096 | — | 0 | 0 |
| Concept | Periodic | 0.638 ± 0.057 | +0.388 | 11.0 | 3.14 |
| Concept | Error-threshold | 0.627 ± 0.078 | +0.377 | 2.7 | 0.69 |
| Concept | ADWIN | 0.474 ± 0.156 | +0.224 | 1.3 | 0.34 |
| Concept | ADWIN-window | 0.591 ± 0.154 | +0.341 | 1.6 | 0.23 |
| Covariate | Frozen | 0.843 ± 0.082 | — | 0 | 0 |
| Covariate | Periodic | 0.892 ± 0.067 | +0.049 | 11.0 | 2.85 |
| Covariate | Error-threshold | 0.844 ± 0.080 | +0.001 | 0.07 | 0.003 |
| Covariate | ADWIN | 0.872 ± 0.061 | +0.029 | 0.5 | 0.12 |
| Covariate | ADWIN-window | 0.876 ± 0.071 | +0.033 | 0.5 | 0.05 |

The gap between plain ADWIN and ADWIN-window confirms the reasoning in Section IV-C. Both detect the change at the same moment and refit about as often, yet the plain version retrains on the full history, which is still mostly pre-drift data. The rolling-accuracy traces in Fig. 5 show this clearly for one seed: after the alarm, plain ADWIN climbs only a little above the frozen curve, while the windowed variant lifts accuracy by about 10 more points. The periodic model, by contrast, keeps refitting every 500 labels, so the share of new-concept data in its training set grows steadily and it eventually overtakes both.


{{figure:fig_traces|Fig. 5. Rolling accuracy over 300 flows for LightGBM (seed 11). The dashed line marks the drift onset.}}

Under covariate drift the picture changes. The losses were small, and the error-threshold policy almost never fired: the error rate rarely crossed 30 %, so it refitted in only 1 of 15 streams and recovered essentially nothing. ADWIN, which tests for any statistically significant rise rather than a fixed level, detected the change in 7 of 15 streams. Periodic retraining again had the best average, and its gain was significant in 14 of 15 streams. The ADWIN variants were significant in 7 of 15, exactly the streams where ADWIN fired. The variability across seeds is large (Fig. 4), and in several seeds the frozen model lost so little that there was little to recover.

### C. Detection delay and false alarms

Because the drift time is known, ADWIN alarms can be scored exactly (Table III). Under concept drift, ADWIN detected the change in all 15 streams with a median delay of 7 ticks (140 flows). Five of those ticks are the label delay itself, so the detector needed only about 2 ticks (40 flows) of released evidence. Under covariate drift, detection was slower and less reliable, because the error rate rose only slightly. Across all 30 ADWIN streams we recorded 2 false alarms.

*Table III. ADWIN detection performance (δ = 0.002, label delay 5 ticks, horizon 60 ticks).*

| Drift | Streams detected | Mean delay (ticks / flows) | Median delay (ticks) | False alarms (total) |
| --- | --- | --- | --- | --- |
| Concept | 15 of 15 | 7.3 / 146 | 7 | 1 |
| Covariate | 7 of 15 | 25.3 / 506 | 22 | 1 |

### D. Cost versus benefit

Fig. 6 plots each policy's gain against its total retraining time. Measured against periodic retraining, ADWIN-window recovered 86 to 92 % of the periodic gain under concept drift while using only 3 to 11 % of its retraining time, and 58 to 73 % of the gain under covariate drift at 1 to 2 % of the time. The error-threshold trigger is a strong option when the drift is severe (96 to 100 % of the periodic gain at 19 to 41 % of the time) but a poor one when it is mild. Plain ADWIN was dominated by its windowed variant in every cell.


{{figure:fig_cost_benefit|Fig. 6. Post-drift macro-F1 gain over frozen against total retraining time per stream (log scale). Filled markers: concept drift; open markers: covariate drift.}}

The absolute costs at this scale are small. Periodic LightGBM retraining used 2.9 s per 6,000-flow stream on our CPU. Two factors make the ratio matter more than the absolute value. First, periodic refits on the full history, so their cost grows without bound as the deployment runs, whereas the windowed refit is capped at 1,000 rows. Second, a Raspberry Pi class gateway is several times slower than the cloud CPU we used, and a real gateway may protect many more nodes.

### E. Inference cost, size and robustness

Table IV lists the five baselines of [1] on the same nine features. The Decision Tree is fastest and smallest by far but also least accurate. LightGBM matched Random Forest's accuracy with about one seventh of its single-flow latency. Stacking was the slowest to train and to predict and offered no accuracy advantage.

*Table IV. Resource measurements, one CPU thread, trained on 1,000 flows (seed 11). Macro-F1 is on the full undrifted stream.*

| Model | Fit time (s) | Model size (KB) | Single-flow latency p50 / p95 (ms) | Throughput, 256-flow batch (flows/s) | Macro-F1 | Predictions changed by ±5 % IQR noise |
| --- | --- | --- | --- | --- | --- | --- |
| Decision Tree | 0.005 | 15 | 0.10 / 0.15 | 2,507,000 | 0.783 | 1.5 % |
| Bagging | 0.069 | 106 | 1.32 / 2.06 | 134,000 | 0.837 | 1.4 % |
| LightGBM | 0.169 | 1,339 | 0.70 / 0.97 | 29,000 | 0.872 | 1.2 % |
| Random Forest | 0.220 | 1,429 | 4.74 / 8.10 | 38,000 | 0.873 | 0.4 % |
| Stacking (DT+RF→MLP) | 1.835 | 1,499 | 5.77 / 9.12 | 34,000 | 0.868 | 0.8 % |

These latencies connect back to the hardware in Section III. At the 0.83 flows per second produced by 50 nodes, even Stacking uses well under 1 % of one core. Multiplying single-flow latency by an assumed 3.4 W gateway draw gives about 2.4 mJ per LightGBM prediction, or roughly 0.05 Wh per day for 72,000 flows, against 82 Wh for the gateway itself. In other words, inference energy is negligible at the gateway; the energy that matters is on the battery-powered node, where each report costs about 0.9 J. Small, bounded measurement noise of ±5 % of the training interquartile range changed between 0.4 % and 1.5 % of predictions and moved accuracy by at most 0.35 points, so the models are not fragile to sensor-level jitter.

### F. Feature attributions

For the DoS class, the top three LightGBM features before the drift were source packets, destination bytes and TCP protocol. After covariate drift, the scaled mean inter-arrival time rose into the top three (mean |SHAP| from 0.62 to 0.89) and replaced TCP, giving a top-3 Jaccard overlap of 0.5. After concept drift the overlap was also 0.5, but the shift was broader: mean attribution for duration more than doubled, from 0.35 to 0.80. Monitoring attributions in this way gives an operator a hint about which features moved, which is useful when deciding whether an alarm reflects a benign firmware change or a new attack. It does not, on its own, say why the change happened.

## VII. Limitations and Threats to Validity

The largest limitation is the data. The streams are synthetic, with clean log-normal features, a single abrupt change and fixed class proportions. Real IoT traffic has bursty arrivals, correlated flows, gradual and recurring drift, and attack families that appear for the first time after deployment. Our results show how the policies behave when the drift is known; they do not show how much a real gateway would gain. The next step is to run the same notebook on Edge-IIoTset and TON_IoT once their acquisition and licence checks are complete in the repository, using the reviewed feature contracts the platform already requires.

Several settings were chosen by hand rather than tuned: δ = 0.002, the 200-label error window and 30 % threshold, the refit period of 500 labels and the window of 1,000 rows. A different window could trade recovery speed against minority-class coverage. The label delay is fixed at 100 flows; in practice it varies and some labels never arrive. We report resource figures from a cloud CPU, not from a Raspberry Pi, so absolute latencies on the gateway will be higher, though the ranking of models should hold. The electrical figures in Section III are design calculations from typical datasheet values; they have not been measured on a built board. Finally, five seeds give a reasonable picture of variability but not tight intervals for small effects, and SHAP rankings describe the model, not the cause of an attack.

## VIII. Summary and Conclusions

This paper studied a practical question for IoT security: what should an edge-gateway intrusion detector do when the traffic it was trained on stops resembling the traffic it sees, and when it learns the truth about past flows only after a delay? We built DriftGuard-IoT on the five lightweight baselines of Ismail et al. [1], added a delayed-label prequential protocol, an ADWIN monitor fed only by released labels, and a windowed retraining policy, and evaluated it in a controlled simulation of 150 streams with known covariate and concept drift. We also designed the ESP32 sensor node behind the traffic and worked out its electrical operating point and power budget.

Four conclusions follow. First, drift is not a corner case. A concept change dropped every frozen model from about 0.92 to about 0.25 macro-F1, regardless of model family. Second, how a model retrains matters as much as when. ADWIN found concept drift in every stream within roughly 40 flows of label release, but retraining on the full history wasted much of that early warning; restricting the refit to the latest 1,000 labels recovered 86 to 92 % of the gain of periodic retraining at 3 to 11 % of its cost. Third, no single trigger was best everywhere. A fixed error threshold matched periodic retraining under severe drift but ignored mild drift, while ADWIN caught about half of the mild cases. Periodic retraining remained the most accurate option when retraining is cheap. Fourth, at the scale of a small IIoT cell, inference energy at the gateway is negligible; the binding energy constraint is on the battery-powered node, where a one-minute reporting interval gives about 21 days of life and a five-minute interval about 103 days.

For practitioners, the result suggests a simple rule: pair a statistical drift detector with a bounded, recent retraining window, and keep a slow periodic refit as a safety net for drift too gradual to trigger an alarm. For researchers, it shows why label delay and retraining cost should be reported alongside accuracy. Future work will run the same Colab pipeline on Edge-IIoTset and TON_IoT once their admission checks are complete, tune the window size and δ on source data only, test gradual and recurring drift, and measure latency and power on a physical Raspberry Pi gateway and ESP32 node.

## References

[1] S. Ismail, S. Dandan, and A. Qushou, "Intrusion detection in IoT and IIoT: Comparing lightweight machine learning techniques using TON_IoT, WUSTL-IIOT-2021, and EdgeIIoTset datasets," *IEEE Access*, vol. 13, pp. 73468–73485, 2025, doi: 10.1109/ACCESS.2025.3554083.

[2] L. Yang and A. Shami, "A lightweight concept drift detection and adaptation framework for IoT data streams," *IEEE Internet of Things Magazine*, vol. 4, no. 2, pp. 96–101, 2021, doi: 10.1109/IOTM.0001.2100012.

[3] M. A. Ferrag, O. Friha, D. Hamouda, L. Maglaras, and H. Janicke, "Edge-IIoTset: A new comprehensive realistic cyber security dataset of IoT and IIoT applications for centralized and federated learning," *IEEE Access*, vol. 10, pp. 40281–40306, 2022, doi: 10.1109/ACCESS.2022.3165809.

[4] A. Alsaedi, N. Moustafa, Z. Tari, A. Mahmood, and A. Anwar, "TON_IoT telemetry dataset: A new generation dataset of IoT and IIoT for data-driven intrusion detection systems," *IEEE Access*, vol. 8, pp. 165130–165150, 2020, doi: 10.1109/ACCESS.2020.3022862.

[5] A. Bifet and R. Gavaldà, "Learning from time-changing data with adaptive windowing," in *Proc. SIAM Int. Conf. Data Mining*, 2007, pp. 443–448, doi: 10.1137/1.9781611972771.42.

[6] L. Yang, D. M. Manias, and A. Shami, "PWPAE: An ensemble framework for concept drift adaptation in IoT data streams," in *Proc. IEEE GLOBECOM*, 2021; preprint arXiv:2109.05013.

[7] Y. Wu, L. Liu, Y. Yu, G. Chen, and J. Hu, "Online ensemble learning-based anomaly detection for IoT systems," *Applied Soft Computing*, vol. 173, art. 112931, 2025, doi: 10.1016/j.asoc.2025.112931.

[8] J. Montiel et al., "River: Machine learning for streaming data in Python," *Journal of Machine Learning Research*, vol. 22, no. 110, pp. 1–8, 2021.

[9] S. M. Lundberg and S.-I. Lee, "A unified approach to interpreting model predictions," in *Advances in Neural Information Processing Systems*, vol. 30, 2017.

[10] G. Ke et al., "LightGBM: A highly efficient gradient boosting decision tree," in *Advances in Neural Information Processing Systems*, vol. 30, 2017.

[11] A. E. Øren, N. K. Peuker, A.-M. A. Adeniran-Lowe, S. Ruepp, and M. N. Petersen, "Concept drift under harsh constraints: A review of potential strategies for IoT systems," *IEEE Access*, vol. 13, pp. 182220–182237, 2025, doi: 10.1109/ACCESS.2025.3622973.

[12] L. Xu, Z. Han, D. Zhao, X. Li, F. Yu, and C. Chen, "Addressing concept drift in IoT anomaly detection: Drift detection, interpretation, and adaptation," *IEEE Transactions on Sustainable Computing*, vol. 9, no. 6, pp. 913–924, 2024, doi: 10.1109/TSUSC.2024.3386667.

[13] J. Gama, I. Žliobaitė, A. Bifet, M. Pechenizkiy, and A. Bouchachia, "A survey on concept drift adaptation," *ACM Computing Surveys*, vol. 46, no. 4, art. 44, 2014, doi: 10.1145/2523813.

[14] J. Lu, A. Liu, F. Dong, F. Gu, J. Gama, and G. Zhang, "Learning under concept drift: A review," *IEEE Transactions on Knowledge and Data Engineering*, vol. 31, no. 12, pp. 2346–2363, 2019, doi: 10.1109/TKDE.2018.2876857.

[15] R. Sommer and V. Paxson, "Outside the closed world: On using machine learning for network intrusion detection," in *Proc. IEEE Symposium on Security and Privacy*, 2010, pp. 305–316, doi: 10.1109/SP.2010.25.

[16] D. Arp et al., "Dos and don'ts of machine learning in computer security," in *Proc. 31st USENIX Security Symposium*, 2022, pp. 3971–3988.

[17] C. Kolias, G. Kambourakis, A. Stavrou, and J. Voas, "DDoS in the IoT: Mirai and other botnets," *Computer*, vol. 50, no. 7, pp. 80–84, 2017, doi: 10.1109/MC.2017.201.

[18] Y. Mirsky, T. Doitshman, Y. Elovici, and A. Shabtai, "Kitsune: An ensemble of autoencoders for online network intrusion detection," in *Proc. Network and Distributed System Security Symposium (NDSS)*, 2018, doi: 10.14722/ndss.2018.23204.

[19] I. Žliobaitė, "Change with delayed labeling: When is it detectable?" in *Proc. IEEE Int. Conf. Data Mining Workshops*, 2010, pp. 843–850, doi: 10.1109/ICDMW.2010.49.

[20] Espressif Systems, *ESP32 Series Datasheet*, ver. 4.x, Shanghai, China. [Online]. Available: https://www.espressif.com/en/support/documents/technical-documents

[21] Microchip Technology, *MCP1700 Low Quiescent Current LDO Regulator Datasheet*, DS20001826. [Online]. Available: https://www.microchip.com

[22] A. K. Gharami, S. Rabbany, and A. Gajam, *DriftGuard-IoT* (source code and Colab notebooks), GitHub, 2026. [Online]. Available: https://github.com/Arungharami/DriftGuard-IoT
