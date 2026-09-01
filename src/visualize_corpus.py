"""Create discipline-wide and UG-versus-PG charts for the CS-44 corpus."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def get_font(size: int, bold: bool = False):
    paths = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf", "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"]
    for path in paths:
        try: return ImageFont.truetype(path, size)
        except OSError: pass
    return ImageFont.load_default()

def short(name: str) -> str:
    return name.replace("Work-Integrated and Applied Learning", "Work-Integrated / Applied").replace("Simulation and Case-Based Learning", "Simulation / Case-Based").replace("Project- and Problem-Based Learning", "Project / Problem-Based").replace("Technology-Mediated Learning", "Technology-Mediated")

def draw_chart(rows, output: Path, metric: str, title: str) -> None:
    image=Image.new("RGB",(1700,1050),"white"); draw=ImageDraw.Draw(image); draw.rectangle((0,0,1700,115),fill="#102A43"); draw.text((65,34),title,fill="white",font=get_font(36,True))
    maximum=max([row[metric] for row in rows]+[1]); left,top,bar_h,gap=550,185,74,48
    for i,row in enumerate(rows):
        y=top+i*(bar_h+gap); draw.text((60,y+17),short(row["category"]),fill="#102A43",font=get_font(24,True)); draw.rounded_rectangle((left,y,1570,y+bar_h),radius=14,fill="#EDF2F7"); filled=int(1020*row[metric]/maximum)
        if filled: draw.rounded_rectangle((left,y,left+filled,y+bar_h),radius=14,fill="#2A9D8F")
        draw.text((1590,y+14),str(row[metric]),fill="#102A43",font=get_font(30,True))
    output.parent.mkdir(parents=True,exist_ok=True); image.save(output)

def draw_comparison(rows, output: Path) -> None:
    image=Image.new("RGB",(1800,1120),"white"); draw=ImageDraw.Draw(image); draw.rectangle((0,0,1800,115),fill="#102A43"); draw.text((65,34),"Units with evidence: UG compared with PG",fill="white",font=get_font(36,True))
    maximum=max([max(r["ug_units_with_evidence"],r["pg_units_with_evidence"]) for r in rows]+[1]); left,top,row_gap=590,175,132
    for i,row in enumerate(rows):
        y=top+i*row_gap; draw.text((55,y+30),short(row["category"]),fill="#102A43",font=get_font(23,True))
        for j,(key,color) in enumerate((("ug_units_with_evidence","#2A9D8F"),("pg_units_with_evidence","#2F6B9A"))):
            yy=y+j*45; value=row[key]; filled=int(1030*value/maximum); draw.rounded_rectangle((left,yy,1620,yy+34),radius=8,fill="#EDF2F7")
            if filled: draw.rounded_rectangle((left,yy,left+filled,yy+34),radius=8,fill=color)
            draw.text((1640,yy+2),str(value),fill="#102A43",font=get_font(23,True))
    draw.rectangle((1260,130,1290,158),fill="#2A9D8F"); draw.text((1300,130),"UG (12 units)",fill="#102A43",font=get_font(20)); draw.rectangle((1470,130,1500,158),fill="#2F6B9A"); draw.text((1510,130),"PG (15 units)",fill="#102A43",font=get_font(20))
    output.parent.mkdir(parents=True,exist_ok=True); image.save(output)

def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--input",type=Path,required=True); p.add_argument("--output-dir",type=Path,required=True); a=p.parse_args(); rows=json.loads(a.input.read_text(encoding="utf-8"))["aggregate"]
    draw_chart(rows,a.output_dir/"discipline_category_units.png","all_units_with_evidence","Pedagogical innovation across the INFS discipline"); draw_comparison(rows,a.output_dir/"ug_pg_comparison.png")
if __name__=="__main__": main()
