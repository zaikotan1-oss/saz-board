"""maps.json の地名（callouts）を Firebase の places に 1 回だけ写す（作戦ノートで地名をみんなで直せるようにするため）。
既に places にそのマップの地名があるマップは飛ばす。"""
import json, re, time, urllib.request, pathlib
HERE = pathlib.Path(__file__).resolve().parent.parent
url = re.findall(r"firebase:\s*'([^']+)'", (HERE / 'board-config.js').read_text(encoding='utf-8'))[-1].rstrip('/')  # 最後の（コメントでない）URL
maps = json.loads((HERE / 'maps' / 'maps.json').read_text(encoding='utf-8'))['maps']
cur = json.loads(urllib.request.urlopen(f'{url}/saz/places.json').read() or b'null') or {}
have = {v.get('map') for v in cur.values()}
for m in maps:
    if m['id'] in have or not m.get('callouts'): print('skip', m['id']); continue
    for i, (name, x, y) in enumerate(m['callouts']):
        body = json.dumps({'text': name, 'map': m['id'], 'x': x, 'y': y, 't': int(time.time() * 1000) + i, 'dev': 'seed'}).encode()
        req = urllib.request.Request(f'{url}/saz/places.json', data=body, method='POST', headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req).read()
    print('seeded', m['id'], len(m['callouts']))
