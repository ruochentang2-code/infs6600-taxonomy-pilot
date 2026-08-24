# INFS6600 classification algorithm and results

## 1. Data scope

- Unit: INFS6600 Business Information Systems Capstone
- Session: 2026 Semester 2, following the project requirement to use the latest Semester 2 outline
- Official source: https://www.sydney.edu.au/units/INFS6600/2026-S2C-NE-CC
- Sections analysed: Overview, Learning Outcomes, assessment descriptions/types and Weekly Schedule
- Total: 32 independently auditable evidence items

## 2. Standards for the first two categories

### Work-Integrated and Applied Learning

An item is counted only when it contains explicit signals of an actual organisation, an industry or business partner, an actual business problem, actual professionals, authentic situations, or professional/boardroom presentation activity. Generic words such as `project`, `business` and `presentation` do not independently constitute evidence.

### Simulation and Case-Based Learning

An item must contain an explicit reference to simulation, a case study/case studies, role-play or a business scenario. Descriptions of a real project or problem-solving activity are not automatically treated as simulation or case-based learning.

## 3. Algorithm

1. Fetch the official public HTML and separately parse the overview, learning outcomes, assessment table and weekly schedule.
2. Convert every paragraph or table row into an evidence item containing an item ID, section, label, original text and source URL.
3. Normalise case, whitespace and dash variants while retaining the original evidence text.
4. Apply weighted phrase rules derived from the client-provided definitions and examples:
   - strong, explicit evidence receives a weight of 3.5-4.0;
   - supporting evidence receives a weight of 1.5-2.5;
   - the classification threshold is 3.0.
5. Count each item no more than once in each category, even when several synonymous phrases are present.
6. Include items that reach the threshold in the result; send weak sub-threshold signals to the review queue without counting them.
7. Export JSON, CSV, charts and an evidence table for manual audit.

## 4. Results

| Unit | Category | Classification | Evidence items | Distribution | Interpretation |
|---|---|---|---:|---|---|
| INFS6600 | Work-Integrated and Applied Learning | Yes - strong evidence | 11 | Overview 1; Learning Outcomes 3; Assessments 4; Weekly Schedule 3 | Strong and repeated evidence across the outline. |
| INFS6600 | Simulation and Case-Based Learning | Yes - provisional | 3 | Learning Outcomes 1; Assessments 2 | Explicit evidence exists, but two items rely on the administrative assessment type `Case studies`. |

Representative Work-Integrated and Applied Learning evidence includes `actual business organisation`, `actual business problem`, `actual business professionals`, `Partner Briefing`, `Pitch to Partner` and `Boardroom Presentation`.

Simulation and Case-Based Learning evidence includes `open-ended business scenarios` in LO2 and two assessments whose official type is `Case studies`. The assessment descriptions are Business Models and Group Report. The client should confirm whether classification should follow the published assessment type or the underlying teaching-task content.

## 5. Why this pilot does not begin with a complex NLP or LLM model

The immediate objective is to demonstrate that the data can be acquired, the decisions can be explained and each result can be reviewed. A transparent rule baseline exposes counting and interpretation issues early and creates client-reviewed labels. Once the client confirms the standards and a small set of units is manually annotated, embedding or LLM methods can be compared using precision, recall and error analysis.

## 6. Next extension

- Adjust rules and thresholds using client-confirmed positive and negative examples.
- Define the discipline-wide counting unit: evidence items, assessment/activity items, or units containing at least one category example.
- Build a manually annotated sample of 5-10 units.
- Add embedding similarity and LLM review after the rule baseline while retaining evidence text and human approval.
- Extend the process to all 2026 BIS undergraduate and postgraduate units, then produce overall, UG, PG and UG-versus-PG charts.

