"""Create the two reviewed PDF deliverables for the tutor-feedback v2 release."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from taxonomy_config import load_taxonomy


NAVY = colors.HexColor("#102A43")
BLUE = colors.HexColor("#2F6B9A")
BLUE_LIGHT = colors.HexColor("#D9EAF5")
GOLD = colors.HexColor("#D5A021")
GOLD_LIGHT = colors.HexColor("#F7E7B2")
LIGHT = colors.HexColor("#F5F7FA")
GRID = colors.HexColor("#BCCCDC")
MUTED = colors.HexColor("#486581")


def _register_fonts() -> tuple[str, str]:
    regular = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    bold = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("CS44Arial", str(regular)))
        pdfmetrics.registerFont(TTFont("CS44ArialBold", str(bold)))
        return "CS44Arial", "CS44ArialBold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = _register_fonts()


def _safe(value: object) -> str:
    return html.escape(str(value).replace("–", "-").replace("—", "-"))


def _styles():
    sample = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "CS44Title",
            parent=sample["Title"],
            fontName=FONT_BOLD,
            fontSize=25,
            leading=29,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=6 * mm,
        ),
        "subtitle": ParagraphStyle(
            "CS44Subtitle",
            parent=sample["Normal"],
            fontName=FONT,
            fontSize=11,
            leading=15,
            textColor=MUTED,
            spaceAfter=5 * mm,
        ),
        "h1": ParagraphStyle(
            "CS44H1",
            parent=sample["Heading1"],
            fontName=FONT_BOLD,
            fontSize=16,
            leading=20,
            textColor=NAVY,
            spaceBefore=5 * mm,
            spaceAfter=3 * mm,
        ),
        "h2": ParagraphStyle(
            "CS44H2",
            parent=sample["Heading2"],
            fontName=FONT_BOLD,
            fontSize=12,
            leading=15,
            textColor=BLUE,
            spaceBefore=3 * mm,
            spaceAfter=2 * mm,
        ),
        "body": ParagraphStyle(
            "CS44Body",
            parent=sample["BodyText"],
            fontName=FONT,
            fontSize=9.2,
            leading=13,
            textColor=colors.HexColor("#243B53"),
            spaceAfter=2.5 * mm,
        ),
        "small": ParagraphStyle(
            "CS44Small",
            parent=sample["BodyText"],
            fontName=FONT,
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#243B53"),
        ),
        "small_bold": ParagraphStyle(
            "CS44SmallBold",
            parent=sample["BodyText"],
            fontName=FONT_BOLD,
            fontSize=7.5,
            leading=10,
            textColor=NAVY,
        ),
        "table_header": ParagraphStyle(
            "CS44TableHeader",
            parent=sample["BodyText"],
            fontName=FONT_BOLD,
            fontSize=7.5,
            leading=10,
            textColor=colors.white,
        ),
        "callout": ParagraphStyle(
            "CS44Callout",
            parent=sample["BodyText"],
            fontName=FONT_BOLD,
            fontSize=10.5,
            leading=14,
            textColor=NAVY,
        ),
        "center": ParagraphStyle(
            "CS44Center",
            parent=sample["BodyText"],
            fontName=FONT,
            fontSize=8,
            leading=10,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),
    }


STYLES = _styles()


def _p(value: object, style: str = "small") -> Paragraph:
    return Paragraph(_safe(value), STYLES[style])


def _bullet(text: str) -> Paragraph:
    return Paragraph(f"&#8226;&nbsp;&nbsp;{_safe(text)}", STYLES["body"])


def _table(data, widths, *, header: bool = True, font_size: float = 7.5) -> Table:
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("FONTNAME", (0, 0), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), font_size + 2.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.45, GRID),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
    ]
    if header:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ]
    table.setStyle(TableStyle(commands))
    return table


def _footer(canvas, doc) -> None:
    canvas.saveState()
    width, _ = doc.pagesize
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 15 * mm, width - doc.rightMargin, 15 * mm)
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 10 * mm, "CS-44 eight-member project team | INFS6600 taxonomy pilot v2")
    canvas.drawRightString(width - doc.rightMargin, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _callout(text: str, width: float) -> Table:
    table = Table([[Paragraph(_safe(text), STYLES["callout"])]], colWidths=[width])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BLUE_LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.8, BLUE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return table


def create_algorithm_pdf(result: dict, taxonomy: dict, path: Path) -> None:
    page_width, _ = A4
    usable = page_width - 36 * mm
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=21 * mm,
        title="Classification Algorithm: Tutor-Feedback v2",
        author="CS-44 Project Team (8 members)",
    )
    story = [
        Paragraph("Classification Algorithm: Tutor-Feedback v2", STYLES["title"]),
        Paragraph(
            "Transparent eight-category, multi-label baseline | Prepared collaboratively by the eight-member CS-44 project team",
            STYLES["subtitle"],
        ),
        _callout(
            "Team delivery: eight members held defined primary workstreams and completed taxonomy decisions, evidence review, quality assurance, and final acceptance collectively. Core decision: categories are not mutually exclusive. Simulation and Case-Based Learning are separate. Week 4 remains an INFS6600-only rerun.",
            usable,
        ),
        Paragraph("1. Tutor-directed changes", STYLES["h1"]),
        _bullet("Split Simulation from Case-Based Learning."),
        _bullet("Allow a unit and an evidence item to belong to more than one category."),
        _bullet("Expect INFS6600 in Work-Integrated and Applied, Project- and Problem-Based, and Case-Based Learning."),
        _bullet("Add category-level total scoring."),
        _bullet("Configure the remaining supplied taxonomy categories without analysing additional units."),
        Paragraph("Supporting and suggested pilot adjustments", STYLES["h2"]),
        _bullet("Count distinct evidence items rather than raw phrase occurrences."),
        _bullet("Retain overlapping industry/case evidence instead of forcing a single label."),
        Paragraph("2. Evidence unit and counting policy", STYLES["h1"]),
        Paragraph(_safe(taxonomy["counting_unit"]), STYLES["body"]),
        Paragraph(
            "Each outline item is evaluated once per category. A rule contributes its weight once even when several alternative phrases are present. Deduplication is at item-category level, so the same item can count once in several categories.",
            STYLES["body"],
        ),
        Paragraph("3. Taxonomy v2", STYLES["h1"]),
    ]
    taxonomy_rows = [[_p("Category", "table_header"), _p("Definition", "table_header"), _p("Overlap / review rule", "table_header")]]
    for category in taxonomy["categories"]:
        taxonomy_rows.append(
            [
                _p(category["name"], "small_bold"),
                _p(category["definition"]),
                _p(
                    f"{category.get('overlap_notes', '')} {category.get('review_guidance', '')}"
                ),
            ]
        )
    story += [_table(taxonomy_rows, [44 * mm, 67 * mm, 63 * mm])]

    story += [Paragraph("4. Tutor-adjusted WIL weights", STYLES["h1"])]
    wil = next(
        category
        for category in taxonomy["categories"]
        if category["id"] == "work_integrated_applied"
    )
    weight_rows = [[_p("Rule group", "table_header"), _p("v2 weight", "table_header"), _p("Status", "table_header")]]
    for rule in wil["rules"]:
        weight_rows.append(
            [
                _p(rule["label"]),
                _p(f"{float(rule['weight']):.1f}", "center"),
                _p(rule.get("weight_status", "configured")),
            ]
        )
    story += [
        _table(weight_rows, [72 * mm, 28 * mm, 74 * mm]),
        KeepTogether(
            [
                Paragraph("5. Decision thresholds and confidence", STYLES["h1"]),
                _callout(
                    f"Positive >= {taxonomy['decision_thresholds']['positive']}; high confidence >= {taxonomy['decision_thresholds']['high_confidence']}. Status: {taxonomy['decision_thresholds']['status']}. These values remain configurable and are not represented as client-validated cut-offs.",
                    usable,
                ),
            ]
        ),
        Spacer(1, 4 * mm),
        KeepTogether(
            [
                Paragraph("6. Scoring and aggregation", STYLES["h1"]),
                _bullet("Normalise lowercase, whitespace, apostrophes, and dash variants."),
                _bullet("Sum weights for matched rule groups within one item-category decision."),
                _bullet("Send an item to review when it is below the positive threshold or contains only review-required rules."),
                _bullet("Classified score total = sum of positive item scores for the unit-category pair."),
                _bullet("Review score total is shown separately and never silently added to the positive score."),
            ]
        ),
        Paragraph("7. Case-Based versus Simulation", STYLES["h1"]),
        Paragraph(
            "Open-ended business scenarios support Case-Based Learning. A Simulation result requires simulation-specific evidence such as a recreated environment, simulation activity, or role play. The administrative assessment type 'Case studies' is assigned weight 2.0 and remains in the review queue unless stronger case-method evidence appears in the same item.",
            STYLES["body"],
        ),
        Paragraph("8. INFS6600 regression checks", STYLES["h1"]),
    ]
    observed = set(result["tutor_feedback_regression"]["observed_positive_categories"])
    checks = [
        ("Eight taxonomy categories loaded", len(taxonomy["categories"]) == 8),
        ("Expected three INFS6600 categories present", result["tutor_feedback_regression"]["expected_categories_present"]),
        ("Simulation evaluated independently and not positive", "simulation" not in observed),
        ("Administrative case labels remain review-only", all(row["category_id"] != "case_based" or row["score"] < 3.0 for row in result["review_queue"] if row["category_id"] == "case_based")),
        ("Thresholds labelled provisional", "provisional" in taxonomy["decision_thresholds"]["status"]),
    ]
    check_rows = [[_p("Acceptance check", "table_header"), _p("Result", "table_header")]]
    check_rows += [[_p(label), _p("PASS" if passed else "FAIL", "small_bold")] for label, passed in checks]
    story += [
        _table(check_rows, [140 * mm, 34 * mm]),
        Paragraph("9. Open client decisions", STYLES["h1"]),
        _bullet("Confirm whether the 3.0 positive and 5.0 high-confidence thresholds should remain."),
        _bullet("Confirm the tentative Career readiness weight of 2.0."),
        _bullet("Confirm whether administrative 'Case studies' labels should remain at review weight 2.0."),
        Paragraph("10. Audit trail", STYLES["h1"]),
        Paragraph(
            f"Taxonomy version: {_safe(result['taxonomy_version'])}<br/>Official source: {_safe(result['source_url'])}<br/>Retrieved: {_safe(result.get('retrieved_at', ''))}",
            STYLES["body"],
        ),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)


def _fit_image(path: Path, max_width: float, max_height: float) -> Image:
    image = Image(str(path))
    ratio = min(max_width / image.imageWidth, max_height / image.imageHeight)
    image.drawWidth = image.imageWidth * ratio
    image.drawHeight = image.imageHeight * ratio
    image.hAlign = "CENTER"
    return image


def create_mapping_pdf(
    result: dict, taxonomy: dict, visualisations: Path, path: Path
) -> None:
    page_size = landscape(A4)
    page_width, page_height = page_size
    usable = page_width - 34 * mm
    doc = SimpleDocTemplate(
        str(path),
        pagesize=page_size,
        leftMargin=17 * mm,
        rightMargin=17 * mm,
        topMargin=16 * mm,
        bottomMargin=21 * mm,
        title="INFS6600 Course-Category Mapping v2",
        author="CS-44 Project Team (8 members)",
    )
    positives = [
        row["category"] for row in result["summary"] if row["belongs_to_category"]
    ]
    story = [
        Paragraph("INFS6600 Course-Category Mapping v2", STYLES["title"]),
        Paragraph(
            f"{_safe(result['unit_title'])} | {_safe(result['session'])} | Taxonomy {_safe(result['taxonomy_version'])} | Eight-member CS-44 team delivery",
            STYLES["subtitle"],
        ),
        _callout(
            "Completed collaboratively by the eight-member CS-44 project team. Positive categories: "
            + "; ".join(positives)
            + ". Categories are not mutually exclusive; percentages and counts are not expected to sum to 100%. This report covers INFS6600 only.",
            usable,
        ),
        Paragraph("1. Category summary", STYLES["h1"]),
    ]
    summary_rows = [[
        _p("Category", "table_header"),
        _p("Status", "table_header"),
        _p("Positive items", "table_header"),
        _p("Review items", "table_header"),
        _p("Classified score", "table_header"),
        _p("Review score", "table_header"),
        _p("Positive sections", "table_header"),
    ]]
    section_labels = {
        "overview": "OV",
        "learning_outcome": "LO",
        "assessment": "AS",
        "weekly_schedule": "WK",
    }
    for row in result["summary"]:
        sections = "; ".join(
            f"{section_labels.get(section, section)}={count}"
            for section, count in row["section_counts"].items()
        ) or "None"
        summary_rows.append(
            [
                _p(row["category"], "small_bold"),
                _p(row["classification_status"]),
                _p(row["evidence_item_count"], "center"),
                _p(row["review_item_count"], "center"),
                _p(f"{row['classified_score_total']:.1f}", "center"),
                _p(f"{row['review_score_total']:.1f}", "center"),
                _p(sections),
            ]
        )
    story += [
        _table(
            summary_rows,
            [62 * mm, 29 * mm, 22 * mm, 21 * mm, 25 * mm, 22 * mm, 58 * mm],
        ),
        Paragraph("2. Positive evidence", STYLES["h1"]),
    ]
    evidence_rows = [[
        _p("Category", "table_header"),
        _p("Item", "table_header"),
        _p("Section", "table_header"),
        _p("Evidence label", "table_header"),
        _p("Score", "table_header"),
        _p("Matched rules", "table_header"),
    ]]
    for row in result["evidence"]:
        rules = "; ".join(match["rule"] for match in row["matched_rules"])
        evidence_rows.append(
            [
                _p(row["category"]),
                _p(row["item_id"], "center"),
                _p(section_labels.get(row["section"], row["section"]), "center"),
                _p(row["label"]),
                _p(f"{row['score']:.1f}", "center"),
                _p(rules),
            ]
        )
    story += [
        _table(
            evidence_rows,
            [50 * mm, 17 * mm, 17 * mm, 63 * mm, 17 * mm, 75 * mm],
            font_size=7.1,
        ),
        Paragraph("3. Manual-review queue", STYLES["h1"]),
    ]
    review_rows = [[
        _p("Category", "table_header"),
        _p("Item", "table_header"),
        _p("Evidence label", "table_header"),
        _p("Score", "table_header"),
        _p("Why review", "table_header"),
    ]]
    for row in result["review_queue"]:
        rules = "; ".join(match["rule"] for match in row["matched_rules"])
        review_rows.append(
            [
                _p(row["category"]),
                _p(row["item_id"], "center"),
                _p(row["label"]),
                _p(f"{row['score']:.1f}", "center"),
                _p(rules),
            ]
        )
    story += [
        _table(review_rows, [55 * mm, 18 * mm, 72 * mm, 18 * mm, 76 * mm]),
        Paragraph("4. Interpretation", STYLES["h1"]),
        _bullet("Work-Integrated and Applied Learning has 11 positive items across all four source sections."),
        _bullet("Case-Based Learning is positive from LO02; the two assessment-type labels remain review-only."),
        _bullet("Project- and Problem-Based Learning is independently positive from the actual problem, project immersion, problem/opportunity scoping, and prototype validation."),
        _bullet("Simulation has no positive evidence and is not inherited from Case-Based Learning."),
        _bullet("Entrepreneurial Learning has two review signals, but no explicit startup, venture, or entrepreneurship evidence."),
        PageBreak(),
        Paragraph("5. Evidence-count distribution", STYLES["h1"]),
        _fit_image(
            visualisations / "category_summary.png", usable, page_height - 66 * mm
        ),
        PageBreak(),
        Paragraph("6. Category score distribution", STYLES["h1"]),
        _fit_image(
            visualisations / "category_scores.png", usable, page_height - 66 * mm
        ),
        PageBreak(),
        Paragraph("7. Source-section distribution", STYLES["h1"]),
        _fit_image(
            visualisations / "evidence_by_section.png", usable, page_height - 66 * mm
        ),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--taxonomy", type=Path)
    parser.add_argument("--visualisations", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    result = json.loads(args.result.read_text(encoding="utf-8"))
    taxonomy = load_taxonomy(args.taxonomy)
    algorithm_path = args.output_dir / "02_Classification_Algorithm_Detailed_v2.pdf"
    mapping_path = args.output_dir / "05_INFS6600_Course_Category_Mapping_v2.pdf"
    create_algorithm_pdf(result, taxonomy, algorithm_path)
    create_mapping_pdf(result, taxonomy, args.visualisations, mapping_path)
    print(f"Wrote PDF reports to {args.output_dir}")


if __name__ == "__main__":
    main()
