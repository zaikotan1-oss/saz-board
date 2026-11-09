"""LINE のトーク履歴（.txt / .zip）をスマホから受け取る受け口（8870）。
この PC・家の中・Tailscale からだけ。届いた物は context/line/inbox/ に日時付きで置く。
  python tools/line_inbox.py
"""
import cgi, datetime, html, pathlib, re, sys
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
HERE = pathlib.Path(__file__).resolve().parent.parent
INBOX = HERE / 'context' / 'line' / 'inbox'; INBOX.mkdir(parents=True, exist_ok=True)
PORT = 8870
OK_IP = re.compile(r'^(127\.|192\.168\.|10\.|100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.)')
PAGE = """<!DOCTYPE html><html lang=ja><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>LINE の履歴を渡す</title><style>body{font-family:sans-serif;background:#1b1d22;color:#e8e8ec;margin:0;padding:20px;font-size:16px;line-height:1.7}
h1{color:#f2b705;font-size:18px}input,button{font-size:16px}button{background:#2a7a3a;color:#fff;border:0;border-radius:10px;padding:14px 20px;font-weight:bold;width:100%%;margin-top:14px}
.box{background:#262930;border:1px solid #3a3e48;border-radius:12px;padding:14px;margin:12px 0}.ok{color:#2fd17a;font-weight:bold}ol{padding-left:22px}</style>
<h1>LINE のトーク履歴を渡す</h1>%s
<div class=box><ol><li>LINE のトーク画面 右上 ≡ → <b>その他</b> → <b>トーク履歴を送信</b></li><li>出てきた共有の画面で <b>「ファイルに保存」</b>（iPhone）／「デバイスに保存」（Android）</li><li>下の「ファイルを選ぶ」でその .txt（.zip でも可）を選んで「送る」</li></ol>
<form method=post action=/up enctype=multipart/form-data><input type=file name=f multiple><button>送る</button></form></div>
<div class=box>これまで届いた物:<br>%s</div>"""
class H(BaseHTTPRequestHandler):
    def parse_request(self):
        ok = super().parse_request()
        if ok and not OK_IP.match(self.client_address[0]): self.send_error(403); return False
        return ok
    def _page(self, note=''):
        got = '<br>'.join(f'{p.name}（{p.stat().st_size // 1024} KB）' for p in sorted(INBOX.iterdir()) if p.is_file()) or 'まだ無し'
        b = (PAGE % (note, got)).encode('utf-8'); self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path.startswith('/ping'): self.send_response(200); self.end_headers(); self.wfile.write(b'ok'); return
        self._page()
    def do_POST(self):
        if not self.path.startswith('/up'): self.send_error(404); return
        fs = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers.get('Content-Type', '')})
        items = fs['f'] if 'f' in fs else []
        if not isinstance(items, list): items = [items]
        saved = []
        for it in items:
            if not getattr(it, 'filename', None): continue
            name = re.sub(r'[\/:*?"<>|]+', '_', pathlib.Path(it.filename).name)
            out = INBOX / f"{datetime.datetime.now():%Y%m%d_%H%M%S}_{name}"; out.write_bytes(it.file.read()); saved.append(out)
            print('saved', out, out.stat().st_size, flush=True)
        self._page(f'<div class=box><span class=ok>届きました ✔</span> {html.escape("・".join(p.name for p in saved)) or "（ファイルが選ばれていません）"}<br>Claude に「送った」と言ってください。</div>')
    def log_message(self, *a): pass
if __name__ == '__main__':
    ThreadingHTTPServer.allow_reuse_address = False
    print('line_inbox on', PORT, flush=True); ThreadingHTTPServer(('0.0.0.0', PORT), H).serve_forever()
