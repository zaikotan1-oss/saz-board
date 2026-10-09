"""GitHub Pages 用に aim/ を組み立てる。
- aim/index.html … 感度くらべ（点の記録と平均）。手で書く本体。
- aim/guide.html … docs/aimingpro-sens/index.html（Artifact 用の断片）に骨組みを足した完全な HTML
- aim/img/        … 説明書の画像のコピー
公開先: https://zaikotan1-oss.github.io/saz-board/aim/
"""
import pathlib, shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "aimingpro-sens"
OUT = ROOT / "aim"
OUT.mkdir(exist_ok=True)

frag = (SRC / "index.html").read_text(encoding="utf-8")
doc = (
    "<!doctype html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"utf-8\">\n"
    "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
    "<meta name=\"description\" content=\"サドンアタック ZP の感度を Aiming.Pro に持ち込み、Hexakill の点で自分に合っているか確かめる手順（スクショ付き）\">\n"
    "<style>body{margin:0}img{max-width:100%;height:auto}</style>\n"
    "</head>\n<body>\n" + frag + "\n</body>\n</html>\n"
)
(OUT / "guide.html").write_text(doc, encoding="utf-8")

img_out = OUT / "img"
img_out.mkdir(exist_ok=True)
n = 0
for p in (SRC / "img").glob("*.jpg"):
    shutil.copy2(p, img_out / p.name)
    n += 1
print("guide.html", len(doc) // 1024, "KB;", n, "images")
