# -*- coding: utf-8 -*-
"""編集画面（editor.html）の保存先。POST /save?map=<id> の本文(JSON)を data/timemap/edits/<id>.json に書く。
起動: python tools/save_server.py   （ポート 8843・CORS 許可）"""
import json, os, io, sys
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'timemap', 'edits'); os.makedirs(OUT, exist_ok=True)
class H(BaseHTTPRequestHandler):
    def _h(self, code=200):
        self.send_response(code); self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Access-Control-Allow-Headers', '*'); self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS'); self.send_header('Content-Type', 'application/json; charset=utf-8'); self.end_headers()
    def do_OPTIONS(self): self._h()
    def do_GET(self):
        m = self.path.split('map=')[-1].split('&')[0] if 'map=' in self.path else ''
        p = os.path.join(OUT, m + '.json')
        if m and os.path.exists(p): self._h(); self.wfile.write(open(p, 'rb').read())
        else: self._h(404); self.wfile.write(b'{}')
    def do_POST(self):
        m = self.path.split('map=')[-1].split('&')[0]
        body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        data = json.loads(body); json.dump(data, open(os.path.join(OUT, m + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('saved', m, len(data.get('edges', [])), 'edges'); self._h(); self.wfile.write(b'{"ok":true}')
    def log_message(self, *a): pass
print('save server on 8843'); ThreadingHTTPServer(('127.0.0.1', 8843), H).serve_forever()
