# Primary-source reference review — 2026-09-25

Scope: bibliographic metadata and the claims used in the working manuscript, not an
independent methodological review or an exhaustive novelty search. Twelve research
references are now cited in the manuscript. Engineering standards are not counted.
No external paper's accuracy is presented as a DriftGuard result.

| Manuscript | Primary evidence inspected | Review boundary |
| --- | --- | --- |
| [1] Ismail et al. | IEEE-deposited [Crossref record](https://api.crossref.org/works/10.1109/ACCESS.2025.3554083); existing `docs/reference-paper-verification.md` | Title, authors, venue, year and pages match; direct IEEE page inaccessible this session; previous full-text audit retained, not repeated |
| [2] Yang & Shami | [Author preprint](https://arxiv.org/abs/2104.10529) | OASW and adaptive LightGBM confirmed in abstract; no comparative performance adopted |
| [3] Ferrag et al. | IEEE-deposited [Crossref record](https://api.crossref.org/works/10.1109/ACCESS.2022.3165809) | Metadata match; IEEE page requested JavaScript verification; dataset license separately checked through official Kaggle workflow |
| [4] Alsaedi et al. | IEEE-deposited [Crossref record](https://api.crossref.org/works/10.1109/ACCESS.2020.3022862) | Metadata match; direct IEEE page requested JavaScript verification; no local dataset validation implied |
| [5] Bifet & Gavaldà | [SIAM publisher abstract](https://epubs.siam.org/doi/10.1137/1.9781611972771.42) | Adaptive windowing and error-rate monitoring described; no claim that our output-mix configuration inherits scientific validation |
| [6] Yang et al. | [Author preprint](https://arxiv.org/abs/2109.05013) | PWPAE name and probability-averaging ensemble confirmed; author record links GLOBECOM DOI, now included in BibTeX |
| [7] Wu et al. | [Elsevier publisher abstract](https://www.sciencedirect.com/science/article/pii/S156849462500242X) and publisher-deposited Crossref metadata | Title, authors, volume and article number match; drift-aware online ensembles are prior art |
| [8] Montiel et al. | [JMLR original](https://www.jmlr.org/papers/v22/20-1380.html) | Streaming software reference; no detector-validation claim |
| [9] Lundberg & Lee | [NeurIPS original](https://papers.neurips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html) | SHAP attribution reference; no causal interpretation |
| [10] Ke et al. | [NeurIPS original](https://papers.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html) | LightGBM algorithm reference; external efficiency results not transferred to this workstation |
| [11] Øren et al. | [Authors' DTU institutional record](https://orbit.dtu.dk/en/publications/concept-drift-under-harsh-constraints-a-review-of-potential-strat/) and IEEE abstract | Metadata and resource-constrained survey scope confirmed; preserve institutional author-name parsing rather than Crossref's inconsistent given/family split |
| [12] Xu et al. | [IEEE publisher abstract](https://ieeexplore.ieee.org/document/10509631/) | Detection, interpretation and adaptation scope confirmed; full comparison pending |

Machine-readable retrieval outcomes, including unsuccessful metadata requests, are in
`docs/evidence/integration/reference-metadata.json`. Absence of accessible full text is
not evidence that a study was reproduced or independently evaluated. The existing NIST
and OASIS BibTeX entries are engineering context, not part of the twelve-paper count.

NIST SP 800-82r3 metadata and its Revision 4 **draft** status were rechecked on the
[official NIST record](https://csrc.nist.gov/pubs/sp/800/82/r3/final).
MQTT 5.0 date/editors were rechecked on the [OASIS standard](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html).
