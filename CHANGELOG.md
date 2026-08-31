# Changelog

## 2026-09-01 - Tutor-feedback v2

### Added

- Eight-category taxonomy configuration in `config/taxonomy_v2.json`.
- Separate Simulation and Case-Based Learning categories.
- Project- and Problem-Based, Community, Entrepreneurial, Technology-Mediated, and Hybrid rule sets.
- Category overlap notes and review guidance.
- Positive, review, and unit-category score summaries.
- Review queue and category summary CSV exports.
- Evidence-count, score, and source-section visualisations.
- Two PDF deliverables and a SHA-256 release manifest.
- Offline unit tests and an INFS6600 tutor-feedback regression test.

### Changed

- Authentic practice weight: 3.5 to 4.0.
- Theory-practice integration weight: 2.5 to 2.0.
- Practical teamwork weight retained at 2.0 per tutor comment.
- Career readiness weight: 1.5 to provisional 2.0.
- Administrative `Case studies` label: strong 4.0 evidence to review-only 2.0.
- Classification output now distinguishes positive evidence from manual-review signals.
- `run_pipeline.py` now supports offline snapshots and versioned PDF output.

### Preserved

- Repository history and the original `main` branch.
- Original v1 visualisations in `visualisations/`.
- Source evidence, matched rules, item IDs, source sections, and official URL audit trail.

### Still provisional

- Positive threshold 3.0.
- High-confidence threshold 5.0.
- Career readiness weight 2.0.
- Treatment of administrative case labels pending further client confirmation.

### Week 4 scope boundary

- Reran INFS6600 only.
- Did not analyse additional units or produce discipline-wide UG/PG results.
- Did not implement a landing page, LLM/RAG component, or formal model-evaluation study.
