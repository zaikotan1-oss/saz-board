# -*- coding: utf-8 -*-
"""編集画面（editor.html）と掲示板（board.html）の手元の保存先。ポート 8843・CORS 許可。
  POST /save?map=<id>   本文(JSON) → data/timemap/edits/<id>.json
  GET  /load?map=<id>   → その JSON
  GET  /ping            → {"ok":true}（掲示板が「手元のサーバーがいる」と判断する）
  GET  /kv?col=<名前>   → data/board/<名前>.json の配列
  POST /kv?col=<名前>   本文(JSON 1件) を配列に追加（id は本文の物）
  DELETE /kv?col=<名前>&id=<id>&dev=<端末>  その端末が書いた物だけ消す
起動: python tools/save_server.py"""
import json, os, io, sys, re, threading
from urllib.parse import urlparse, parse_qs
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'timemap', 'edits'); os.makedirs(OUT, exist_ok=True)
BOARD = os.path.join(ROOT, 'data', 'board'); os.makedirs(BOARD, exist_ok=True)
LOCK = threading.Lock()
SAFE = re.compile(r'^[A-Za-z0-9_\-]{1,40}$')
def col_path(col): return os.path.join(BOARD, col + '.json') if SAFE.match(col or '') else None
def read_col(col):
    p = col_path(col)
    if p and os.path.exists(p):
        try: return json.load(open(p, encoding='utf-8'))
        except Exception: return []
    return []
def write_col(col, items): json.dump(items, open(col_path(col), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
class H(BaseHTTPRequestHandler):
    def _h(self, code=200):
        self.send_response(code); self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Access-Control-Allow-Headers', '*'); self.send_header('Access-Control-Allow-Methods', 'POST, GET, DELETE, OPTIONS'); self.send_header('Content-Type', 'application/json; charset=utf-8'); self.send_header('Cache-Control', 'no-store'); self.end_headers()
    def _json(self, obj, code=200): self._h(code); self.wfile.write(json.dumps(obj, ensure_ascii=False).encode('utf-8'))
    def q(self): u = urlparse(self.path); return u.path, {k: v[0] for k, v in parse_qs(u.query).items()}
    def do_OPTIONS(self): self._h()
    def do_GET(self):
        path, q = self.q()
        if path == '/ping': return self._json({'ok': True})
        if path == '/kv': return self._json(read_col(q.get('col', '')))
        m = q.get('map', ''); p = os.path.join(OUT, m + '.json')
        if m and SAFE.match(m) and os.path.exists(p): self._h(); self.wfile.write(open(p, 'rb').read())
        else: self._json({}, 404)
    def do_POST(self):
        path, q = self.q()
        body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        data = json.loads(body or b'{}')
        if path == '/kv':
            col = q.get('col', '')
            if not col_path(col): return self._json({'error': 'bad col'}, 400)
            with LOCK:
                items = read_col(col); items.append(data); write_col(col, items)
            print('board', col, '+1 →', len(items)); return self._json({'ok': True, 'id': data.get('id')})
        m = q.get('map', '')
        if not SAFE.match(m): return self._json({'error': 'bad map'}, 400)
        json.dump(data, open(os.path.join(OUT, m + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('saved', m, len(data.get('edges', [])), 'edges'); self._json({'ok': True})
    def do_DELETE(self):
        path, q = self.q()
        if path != '/kv': return self._json({}, 404)
        col, pid, dev = q.get('col', ''), q.get('id', ''), q.get('dev', '')
        if not col_path(col): return self._json({'error': 'bad col'}, 400)
        with LOCK:
            items = read_col(col); keep = [x for x in items if not (x.get('id') == pid and x.get('dev') == dev)]
            write_col(col, keep)
        print('board', col, 'del', pid, len(items) - len(keep)); self._json({'ok': True, 'removed': len(items) - len(keep)})
    def log_message(self, *a): pass
print('save server on 8843'); ThreadingHTTPServer(('127.0.0.1', 8843), H).serve_forever()
