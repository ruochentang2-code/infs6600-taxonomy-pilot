"""Generate dependency-light PNG charts with Pillow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


NAVY = "#102A43"
BLUE = "#2F6B9A"
TEAL = "#2A9D8F"
GOLD = "#E9C46A"
LIGHT = "#F5F7FA"
GRID = "#D9E2EC"


def font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, font_obj, width: int) -> list[str]:
    words = text.split()
    lines, current = [], ""
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


def category_chart(result: dict, output: Path) -> None:
    image = Image.new("RGB", (1400, 820), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1400, 110), fill=NAVY)
    draw.text((70, 35), "INFS6600 taxonomy pilot", fill="white", font=font(38, True))
    draw.text((70, 135), "Classified evidence items by category", fill=NAVY, font=font(30, True))
    max_count = max([row["evidence_item_count"] for row in result["summary"]] + [1])
    colors = [TEAL, BLUE]
    y_positions = [285, 535]
    for index, row in enumerate(result["summary"]):
        y = y_positions[index]
        label_lines = wrap(draw, row["category"], font(25, True), 420)
        for line_index, line in enumerate(label_lines):
            draw.text((70, y - 55 + line_index * 31), line, fill=NAVY, font=font(25, True))
        bar_x, bar_y, bar_w, bar_h = 515, y - 38, 700, 76
        draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=18, fill=LIGHT)
        filled = int(bar_w * row["evidence_item_count"] / max_count)
        draw.rounded_rectangle((bar_x, bar_y, bar_x + filled, bar_y + bar_h), radius=18, fill=colors[index])
        draw.text((1245, y - 29), str(row["evidence_item_count"]), fill=NAVY, font=font(38, True))
    draw.text((70, 735), "Count = distinct auditable outline items above the category threshold.", fill="#486581", font=font(22))
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def section_chart(result: dict, output: Path) -> None:
    sections = ["overview", "learning_outcome", "assessment", "weekly_schedule"]
    labels = ["Overview", "Learning outcomes", "Assessments", "Weekly schedule"]
    image = Image.new("RGB", (1500, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1500, 110), fill=NAVY)
    draw.text((70, 35), "Where the evidence appears", fill="white", font=font(38, True))
    draw.text((70, 145), "INFS6600 Semester 2, 2026", fill=NAVY, font=font(28, True))
    plot_left, plot_top, plot_bottom, max_h = 170, 260, 760, 440
    max_count = max(
        [row["section_counts"].get(section, 0) for row in result["summary"] for section in sections] + [1]
    )
    for tick in range(max_count + 1):
        y = plot_bottom - int(max_h * tick / max_count)
        draw.line((plot_left, y, 1400, y), fill=GRID, width=2)
        draw.text((125, y - 12), str(tick), fill="#486581", font=font(18))
    colors = [TEAL, BLUE]
    group_width = 280
    for section_index, section in enumerate(sections):
        group_x = plot_left + 70 + section_index * group_width
        for category_index, row in enumerate(result["summary"]):
            count = row["section_counts"].get(section, 0)
            height = int(max_h * count / max_count)
            x = group_x + category_index * 80
            draw.rounded_rectangle((x, plot_bottom - height, x + 58, plot_bottom), radius=8, fill=colors[category_index])
            draw.text((x + 18, plot_bottom - height - 32), str(count), fill=NAVY, font=font(20, True))
        draw.text((group_x - 25, 790), labels[section_index], fill=NAVY, font=font(19, True))
    draw.rectangle((1040, 150, 1070, 180), fill=TEAL)
    draw.text((1085, 152), "Work-Integrated & Applied", fill=NAVY, font=font(20))
    draw.rectangle((1040, 195, 1070, 225), fill=BLUE)
    draw.text((1085, 197), "Simulation & Case-Based", fill=NAVY, font=font(20))
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(args.input.read_text(encoding="utf-8"))
    category_chart(result, args.output_dir / "category_summary.png")
    section_chart(result, args.output_dir / "evidence_by_section.png")
    print(f"Wrote visualisations to {args.output_dir}")


if __name__ == "__main__":
    main()

