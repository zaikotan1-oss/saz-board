"""docs/aimingpro-sens/index.html を LINE で送れる PDF にする（Playwright の Chromium で印刷）。
出力: docs/aimingpro-sens/サドン感度_AimingPro確認手順.pdf
"""
import pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent.parent / "docs" / "aimingpro-sens"
SRC = HERE / "index.html"
OUT = HERE / "サドン感度_AimingPro確認手順.pdf"

# 公開用の index.html は <title> から始まる断片なので、印刷用に骨組みを足す
html = SRC.read_text(encoding="utf-8")
doc = (
    "<!doctype html><html lang=\"ja\"><head><meta charset=\"utf-8\">"
    "<style>"
    "body{margin:0;font-size:14px}"
    ".wrap{max-width:none}"
    "figure,table,.goal,.two>div,.step{break-inside:avoid}"
    "h2,h3,h4{break-after:avoid;break-inside:avoid}"
    ".jump{display:none}"
    ".log input{border:1px solid #999;background:#fff}"
    "</style>"
    "</head><body>" + html + "</body></html>"
)
tmp = HERE / "_print.html"
tmp.write_text(doc, encoding="utf-8")

with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page()
    pg.emulate_media(media="print", color_scheme="light")
    pg.goto(tmp.as_uri(), wait_until="networkidle")
    pg.wait_for_timeout(1500)  # Google Fonts の読み込み待ち
    pg.pdf(
        path=str(OUT),
        format="A4",
        print_background=True,
        margin={"top": "14mm", "bottom": "14mm", "left": "12mm", "right": "12mm"},
    )
    br.close()
tmp.unlink()
print(OUT, OUT.stat().st_size // 1024, "KB")
