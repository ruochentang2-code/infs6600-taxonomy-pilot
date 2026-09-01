# Tutor feedback implementation record

## Source decisions

The v2 release implements the client meeting and document feedback received on 26 August 2026.

## Delivery ownership

This release was completed collaboratively by the eight-member CS-44 project
team: Houming Chen, Haidi Sun, Yulei He, Ruochen Tang, Xiaopeng Ding, Huaicong
Yu, Jinfei Qiu, and Yihang Zhao. Each member held primary ownership for a
defined workstream, while taxonomy decisions, INFS6600 evidence review,
quality assurance, and final acceptance were completed collectively.

| Tutor feedback | v2 implementation | Verification |
|---|---|---|
| Simulation and Case-Based Learning should be separated | Created independent `simulation` and `case_based` categories | Taxonomy validation and regression tests |
| Categories are not mutually exclusive | Multi-label policy is explicit; no argmax or single-category winner | Same item can classify into WIL and Project/Problem-Based |
| INFS6600 should appear in three categories | Regression expects WIL, Case-Based, and Project/Problem-Based | Real outline output contains all three |
| Authentic practice: “Give 4” | Weight 4.0 | Configuration test |
| Theory-practice: “Give 2” | Weight 2.0 | Configuration test |
| Practical teamwork: “Give 2” | Weight 2.0 | Configuration test |
| Career readiness: “Maybe 2 here” | Weight 2.0 with provisional status | Configuration test plus outstanding-decision note |
| Case/industry overlap needs review | Both categories may be positive; overlap notes are retained | INFS6600 AS06 supports WIL while its case label remains review-only |
| Meeting suggestion: count distinct evidence, not raw occurrences | Deduplication remains at item-category level; treated as a supporting correction, not a new analysis stream | One-rule-alternatives test |
| Add total scoring | Added classified score, review score, and total matched score | Summary JSON/CSV and charts |
| Explore taxonomy distribution diagrams | Added three static INFS6600 figures only | Static visual QA and PDF inclusion |

## Important interpretation changes

- `Type: Case studies` no longer creates automatic positive Case-Based evidence.
- LO02 `open-ended business scenarios` independently supports Case-Based Learning.
- Simulation requires simulation-specific evidence and is not inherited from Case-Based Learning.
- INFS6600 Project/Problem-Based evidence is independently identified from the actual business problem, project immersion, problem/opportunity scoping, and prototype validation.

## Configuration status

The taxonomy is versioned as `2026-09-01-tutor-feedback-v2`. Thresholds and the tentative Career readiness weight remain explicitly provisional pending client confirmation.

## Scope guard

This release reruns INFS6600 only. The additional taxonomy categories are
configured in response to the instruction to proceed with the rest of the
taxonomy, but they are not described as client-validated. Additional units,
discipline-wide comparisons, a landing page, LLM/RAG work, and formal model
evaluation are outside this Week 4 update.
