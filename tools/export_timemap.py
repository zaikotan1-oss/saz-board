# -*- coding: utf-8 -*-
"""移動時間（editor.html）を マップ×武器 ごとに PNG にする → data/timemap/png/　※点が無いマップは飛ばす
使い方: python tools/export_timemap.py [map_id]"""
import base64, json, os, sys, threading, io
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT = 8842
only = sys.argv[1] if len(sys.argv) > 1 else None
class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def log_message(self, *a): pass
srv = ThreadingHTTPServer(('127.0.0.1', PORT), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
from playwright.sync_api import sync_playwright
idx = json.load(open(os.path.join(ROOT, 'data', 'timemap', 'index.json'), encoding='utf-8'))
out = os.path.join(ROOT, 'data', 'timemap', 'png'); os.makedirs(out, exist_ok=True)
with sync_playwright() as pw:
    br = pw.chromium.launch(); pg = br.new_page(viewport={'width': 1500, 'height': 900})
    for m in idx['maps']:
        if only and m['map'] != only: continue
        if not os.path.exists(os.path.join(ROOT, 'data', 'timemap', 'edits', m['map'] + '.json')): continue
        for w in idx['weapons']:
            pg.goto(f"http://127.0.0.1:{PORT}/editor.html?map={m['map']}&weapon={w['id']}")
            pg.wait_for_function('window.__ed && window.__ed.ready'); pg.wait_for_timeout(400)
            data = pg.evaluate('window.__ed.exportDataURL(2)')
            name = f"{m['map']}_{w['id']}_{m['name']}_{w['label'].replace('/', '／').replace(' ', '')}.png"
            open(os.path.join(out, name), 'wb').write(base64.b64decode(data.split(',', 1)[1])); print('wrote', name)
    br.close()
srv.shutdown()
