"""Generate reproducible Week 4 v2 PNG charts with Pillow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


NAVY = "#102A43"
BLUE = "#2F6B9A"
BLUE_DARK = "#1D4F73"
BLUE_LIGHT = "#D9EAF5"
GOLD = "#D5A021"
GOLD_LIGHT = "#F7E7B2"
LIGHT = "#F5F7FA"
GRID = "#D9E2EC"
MUTED = "#486581"
WHITE = "#FFFFFF"


def font(size: int, bold: bool = False):
    candidates = [
        (
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
            if bold
            else "/System/Library/Fonts/Supplemental/Arial.ttf"
        ),
        (
            "C:/Windows/Fonts/arialbd.ttf"
            if bold
            else "C:/Windows/Fonts/arial.ttf"
        ),
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, font_obj, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textbbox((0, 0), trial, font=font_obj)[2] <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _header(draw: ImageDraw.ImageDraw, width: int, title: str, subtitle: str) -> None:
    draw.rectangle((0, 0, width, 126), fill=NAVY)
    draw.text((70, 31), title, fill=WHITE, font=font(38, True))
    draw.text((70, 151), subtitle, fill=NAVY, font=font(27, True))


def _legend(draw: ImageDraw.ImageDraw, x: int, y: int, first: str, second: str) -> None:
    draw.rounded_rectangle((x, y, x + 28, y + 28), radius=5, fill=BLUE)
    draw.text((x + 42, y - 1), first, fill=NAVY, font=font(19))
    draw.rounded_rectangle((x + 260, y, x + 288, y + 28), radius=5, fill=GOLD)
    draw.text((x + 302, y - 1), second, fill=NAVY, font=font(19))


def _stacked_bar_chart(
    result: dict,
    output: Path,
    *,
    title: str,
    subtitle: str,
    positive_key: str,
    review_key: str,
    positive_legend: str,
    review_legend: str,
    value_format,
) -> None:
    width, height = 1800, 1320
    image = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(image)
    _header(draw, width, title, subtitle)
    _legend(draw, 1160, 153, positive_legend, review_legend)

    label_left = 70
    plot_left = 625
    plot_right = 1640
    plot_width = plot_right - plot_left
    row_top = 248
    row_height = 118
    totals = [
        float(row[positive_key]) + float(row[review_key]) for row in result["summary"]
    ]
    max_total = max(totals + [1.0])

    for index, row in enumerate(result["summary"]):
        center_y = row_top + index * row_height + 42
        label_lines = wrap(draw, row["category"], font(24, True), 500)
        label_y = center_y - (len(label_lines) * 28) // 2
        for line_index, line in enumerate(label_lines):
            draw.text(
                (label_left, label_y + line_index * 29),
                line,
                fill=NAVY,
                font=font(24, True),
            )

        bar_y = center_y - 25
        draw.rounded_rectangle(
            (plot_left, bar_y, plot_right, bar_y + 50), radius=10, fill=LIGHT
        )
        positive = float(row[positive_key])
        review = float(row[review_key])
        positive_width = int(plot_width * positive / max_total)
        review_width = int(plot_width * review / max_total)
        if positive_width:
            draw.rounded_rectangle(
                (plot_left, bar_y, plot_left + positive_width, bar_y + 50),
                radius=10,
                fill=BLUE,
            )
        if review_width:
            start = plot_left + positive_width
            draw.rectangle((start, bar_y, start + review_width, bar_y + 50), fill=GOLD)

        draw.text(
            (plot_right + 24, center_y - 17),
            f"{value_format(positive)} + {value_format(review)}",
            fill=NAVY,
            font=font(23, True),
        )
        draw.line(
            (label_left, row_top + (index + 1) * row_height - 18, 1730, row_top + (index + 1) * row_height - 18),
            fill=GRID,
            width=1,
        )

    footer_y = 1215
    draw.text(
        (70, footer_y),
        "Categories are not mutually exclusive. Review signals are reported separately from positive evidence.",
        fill=MUTED,
        font=font(20),
    )
    draw.text(
        (70, footer_y + 38),
        f"Source: official {result['unit_code']} {result['session']} unit outline.",
        fill=MUTED,
        font=font(18),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, quality=95)


def category_chart(result: dict, output: Path) -> None:
    _stacked_bar_chart(
        result,
        output,
        title="INFS6600 taxonomy pilot v2",
        subtitle="Distinct evidence items by category",
        positive_key="evidence_item_count",
        review_key="review_item_count",
        positive_legend="Positive evidence",
        review_legend="Review queue",
        value_format=lambda value: str(int(value)),
    )


def score_chart(result: dict, output: Path) -> None:
    _stacked_bar_chart(
        result,
        output,
        title="INFS6600 category score summary",
        subtitle="Classified score and separately retained review score",
        positive_key="classified_score_total",
        review_key="review_score_total",
        positive_legend="Classified score",
        review_legend="Review score",
        value_format=lambda value: f"{value:.1f}",
    )


def _heat_color(value: int, maximum: int) -> str:
    if value <= 0:
        return LIGHT
    ratio = value / max(maximum, 1)
    light = (217, 234, 245)
    dark = (47, 107, 154)
    rgb = tuple(int(light[i] + (dark[i] - light[i]) * ratio) for i in range(3))
    return "#%02X%02X%02X" % rgb


def section_chart(result: dict, output: Path) -> None:
    sections = ["overview", "learning_outcome", "assessment", "weekly_schedule"]
    labels = ["Overview", "Learning outcomes", "Assessments", "Weekly schedule"]
    width, height = 1800, 1280
    image = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(image)
    _header(
        draw,
        width,
        "Where positive evidence appears",
        f"{result['unit_code']} {result['session']} - distinct item counts",
    )

    label_left = 70
    grid_left = 655
    grid_top = 285
    cell_width = 245
    cell_height = 102
    maximum = max(
        [
            row["section_counts"].get(section, 0)
            for row in result["summary"]
            for section in sections
        ]
        + [1]
    )

    for column, label in enumerate(labels):
        text_width = draw.textbbox((0, 0), label, font=font(21, True))[2]
        draw.text(
            (grid_left + column * cell_width + (cell_width - text_width) / 2, 231),
            label,
            fill=NAVY,
            font=font(21, True),
        )

    for row_index, row in enumerate(result["summary"]):
        y = grid_top + row_index * cell_height
        label_lines = wrap(draw, row["category"], font(23, True), 520)
        label_y = y + (cell_height - len(label_lines) * 27) / 2
        for line_index, line in enumerate(label_lines):
            draw.text(
                (label_left, label_y + line_index * 27),
                line,
                fill=NAVY,
                font=font(23, True),
            )
        for column, section in enumerate(sections):
            x = grid_left + column * cell_width
            value = int(row["section_counts"].get(section, 0))
            fill = _heat_color(value, maximum)
            draw.rectangle(
                (x, y, x + cell_width - 10, y + cell_height - 10),
                fill=fill,
                outline=WHITE,
                width=3,
            )
            text_fill = WHITE if value / maximum >= 0.6 else NAVY
            text = str(value)
            box = draw.textbbox((0, 0), text, font=font(30, True))
            draw.text(
                (
                    x + (cell_width - 10 - (box[2] - box[0])) / 2,
                    y + (cell_height - 10 - (box[3] - box[1])) / 2 - 4,
                ),
                text,
                fill=text_fill,
                font=font(30, True),
            )

    footer_y = 1130
    draw.text(
        (70, footer_y),
        "Each cell counts distinct positive evidence items. Zero means no positive item was found in that section.",
        fill=MUTED,
        font=font(20),
    )
    draw.text(
        (70, footer_y + 38),
        "Categories are not mutually exclusive; the same outline item may appear once in more than one category.",
        fill=MUTED,
        font=font(20),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, quality=95)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(args.input.read_text(encoding="utf-8"))
    category_chart(result, args.output_dir / "category_summary.png")
    score_chart(result, args.output_dir / "category_scores.png")
    section_chart(result, args.output_dir / "evidence_by_section.png")
    print(f"Wrote visualisations to {args.output_dir}")


if __name__ == "__main__":
    main()
