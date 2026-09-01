# Week 4 v2 implementation record

## Source decisions

The v2 release implements the project decisions agreed on 26 August 2026.

## Team completion

The eight-member CS-44 project team completed this release: Houming Chen,
Haidi Sun, Yulei He, Ruochen Tang, Xiaopeng Ding, Huaicong Yu, Jinfei Qiu, and
Yihang Zhao. The team delivered the taxonomy configuration, evidence analysis,
scoring, visualisation, quality assurance, reports, and final release package.

| Agreed change | v2 implementation | Verification |
|---|---|---|
| Simulation and Case-Based Learning should be separated | Created independent `simulation` and `case_based` categories | Taxonomy validation and regression tests |
| Categories are not mutually exclusive | Multi-label policy is explicit; no argmax or single-category winner | Same item can classify into WIL and Project/Problem-Based |
| INFS6600 should appear in three categories | Regression expects WIL, Case-Based, and Project/Problem-Based | Real outline output contains all three |
| Authentic practice: “Give 4” | Weight 4.0 | Configuration test |
| Theory-practice: “Give 2” | Weight 2.0 | Configuration test |
| Practical teamwork: “Give 2” | Weight 2.0 | Configuration test |
| Career readiness requires a provisional calibration | Weight 2.0 with provisional status | Configuration test plus outstanding-decision note |
| Case/industry overlap needs review | Both categories may be positive; overlap notes are retained | INFS6600 AS06 supports WIL while its case label remains review-only |
| Count distinct evidence, not raw occurrences | Deduplication remains at item-category level; treated as a supporting correction, not a new analysis stream | One-rule-alternatives test |
| Add total scoring | Added classified score, review score, and total matched score | Summary JSON/CSV and charts |
| Explore taxonomy distribution diagrams | Added three static INFS6600 figures only | Static visual QA and PDF inclusion |

## Important interpretation changes

- `Type: Case studies` no longer creates automatic positive Case-Based evidence.
- LO02 `open-ended business scenarios` independently supports Case-Based Learning.
- Simulation requires simulation-specific evidence and is not inherited from Case-Based Learning.
- INFS6600 Project/Problem-Based evidence is independently identified from the actual business problem, project immersion, problem/opportunity scoping, and prototype validation.

## Configuration status

The taxonomy is versioned as `2026-09-01-week4-v2`. Thresholds and the Career readiness weight remain explicitly provisional pending validation.

## Scope guard

This release reruns INFS6600 only. The additional taxonomy categories are
configured as part of the complete pilot taxonomy, but they are not described
as empirically validated. Additional units,
discipline-wide comparisons, a landing page, LLM/RAG work, and formal model
evaluation are outside this Week 4 update.
