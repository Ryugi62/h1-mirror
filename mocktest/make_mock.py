"""Mock H1-register rows for the Round-1 reading test (synthetic; no real patient or prescriber).
Each row: date | patient (masked on the phone, drawn as a black bar) | prescriber + registration no. | drug line | quantity.
Handwriting-style fonts + jitter, tilt, blur, noise, JPEG. Ground truth is written OUTSIDE the image folder so the
reader model never sees it.  Usage: python3 make_mock.py <truth_json_path>"""
import json
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "imgs")
FONTS = ["/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf", "/System/Library/Fonts/Noteworthy.ttc",
         "/System/Library/Fonts/Supplemental/ChalkboardSE.ttc", "/System/Library/Fonts/MarkerFelt.ttc",
         "/System/Library/Fonts/Supplemental/SnellRoundhand.ttc"]
DRUGS = ["Cefixime 200 mg", "Taxim-O 200", "Clavam 625", "Amoxycillin 500 mg", "Azithromycin 500 mg",
         "Cefixime 200 + Ofloxacin 200", "Ofloxacin 200 + Ornidazole 500", "Cefpodoxime 200 mg", "Wymox 500",
         "Linezolid 600 mg", "Doxycycline 100 mg", "Ciprofloxacin 500 mg", "Monocef-O 200", "Levofloxacin 500 mg",
         "Cefuroxime 500 mg", "Amoxycillin 500 + Clavulanate 125"]
NAMES = ["Das", "Sen", "Roy", "Nair", "Menon", "Pillai", "Ghosh", "Banerjee", "Kurian", "Iyer", "Rao", "Varghese"]
QTY = ["10 tab", "6 tab", "5 cap", "3 tab", "14 cap", "1 strip", "15 cap", "7 tab"]
COUNCIL = ["WBMC", "TCMC"]


def jitter_text(draw, xy, text, font, rng):
    x, y = xy
    for ch in text:
        dy = rng.uniform(-2.5, 2.5)
        draw.text((x, y + dy), ch, font=font, fill=(20 + rng.randint(0, 40), 30, 90 + rng.randint(0, 60)))
        x += draw.textlength(ch, font=font) * rng.uniform(0.96, 1.06)


def make(n=40, seed=20260926):
    rng = random.Random(seed)
    os.makedirs(IMG, exist_ok=True)
    truth = []
    for i in range(n):
        font_path = FONTS[i % len(FONTS)]
        font = ImageFont.truetype(font_path, rng.randint(34, 40))
        small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 18)
        row = {"id": f"mock-{i + 1:02d}", "font": os.path.basename(font_path),
               "date": f"{rng.randint(1, 28):02d}/{rng.choice([8, 9]):02d}/26",
               "prescriber_name": "Dr. " + rng.choice(NAMES),
               "reg_no": f"{rng.choice(COUNCIL)} {rng.randint(10000, 99999)}",
               "drug_line": DRUGS[i % len(DRUGS)] if i < len(DRUGS) else rng.choice(DRUGS),
               "qty": rng.choice(QTY)}
        W, H = 1500, 190
        im = Image.new("RGB", (W, H), (246, 243, 232))
        d = ImageDraw.Draw(im)
        cols = [0, 150, 420, 820, 1330, W]
        heads = ["Date", "Patient (masked)", "Prescriber / Reg. No.", "Drug & strength", "Qty"]
        for c, h in zip(cols, heads):
            d.line([(c, 0), (c, H)], fill=(150, 150, 170), width=2)
            d.text((c + 8, 6), h, font=small, fill=(90, 90, 110))
        d.line([(0, 34), (W, 34)], fill=(150, 150, 170), width=2)
        d.rectangle([cols[1] + 12, 70, cols[2] - 12, 150], fill=(0, 0, 0))            # on-phone mask
        jitter_text(d, (cols[0] + 8, 80), row["date"], ImageFont.truetype(font_path, 30), rng)
        jitter_text(d, (cols[2] + 10, 50), row["prescriber_name"], font, rng)
        jitter_text(d, (cols[2] + 10, 110), row["reg_no"], font, rng)
        jitter_text(d, (cols[3] + 10, 80), row["drug_line"], font, rng)
        jitter_text(d, (cols[4] + 10, 80), row["qty"], ImageFont.truetype(font_path, 32), rng)
        im = im.transform(im.size, Image.AFFINE, (1, rng.uniform(-0.08, 0.08), 0, 0, 1, 0), fillcolor=(246, 243, 232))
        im = im.rotate(rng.uniform(-2.5, 2.5), expand=False, fillcolor=(246, 243, 232))
        im = im.filter(ImageFilter.GaussianBlur(rng.uniform(0.5, 1.2)))
        px = im.load()
        for _ in range(2500):
            x, y = rng.randrange(W), rng.randrange(H)
            v = rng.randint(-40, 40)
            r, g, b = px[x, y]
            px[x, y] = (max(0, min(255, r + v)), max(0, min(255, g + v)), max(0, min(255, b + v)))
        im.save(os.path.join(IMG, row["id"] + ".jpg"), quality=55)
        truth.append(row)
    return truth


if __name__ == "__main__":
    t = make()
    json.dump(t, open(sys.argv[1], "w"), indent=1)
    print(len(t), "rows")
