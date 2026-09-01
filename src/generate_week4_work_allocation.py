"""Generate the Week 4 eight-person work allocation meeting handout."""

from __future__ import annotations

import argparse
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


OUTPUT = Path("output/docx/CS-44_Week4_Eight-Person_Work_Allocation.docx")

NAVY = "1F4D78"
BLUE = "2E74B5"
BLUE_DARK = "17365D"
BLUE_LIGHT = "DCE6F1"
PALE_BLUE = "EEF4F8"
GOLD = "D6A84B"
PALE_GOLD = "FFF4D6"
GREY = "F2F4F7"
MID_GREY = "D0D7DE"
TEXT = "243B53"
MUTED = "52606D"
WHITE = "FFFFFF"
GREEN = "2E7D32"


MEMBERS = [
    {
        "number": "01",
        "name": "Houming Chen",
        "stream": "Coordination, tutor-feedback traceability and scope control",
        "completed": [
            "Converted the meeting, email, PDF comments and scope-document changes into one acceptance checklist.",
            "Kept Week 4 limited to the tutor-requested INFS6600 update and its necessary supporting work.",
            "Coordinated the eight workstreams, hand-offs and shared meeting narrative.",
        ],
        "outputs": [
            "Meeting decision record and tutor-feedback implementation record",
            "Week 4 delivery checklist and scope guard",
            "Integrated meeting handout and speaking order",
        ],
        "line": "I coordinated the tutor-feedback v2 update, mapped every requested change to an acceptance check, and kept the team within the agreed INFS6600-only Week 4 scope.",
    },
    {
        "number": "02",
        "name": "Haidi Sun",
        "stream": "Taxonomy definitions and versioned configuration",
        "completed": [
            "Configured all eight supplied taxonomy categories for the pilot.",
            "Separated Simulation from Case-Based Learning and clarified their definitions.",
            "Added overlap notes, review guidance and provisional-status labels to the taxonomy.",
        ],
        "outputs": [
            "config/taxonomy_v2.json",
            "Eight-category standards in the detailed algorithm report",
            "Configuration notes for unresolved client decisions",
        ],
        "line": "I updated the supplied taxonomy into a versioned eight-category configuration and made Simulation and Case-Based Learning independent categories with clear overlap and review guidance.",
    },
    {
        "number": "03",
        "name": "Yulei He",
        "stream": "Multi-label, overlap and review policy",
        "completed": [
            "Defined categories as non-mutually-exclusive and removed any single-winner assumption.",
            "Retained an evidence item once per category so genuine overlap remains visible.",
            "Moved administrative “Case studies” labels to review rather than treating them as automatic positive evidence.",
        ],
        "outputs": [
            "Multi-label and item-category deduplication policy",
            "Case/industry overlap interpretation",
            "Manual-review rules and review-queue criteria",
        ],
        "line": "I formalised the multi-label policy: a unit or evidence item can support several categories, while ambiguous administrative labels stay visible in the review queue instead of becoming automatic positives.",
    },
    {
        "number": "04",
        "name": "Ruochen Tang",
        "stream": "INFS6600 source evidence and pilot rerun",
        "completed": [
            "Verified the INFS6600 2026 Semester 2 public-outline snapshot and official source URL.",
            "Maintained auditable evidence units across overview, learning outcomes, assessments and weekly schedule.",
            "Reran the pilot and checked item IDs, source sections and original evidence text.",
        ],
        "outputs": [
            "Versioned INFS6600 source snapshot and course-information summary",
            "Classified-evidence and review-queue datasets",
            "Traceable evidence for the three positive categories",
        ],
        "line": "I prepared and verified the INFS6600 evidence base, reran the pilot across all four outline sections, and ensured every result remained traceable to an item ID and the official source.",
    },
    {
        "number": "05",
        "name": "Xiaopeng Ding",
        "stream": "Scoring method, WIL weights and confidence logic",
        "completed": [
            "Applied the tutor comments to the four WIL weights: 4.0, 2.0, 2.0 and provisional 2.0.",
            "Kept one contribution per matched rule group and separated classified score from review score.",
            "Documented the 3.0 and 5.0 thresholds as configurable and provisional.",
        ],
        "outputs": [
            "Updated weighted phrase-scoring configuration and logic",
            "Classified, review and total matched score fields",
            "02_Classification_Algorithm_Detailed_v2.pdf",
        ],
        "line": "I implemented the tutor’s WIL weighting comments, separated positive and review scoring, and kept the decision thresholds explicit and provisional rather than presenting them as validated cut-offs.",
    },
    {
        "number": "06",
        "name": "Huaicong Yu",
        "stream": "Evidence aggregation and course-category mapping",
        "completed": [
            "Counted distinct evidence items rather than raw keyword occurrences.",
            "Aggregated positive items, review items, classified score, review score and section counts by category.",
            "Produced the complete eight-category mapping while preserving the three positive INFS6600 allocations.",
        ],
        "outputs": [
            "classification_results.json and unit_category_summary.csv",
            "Course-category mapping in Markdown and CSV",
            "Verified WIL, Case-Based and Project/Problem-Based positive result",
        ],
        "line": "I built the category-level aggregation and mapping outputs, using distinct evidence-item counts and separate score totals so the three INFS6600 allocations can be audited clearly.",
    },
    {
        "number": "07",
        "name": "Jinfei Qiu",
        "stream": "Visualisation and report production",
        "completed": [
            "Created three INFS6600-only taxonomy figures for evidence counts, scores and source sections.",
            "Integrated total scoring, review signals and multi-label interpretation into the pilot report.",
            "Produced the updated course-category mapping report for meeting review.",
        ],
        "outputs": [
            "Three versioned PNG figures",
            "pilot_results_v2.md",
            "05_INFS6600_Course_Category_Mapping_v2.pdf",
        ],
        "line": "I turned the updated results into the three requested pilot-scale figures and the mapping report, showing evidence counts, total scores and where the evidence appears in the unit outline.",
    },
    {
        "number": "08",
        "name": "Yihang Zhao",
        "stream": "Quality assurance, release packaging and version control",
        "completed": [
            "Ran offline unit and tutor-feedback regression checks for the eight-category multi-label result.",
            "Verified generated reports, release hashes and the two final PDF deliverables.",
            "Packaged the update as a separate tutor-feedback-v2 Git version while preserving the original main branch.",
        ],
        "outputs": [
            "Regression tests and acceptance-check results",
            "SHA-256 release manifest, README and changelog",
            "Versioned Git branch and final delivery package",
        ],
        "line": "I completed release QA and version packaging, confirmed the expected three-category result and kept this Week 4 update separate so the original repository version remains intact.",
    },
]


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=90, start=120, bottom=90, end=120) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for edge, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        tag = f"w:{edge}"
        node = tc_mar.find(qn(tag))
        if node is None:
            node = OxmlElement(tag)
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_cell_width(cell, width_dxa: int) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(width_dxa))
    tc_w.set(qn("w:type"), "dxa")


def set_table_fixed(table, widths: list[int]) -> None:
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_layout = tbl_pr.find(qn("w:tblLayout"))
    if tbl_layout is None:
        tbl_layout = OxmlElement("w:tblLayout")
        tbl_pr.append(tbl_layout)
    tbl_layout.set(qn("w:type"), "fixed")
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            set_cell_width(cell, widths[idx])
            cell.width = Inches(widths[idx] / 1440)
            set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def prevent_row_split(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    if tr_pr.find(qn("w:cantSplit")) is None:
        tr_pr.append(OxmlElement("w:cantSplit"))


def repeat_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_cell_border(cell, color=MID_GREY, size="6", **edges) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        settings = edges.get(edge, {"val": "single", "sz": size, "color": color})
        tag = f"w:{edge}"
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        for key, value in settings.items():
            element.set(qn(f"w:{key}"), str(value))


def add_run(paragraph, text: str, *, bold=False, color=TEXT, size=None, italic=False):
    run = paragraph.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.name = "Calibri"
    run.font.color.rgb = RGBColor.from_string(color)
    if size:
        run.font.size = Pt(size)
    return run


def clear_cell(cell) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)


def add_bullet(cell, text: str, *, compact=True) -> None:
    paragraph = cell.add_paragraph(style="List Bullet")
    paragraph.paragraph_format.left_indent = Inches(0.18)
    paragraph.paragraph_format.first_line_indent = Inches(-0.12)
    paragraph.paragraph_format.space_after = Pt(2 if compact else 4)
    paragraph.paragraph_format.line_spacing = 1.0
    add_run(paragraph, text, size=8.6)


def add_field(paragraph, field: str) -> None:
    run = paragraph.add_run()
    fld_char = OxmlElement("w:fldChar")
    fld_char.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = field
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_char, instr_text, fld_end])


def configure_document(document: Document) -> None:
    section = document.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.72)
    section.left_margin = Inches(0.78)
    section.right_margin = Inches(0.78)
    section.header_distance = Inches(0.32)
    section.footer_distance = Inches(0.35)

    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10)
    normal.font.color.rgb = RGBColor.from_string(TEXT)
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.08

    title = styles["Title"]
    title.font.name = "Calibri"
    title.font.size = Pt(25)
    title.font.bold = True
    title.font.color.rgb = RGBColor.from_string(NAVY)
    title.paragraph_format.space_after = Pt(5)

    for style_name, size, color, before, after in (
        ("Heading 1", 16, BLUE, 15, 7),
        ("Heading 2", 13, NAVY, 11, 5),
        ("Heading 3", 11.5, BLUE_DARK, 8, 4),
    ):
        style = styles[style_name]
        style.font.name = "Calibri"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    list_style = styles["List Bullet"]
    list_style.font.name = "Calibri"
    list_style.font.size = Pt(9)
    list_style.paragraph_format.space_after = Pt(3)

    for sec in document.sections:
        header = sec.header
        p = header.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(3)
        add_run(p, "CS-44", bold=True, color=NAVY, size=8.5)
        add_run(p, "  |  Week 4 Tutor-Feedback v2  |  Eight-Person Work Allocation", color=MUTED, size=8.5)
        p_pr = p._p.get_or_add_pPr()
        p_bdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "8")
        bottom.set(qn("w:color"), BLUE)
        bottom.set(qn("w:space"), "3")
        p_bdr.append(bottom)
        p_pr.append(p_bdr)

        footer = sec.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_run(fp, "CS-44 Project Team (8 members)  •  1 September 2026  •  Page ", color=MUTED, size=8)
        add_field(fp, "PAGE")


def add_metadata(document: Document) -> None:
    table = document.add_table(rows=2, cols=4)
    set_table_fixed(table, [1200, 3480, 1200, 3480])
    values = [
        ("Project", "Exploring Pedagogical Innovations in Business Education", "Group", "CS-44"),
        ("Meeting", "Week 4 progress report", "Release", "tutor-feedback-v2"),
    ]
    for row, values_row in zip(table.rows, values):
        prevent_row_split(row)
        for idx, value in enumerate(values_row):
            cell = row.cells[idx]
            clear_cell(cell)
            set_cell_shading(cell, GREY if idx % 2 == 0 else WHITE)
            set_cell_border(cell)
            p = cell.paragraphs[0]
            add_run(p, value, bold=idx % 2 == 0, color=NAVY if idx % 2 == 0 else TEXT, size=8.5)
    document.add_paragraph().paragraph_format.space_after = Pt(0)


def add_callout(document: Document, text: str, *, fill=BLUE_LIGHT, border=BLUE) -> None:
    table = document.add_table(rows=1, cols=1)
    set_table_fixed(table, [9360])
    cell = table.cell(0, 0)
    set_cell_shading(cell, fill)
    set_cell_border(cell, color=border, size="10")
    clear_cell(cell)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    add_run(p, text, bold=True, color=NAVY, size=10)


def add_scope_table(document: Document) -> None:
    document.add_heading("Completed Week 4 scope", level=1)
    table = document.add_table(rows=1, cols=3)
    widths = [3120, 3120, 3120]
    set_table_fixed(table, widths)
    headers = ["Tutor-directed", "Necessary supporting work", "Tutor suggestions at pilot scale"]
    for idx, header in enumerate(headers):
        cell = table.rows[0].cells[idx]
        clear_cell(cell)
        set_cell_shading(cell, NAVY)
        set_cell_border(cell, color=WHITE, size="4")
        p = cell.paragraphs[0]
        add_run(p, header, bold=True, color=WHITE, size=9)
    repeat_header(table.rows[0])
    body = table.add_row()
    prevent_row_split(body)
    content = [
        [
            "Separated Simulation and Case-Based Learning",
            "Applied non-exclusive multi-label classification",
            "Updated tutor-commented WIL weights",
            "Added total scoring and configured all supplied categories",
        ],
        [
            "Reran INFS6600 only",
            "Added overlap and review policy",
            "Produced structured evidence and mapping outputs",
            "Added regression tests, release notes and audit hashes",
        ],
        [
            "Counted distinct evidence items",
            "Created three INFS6600 category-distribution figures",
            "Kept both suggestions inside the existing pilot scope",
        ],
    ]
    for idx, lines in enumerate(content):
        cell = body.cells[idx]
        clear_cell(cell)
        set_cell_shading(cell, PALE_BLUE if idx < 2 else PALE_GOLD)
        set_cell_border(cell)
        for line in lines:
            add_bullet(cell, line)


def add_allocation_overview(document: Document) -> None:
    document.add_page_break()
    document.add_heading("Eight-person allocation at a glance", level=1)
    p = document.add_paragraph()
    add_run(p, "Primary ownership indicates accountability for coordination and review; it does not mean the work was completed in isolation.", italic=True, color=MUTED, size=9)

    table = document.add_table(rows=1, cols=4)
    widths = [600, 1830, 4650, 2280]
    set_table_fixed(table, widths)
    headers = ["#", "Member", "Primary workstream", "Meeting focus"]
    for idx, header in enumerate(headers):
        cell = table.rows[0].cells[idx]
        clear_cell(cell)
        set_cell_shading(cell, NAVY)
        set_cell_border(cell, color=WHITE, size="4")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if idx in (0, 3) else WD_ALIGN_PARAGRAPH.LEFT
        add_run(p, header, bold=True, color=WHITE, size=8.5)
    repeat_header(table.rows[0])

    focuses = [
        "Scope and integration",
        "Taxonomy changes",
        "Overlap policy",
        "Evidence rerun",
        "Scoring changes",
        "Results and mapping",
        "Figures and reports",
        "QA and release",
    ]
    for member, focus in zip(MEMBERS, focuses):
        row = table.add_row()
        prevent_row_split(row)
        fill = WHITE if int(member["number"]) % 2 else GREY
        for idx, value in enumerate((member["number"], member["name"], member["stream"], focus)):
            cell = row.cells[idx]
            clear_cell(cell)
            set_cell_shading(cell, fill)
            set_cell_border(cell)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if idx in (0, 3) else WD_ALIGN_PARAGRAPH.LEFT
            add_run(p, value, bold=idx == 1, color=NAVY if idx in (0, 1) else TEXT, size=8.4)

    document.add_heading("Shared completion rule", level=2)
    add_callout(
        document,
        "Every workstream was cross-checked by at least one other member, and taxonomy interpretation, INFS6600 evidence acceptance, scope decisions and final release acceptance were agreed collectively by all eight members.",
    )


def add_member_card(document: Document, member: dict) -> None:
    table = document.add_table(rows=1, cols=2)
    widths = [4680, 4680]
    set_table_fixed(table, widths)
    header = table.rows[0]
    merged = header.cells[0].merge(header.cells[1])
    clear_cell(merged)
    set_cell_shading(merged, BLUE_DARK)
    set_cell_border(merged, color=BLUE_DARK, size="8")
    p = merged.paragraphs[0]
    add_run(p, f"{member['number']}  {member['name']}", bold=True, color=WHITE, size=11)
    add_run(p, f"  |  {member['stream']}", color=WHITE, size=9.5)

    body = table.add_row()
    prevent_row_split(body)
    for idx, heading in enumerate(("Completed responsibilities", "Concrete deliverables")):
        cell = body.cells[idx]
        clear_cell(cell)
        set_cell_shading(cell, WHITE if idx == 0 else PALE_BLUE)
        set_cell_border(cell)
        p = cell.paragraphs[0]
        add_run(p, heading, bold=True, color=BLUE, size=8.8)
        items = member["completed"] if idx == 0 else member["outputs"]
        for item in items:
            add_bullet(cell, item)

    line_row = table.add_row()
    prevent_row_split(line_row)
    line_cell = line_row.cells[0].merge(line_row.cells[1])
    clear_cell(line_cell)
    set_cell_shading(line_cell, PALE_GOLD)
    set_cell_border(line_cell, color=GOLD, size="6")
    p = line_cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    add_run(p, "Suggested meeting line: ", bold=True, color=NAVY, size=8.6)
    add_run(p, f"“{member['line']}”", italic=True, color=TEXT, size=8.6)

    spacer = document.add_paragraph()
    spacer.paragraph_format.space_after = Pt(2)


def add_member_pages(document: Document) -> None:
    document.add_page_break()
    document.add_heading("Individual completed contributions — members 1–4", level=1)
    for member in MEMBERS[:4]:
        add_member_card(document, member)

    document.add_page_break()
    document.add_heading("Individual completed contributions — members 5–8", level=1)
    for member in MEMBERS[4:]:
        add_member_card(document, member)


def add_final_page(document: Document) -> None:
    document.add_page_break()
    document.add_heading("Meeting run sheet and shared wording", level=1)
    add_callout(
        document,
        "Recommended total speaking time: 8–10 minutes. Each member owns one 40–60 second update; Houming opens with scope and Yihang closes with verification and release status.",
    )

    document.add_heading("Speaking order", level=2)
    table = document.add_table(rows=1, cols=3)
    widths = [900, 2550, 5910]
    set_table_fixed(table, widths)
    for idx, header in enumerate(("Order", "Speaker", "One-sentence hand-off")):
        cell = table.rows[0].cells[idx]
        clear_cell(cell)
        set_cell_shading(cell, NAVY)
        set_cell_border(cell, color=WHITE, size="4")
        p = cell.paragraphs[0]
        add_run(p, header, bold=True, color=WHITE, size=8.5)
    repeat_header(table.rows[0])
    handoffs = [
        "Tutor feedback, acceptance checklist and Week 4 scope",
        "Eight-category taxonomy and Simulation/Case split",
        "Multi-label, overlap and review treatment",
        "INFS6600 evidence preparation and rerun",
        "Weights, scoring and provisional thresholds",
        "Distinct counts, totals and category mapping",
        "Pilot-scale figures and reports",
        "Tests, release manifest, PDFs and versioned Git delivery",
    ]
    for idx, (member, handoff) in enumerate(zip(MEMBERS, handoffs), start=1):
        row = table.add_row()
        prevent_row_split(row)
        fill = WHITE if idx % 2 else GREY
        for col, value in enumerate((str(idx), member["name"], handoff)):
            cell = row.cells[col]
            clear_cell(cell)
            set_cell_shading(cell, fill)
            set_cell_border(cell)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col == 0 else WD_ALIGN_PARAGRAPH.LEFT
            add_run(p, value, bold=col == 1, color=NAVY if col == 1 else TEXT, size=8.5)

    document.add_heading("Approved team delivery statement", level=2)
    add_callout(
        document,
        "The Week 4 tutor-feedback v2 release was completed collaboratively by the eight-member CS-44 project team. Each member held primary ownership for a defined workstream, while taxonomy decisions, INFS6600 evidence review, quality assurance and final acceptance were completed collectively.",
        fill=BLUE_LIGHT,
    )

    document.add_heading("Closing result statement", level=2)
    p = document.add_paragraph()
    add_run(
        p,
        "Together, the team applied the tutor’s requested changes to the existing INFS6600 pilot, preserved multi-label classification, and confirmed positive allocation to Work-Integrated and Applied Learning, Case-Based Learning, and Project- and Problem-Based Learning. No additional units or unrelated future-stage work were advanced this week.",
        size=9.4,
    )

    document.add_heading("Scope guard for questions", level=2)
    guard = document.add_table(rows=1, cols=2)
    set_table_fixed(guard, [4680, 4680])
    for idx, (title, items, fill) in enumerate(
        (
            (
                "Completed this week",
                ["Tutor-directed INFS6600 v2 changes", "Necessary supporting implementation", "Two pilot-scale tutor suggestions"],
                PALE_BLUE,
            ),
            (
                "Not advanced this week",
                ["Additional units or UG/PG comparison", "Landing page or LLM/RAG work", "Formal precision/recall/F1 evaluation"],
                GREY,
            ),
        )
    ):
        cell = guard.cell(0, idx)
        clear_cell(cell)
        set_cell_shading(cell, fill)
        set_cell_border(cell)
        p = cell.paragraphs[0]
        add_run(p, title, bold=True, color=NAVY, size=9)
        for item in items:
            add_bullet(cell, item)


def build_document(path: Path) -> None:
    document = Document()
    configure_document(document)
    document.core_properties.title = "CS-44 Week 4 Eight-Person Work Allocation"
    document.core_properties.subject = "Tutor-feedback v2 meeting reporting notes"
    document.core_properties.author = "CS-44 Project Team (8 members)"
    document.core_properties.comments = "Prepared collaboratively for the Week 4 project meeting."

    p = document.add_paragraph(style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_run(p, "Week 4 Eight-Person Work Allocation", bold=True, color=NAVY, size=25)
    subtitle = document.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(10)
    add_run(subtitle, "INFS6600 Taxonomy Pilot — Tutor-Feedback v2", bold=True, color=BLUE, size=13)
    add_run(subtitle, "\nMeeting reporting notes and completed contribution record", color=MUTED, size=10)

    add_metadata(document)
    add_callout(
        document,
        "All Week 4 deliverables were completed collaboratively by the eight-member CS-44 team. The allocation below identifies each member’s primary ownership for meeting reporting; it does not represent isolated or exclusive authorship.",
    )

    p = document.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    add_run(p, "Week 3 continuity basis", bold=True, color=NAVY, size=10)
    p = document.add_paragraph()
    p.paragraph_format.space_after = Pt(7)
    add_run(
        p,
        "This Week 4 allocation continues the Week 3 team-level workflow from scope and taxonomy through extraction, classification, visualisation and handover. Primary responsibilities follow that same end-to-end chain, while the explicitly documented pilot-demo and scoring-method activities remain continuous with the meeting record.",
        size=9.2,
    )

    add_scope_table(document)
    add_allocation_overview(document)
    add_member_pages(document)
    add_final_page(document)

    path.parent.mkdir(parents=True, exist_ok=True)
    document.save(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    build_document(args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
