# -*- coding: utf-8 -*-
"""patterns/index.json にある見本パターンを全部 PNG にして patterns/png/ に書く。
ボードの HTML をヘッドレスの Chromium で開き、__board.exportDataURL() を呼ぶだけ（描画は本物と同じ）。
使い方:  python tools/export_png.py            … 全部
         python tools/export_png.py supply3    … そのマップだけ
"""
import base64, json, os, sys, threading, io
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8841
only = sys.argv[1] if len(sys.argv) > 1 else None

class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def log_message(self, *a): pass
srv = ThreadingHTTPServer(('127.0.0.1', PORT), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()

from playwright.sync_api import sync_playwright
index = json.load(open(os.path.join(ROOT, 'patterns', 'index.json'), encoding='utf-8'))
out = os.path.join(ROOT, 'patterns', 'png'); os.makedirs(out, exist_ok=True)
with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page(viewport={'width': 1400, 'height': 900})
    for it in index:
        if only and it['map'] != only: continue
        pg.goto(f'http://127.0.0.1:{PORT}/index.html?pattern={it["file"]}&export=1')
        pg.wait_for_function('window.__board && window.__board.ready && window.__board.pat.pieces.length > 0')
        pg.wait_for_timeout(300)
        data = pg.evaluate('window.__board.exportDataURL(2)')
        name = os.path.splitext(os.path.basename(it['file']))[0] + '_' + it['title'].replace('/', '／') + '.png'
        with open(os.path.join(out, name), 'wb') as f: f.write(base64.b64decode(data.split(',', 1)[1]))
        print('wrote', name)
    br.close()
srv.shutdown()
