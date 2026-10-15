export const PRESENTATION_FOLDER = "https://drive.google.com/drive/folders/1JR32TfmDbGKQKCkAjPRUkmcnzlmn07FK";

export const JOURNEY = [
  { date: "September 18, 2026", title: "A paper to build on", status: "Course foundation", detail: "Our team selected the IoT and IIoT intrusion-detection study by Ismail, Dandan and Qushou. Professor Ilyas approved the paper for Presentation 1 and encouraged us to move forward.", source: "", sourceLabel: "Course approval email supplied by the team" },
  { date: "September 23, 2026", title: "A reproducible research foundation", status: "Implementation merged", detail: "We established the package structure, scientific protocol, dataset registry and provenance records. Five baseline configurations and train-only preprocessing provide a foundation for controlled evaluation.", source: "https://github.com/Arungharami/DriftGuard-IoT/pull/3", sourceLabel: "M2 implementation, PR #3" },
  { date: "September 23, 2026", title: "Making the data barrier explicit", status: "Research blocked", detail: "The first real-data benchmark remained blocked because the required dataset file was absent. Admission checks and split records help prevent a development run from being presented as a research result.", source: "https://github.com/Arungharami/DriftGuard-IoT/pull/13", sourceLabel: "First benchmark preparation, PR #13" },
  { date: "September 24–25, 2026", title: "Connecting the MQTT workflow", status: "Synthetic demonstration", detail: "MQTT replay, an authenticated broker, a fail-closed worker and event logging were integrated into the portal. This demonstrates software behavior using synthetic inputs. Real device traffic and attack-detection effectiveness still require measurement.", source: "https://github.com/Arungharami/DriftGuard-IoT/pull/17", sourceLabel: "MQTT observatory integration, PR #17" },
  { date: "October 5, 2026", title: "Repairing streaming limits", status: "Engineering repair merged", detail: "A correctness review identified unsafe queue and rate-limit inputs. Validation now rejects invalid limits, and bounded-queue behavior has regression coverage. This is an engineering repair rather than evidence of improved detection accuracy.", source: "https://github.com/Arungharami/DriftGuard-IoT/pull/28", sourceLabel: "Streaming correctness repair, PR #28" },
  { date: "October 7, 2026", title: "Preparing our first presentation", status: "Presentation artifact", detail: "Our 25-slide deck reviews the reference paper and separates its findings from the DriftGuard-IoT implementation update and proposed research. The repository also gained clearer contribution guidance.", source: PRESENTATION_FOLDER, sourceLabel: "Open team presentation folder" },
  { date: "Next research stage", title: "Evidence before conclusions", status: "Proposed experiments", detail: "Acquire and fingerprint authorized benchmark data, validate timestamps, and compare static, periodic and drift-triggered updates under the same label delays. Measure macro-F1, attack recall, false alarms, latency, memory and retraining cost before making performance claims.", source: "https://github.com/Arungharami/DriftGuard-IoT/blob/main/docs/research-2026/complete-study-plan.md", sourceLabel: "Research study plan" },
];

/** Text review of the existing 25-slide deck, not a replacement or a rendered PPT viewer. */
export const SLIDE_REVIEW = [
  ["Lightweight intrusion detection", "Title, reference paper, course and Grad1 team."],
  ["Presentation roadmap", "Paper context, methodology, results, critical review and group perspective."],
  ["Paper summary", "The reference study compares five models across three datasets. Its reported findings belong to the original authors."],
  ["IoT and IIoT security challenges", "Connected assets expose varied attack patterns under constrained memory and computing budgets."],
  ["Research gap and contribution", "The paper considers multiple datasets, model resource costs, transfer and a traffic pipeline."],
  ["Research goal and questions", "Detection, class imbalance, cross-environment transfer and live monitoring frame the paper review."],
  ["IDS architecture", "A gateway or monitoring point observes traffic between devices, middleware and cloud services."],
  ["Three benchmark datasets", "TON_IoT, WUSTL-IIOT-2021 and EdgeIIoTset represent different environments and class distributions."],
  ["Preprocessing methodology", "The deck raises a question about resampling order. Our reproduction fits preprocessing only on training data."],
  ["Five baseline models", "Decision Tree, Random Forest, Bagging, Stacking and LightGBM have different resource requirements."],
  ["TON_IoT results in the reference study", "Review the authors’ reported scores alongside attack-class performance. These are not our measurements."],
  ["WUSTL-IIOT-2021 results in the reference study", "Class imbalance makes per-class recall and false alarms important."],
  ["EdgeIIoTset results in the reference study", "Attack-specific weaknesses require closer examination than an aggregate score provides."],
  ["Model size and training time", "The deck compares reported resource costs. Target-device inference, memory and energy require separate validation."],
  ["Cross-dataset and live traffic tests", "The original paper’s transfer and Tshark/Argus experiment are separate from our MQTT demonstration."],
  ["Critical review: strengths", "Multiple datasets and resource-aware comparisons broaden the evidence considered."],
  ["Critical review: limitations", "Preprocessing ambiguity, rare-class metrics, hardware validation and reproduction details motivate further work."],
  ["DriftGuard-IoT implementation", "The deck credits Arun’s implementation update: research foundation, streaming engineering and the current evidence boundary."],
  ["Proposed next research version", "Leakage-safe experiments, drift and adaptation comparisons, and measured IoT deployment costs remain proposed work."],
  ["Other observations", "A model’s usefulness depends on its traffic environment, attack classes and target hardware."],
  ["Our group’s perspective", "The group discusses transfer, resource constraints, rare attacks and reproducibility."],
  ["Potential improvements", "Train-only preprocessing, imbalance-aware metrics, broader transfer tests and documented hardware evaluation could strengthen evidence."],
  ["Proposed follow-up study", "Dataset auditing, controlled training and deployment measurements form a prospective study."],
  ["Conclusion", "A useful IDS needs reliable evaluation and a documented deployment budget."],
  ["References and team credits", "The closing slide cites the original paper and credits all three members. Speaker assignments differ between deck sections and need team reconciliation."],
] as const;
