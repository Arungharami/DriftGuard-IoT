export type NavItem = { href: string; label: string };

export const NAV: NavItem[] = [
  { href: "/", label: "Home" },
  { href: "/research", label: "Research" },
  { href: "/architecture", label: "Architecture" },
  { href: "/datasets", label: "Datasets" },
  { href: "/experiments", label: "Experiments" },
  { href: "/drift-lab", label: "Drift Lab" },
  { href: "/model-explorer", label: "Model Explorer" },
  { href: "/explainability", label: "Explainability" },
  { href: "/reproducibility", label: "Reproducibility" },
  { href: "/publications", label: "Publications" },
  { href: "/team", label: "Team" },
];

/** Names only; contact details are deliberately not published on the portal. */
export const TEAM: { name: string; affiliation: string }[] = [
  { name: "Arun Kumar Gharami", affiliation: "Florida Atlantic University" },
  { name: "Shefatha Rabbany", affiliation: "Florida Atlantic University" },
  { name: "Ankith Gajam", affiliation: "Florida Atlantic University" },
];

export const REPO_URL ="https://github.com/Arungharami/DriftGuard-IoT";

export const REFERENCE_PAPER = {
  citation:
    "Ismail, Dandan and Qushou (2025). Intrusion Detection in IoT and IIoT: Comparing Lightweight Machine Learning Techniques Using TON_IoT, WUSTL-IIOT-2021, and EdgeIIoTset Datasets. IEEE Access 13 (2025): 73468–73485.",
  doi: "10.1109/ACCESS.2025.3554083",
};

export type MilestoneStatus = "in_progress" | "planned" | "complete";

export const MILESTONES: { id: string; title: string; status: MilestoneStatus }[] = [
  { id: "M0", title: "Repository, architecture, scientific protocol, CI", status: "in_progress" },
  { id: "M1", title: "Dataset registry, synthetic fixtures, Kaggle integration, provenance", status: "in_progress" },
  { id: "M2", title: "Leakage-safe preprocessing and five configurable baselines", status: "in_progress" },
  { id: "M3", title: "Reproducible single-dataset benchmark and reporting", status: "planned" },
  { id: "M4", title: "Cross-dataset schemas, chronological evaluation, domain shift", status: "planned" },
  { id: "M5", title: "Drift detector and adaptation-policy evaluation", status: "planned" },
  { id: "M6", title: "Explainability and resource benchmarking", status: "planned" },
  { id: "M7", title: "Colab workflows and verified Hugging Face artifacts", status: "planned" },
  { id: "M8", title: "Research portal and inference API integration", status: "planned" },
  { id: "M9", title: "Full experiment campaign, ablations, statistics", status: "planned" },
  { id: "M10", title: "Manuscript and public release readiness", status: "planned" },
];

export const RESEARCH_QUESTIONS: { id: string; text: string }[] = [
  { id: "RQ1", text: "How do leakage-safe baselines perform across the three IoT/IIoT datasets?" },
  { id: "RQ2", text: "How do their minority-class detection rates change under domain shift and chronological evaluation?" },
  { id: "RQ3", text: "Can drift monitoring identify significant changes in input distributions without excessive false alarms?" },
  { id: "RQ4", text: "Can a drift-triggered adaptation policy improve robustness compared with static models and simple periodic retraining?" },
  { id: "RQ5", text: "What are the measured accuracy, latency, memory and throughput trade-offs?" },
  { id: "RQ6", text: "How stable and interpretable are selected features across environments?" },
];
