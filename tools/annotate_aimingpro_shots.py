"""Aiming.Pro の操作スクショに「ここを押す」の赤い印（角丸の枠＋番号）を付けて docs/aimingpro-sens/img/ に置く。
元画像は Claude のツール結果（撮影日 2026-10-08）。座標は撮影時の画面（1568x698、トップページだけ 800x609）での実測。
"""
import pathlib
from PIL import Image, ImageDraw, ImageFont

TR = pathlib.Path(r"C:\Users\zaiko\.claude\projects\C--Users-zaiko\57c37557-dea2-40b8-ac41-5b0ee607da45\tool-results")
OUT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "aimingpro-sens" / "img"
OUT.mkdir(parents=True, exist_ok=True)

RED = (230, 40, 40)
try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 34)
except Exception:
    FONT = ImageFont.load_default()

def mark(draw, box, label=None, width=5, at=None):
    """at: 番号を置く中心座標。省略すると枠の左上"""
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=10, outline=RED, width=width)
    if label:
        r = 22
        cx, cy = at if at else (x0 - 6, y0 - 6)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=RED)
        tw = draw.textlength(label, font=FONT)
        draw.text((cx - tw / 2, cy - 21), label, fill=(255, 255, 255), font=FONT)

# (出力名, 元ファイル, [(box, label), ...])
JOBS = [
    ("10_top.jpg", "mcp-Claude_Browser-blob-1791470197614-aenvw8.jpg",
     [((30, 362, 200, 410), "1")]),
    ("11_play.jpg", "mcp-claude-in-chrome-blob-1791470191549-ci3ako.jpg",
     [((276, 188, 1076, 600), "2")]),
    ("12_benchmarks.jpg", "mcp-claude-in-chrome-blob-1791470219527-inthkm.jpg",
     [((286, 258, 440, 290), "3"), ((700, 236, 780, 262), None)]),
    ("13_loading.jpg", "mcp-claude-in-chrome-blob-1791470258155-l6nb3s.jpg", []),
    ("14_fire.jpg", "mcp-claude-in-chrome-blob-1791470258155-iyym2y.jpg",
     [((690, 370, 880, 412), "4"), ((1462, 644, 1548, 672), "5")]),
    ("15_paused.jpg", "mcp-claude-in-chrome-blob-1791470272293-on9gvk.jpg",
     [((660, 432, 908, 474), "6")]),
    ("16_settings.jpg", "mcp-claude-in-chrome-blob-1791470285833-65n4jg.jpg",
     [((294, 148, 480, 198), "7"), ((328, 236, 380, 262), "8"), ((540, 392, 584, 418), "9")]),
    ("17_values.jpg", "mcp-claude-in-chrome-blob-1791467864522-9p021r.jpg",
     [((683, 312, 812, 342), "10", (842, 327)), ((683, 350, 776, 380), "11", (735, 404)), ((779, 348, 814, 384), "12", (842, 366)), ((294, 574, 390, 618), "13")]),
    ("18_resume.jpg", "mcp-claude-in-chrome-blob-1791470272293-on9gvk.jpg",
     [((660, 340, 908, 382), "14")]),
    ("19_score.jpg", "mcp-claude-in-chrome-blob-1791470219527-inthkm.jpg",
     [((700, 236, 780, 262), "15")]),
]

for name, src, marks in JOBS:
    im = Image.open(TR / src).convert("RGB")
    d = ImageDraw.Draw(im)
    for m in marks:
        box, label = m[0], m[1]
        mark(d, box, label, at=(m[2] if len(m) > 2 else None))
    im.save(OUT / name, quality=88)
    print(name, im.size)
