# Tutor feedback implementation record

## Source decisions

The v2 release implements the client meeting and document feedback received on 26 August 2026.

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
| Count distinct evidence, not raw occurrences | Deduplication remains at item-category level | One-rule-alternatives test |
| Add total scoring | Added classified score, review score, and total matched score | Summary JSON/CSV and charts |
| Add taxonomy distribution diagrams | Added category count, category score, and source-section figures | Static visual QA and PDF inclusion |

## Important interpretation changes

- `Type: Case studies` no longer creates automatic positive Case-Based evidence.
- LO02 `open-ended business scenarios` independently supports Case-Based Learning.
- Simulation requires simulation-specific evidence and is not inherited from Case-Based Learning.
- INFS6600 Project/Problem-Based evidence is independently identified from the actual business problem, project immersion, problem/opportunity scoping, and prototype validation.

## Configuration status

The taxonomy is versioned as `2026-09-01-tutor-feedback-v2`. Thresholds and the tentative Career readiness weight remain explicitly provisional pending client confirmation.
