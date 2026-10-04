# -*- coding: utf-8 -*-
"""地点どうしの移動時間を計算して data/timemap/<map>.json に書く。
- 地図ごとに「地点（ノード）」と「通路（エッジ、折れ線）」を地名で定義
- 縮尺: 第3補給倉庫は実測（Bテラス→階段 ＝ ナイフ 8.97 秒）。他のマップは同じ px/秒 を仮に使う（未校正）
- 速さ: ナイフ基準の倍率（実測 2026-10-04）
使い方: python tools/timemap_build.py
"""
import json, os, math, heapq, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = json.load(open(os.path.join(ROOT, 'maps', 'maps.json'), encoding='utf-8'))
MAPS = {m['id']: m for m in DB['maps']}

# 時間の倍率（ナイフ走り = 1.00）。実測秒 ÷ ナイフ秒
WEAPONS = [
    {'id': 'knife', 'label': 'ナイフ', 'factor': 1.0},
    {'id': 'p90', 'label': 'P90', 'factor': 9.07 / 8.97},
    {'id': 'scar', 'label': 'SCAR / AK-47', 'factor': 9.44 / 8.97},
    {'id': 'm249', 'label': 'M249', 'factor': 12.15 / 8.97},
    {'id': 'walk', 'label': '歩き(Shift)', 'factor': 13.47 / 8.97},
]
KNIFE_SEC = 8.97

def C(m, name):
    for n, x, y in MAPS[m]['callouts']:
        if n == name or n.startswith(name): return (x, y)
    raise KeyError(f'{m}: {name}')

def build(map_id, nodes, edges, attack, defend, calib=None, sites=None):
    """nodes: {表示名: 地名 or (x,y)}, edges: [(a, b, [中継地名...])], attack/defend: 表示名リスト
    calib: (a, b, 秒) 実測。None なら第3補給倉庫の px/秒 を流用"""
    pos = {}
    for k, v in nodes.items(): pos[k] = C(map_id, v) if isinstance(v, str) else tuple(v)
    def plen(pts): return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    E = []
    for a, b, via in edges:
        pts = [pos[a]] + [C(map_id, v) if isinstance(v, str) else tuple(v) for v in via] + [pos[b]]
        E.append({'a': a, 'b': b, 'pts': pts, 'px': round(plen(pts), 1)})
    return {'map': map_id, 'nodes': pos, 'edges': E, 'attack': attack, 'defend': defend, 'calib': calib}

def dijkstra(G, src):
    adj = {}
    for e in G['edges']:
        adj.setdefault(e['a'], []).append((e['b'], e['px'])); adj.setdefault(e['b'], []).append((e['a'], e['px']))
    dist = {src: 0}; prev = {}; pq = [(0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18): continue
        for v, w in adj.get(u, []):
            nd = d + w
            if nd < dist.get(v, 1e18): dist[v] = nd; prev[v] = u; heapq.heappush(pq, (nd, v))
    return dist, prev

GRAPHS = []

# ---------------- 第3補給倉庫（実測で校正） ----------------
GRAPHS.append(build('supply3',
    nodes={'赤リスポ': '赤リスポ', 'テロ部屋': 'テロ部屋', 'Aロング出口': 'テラス', 'Aサイト': 'Aポイント', 'ショート': 'ショート',
           'センター': 'センター', 'CT階段': 'CT階段', '青リスポ': (640, 520), 'Bテラス': 'Bテラス', 'Bロング(タワー)': 'タワー上下',
           '階段(B段差)': '階段', 'Bサイト': 'Bポイント', 'キャット': 'キャット', 'イナバ': 'イナバ', '1柱': '1柱', 'スナポジ': 'スナポジ'},
    edges=[('赤リスポ', 'テロ部屋', ['シリンダー']), ('テロ部屋', 'Aロング出口', ['Aロング']), ('Aロング出口', 'Aサイト', ['3ドラム', '2ドラム']),
           ('Aサイト', 'スナポジ', []), ('テロ部屋', 'ショート', []), ('ショート', 'センター', []), ('センター', 'CT階段', []),
           ('CT階段', '青リスポ', []), ('青リスポ', 'Aサイト', ['1ドラム']), ('センター', 'キャット', ['S字']), ('キャット', 'イナバ', []),
           ('イナバ', '1柱', []), ('1柱', 'Bサイト', []), ('赤リスポ', 'Bテラス', []), ('Bテラス', 'Bロング(タワー)', ['Bロング']),
           ('Bロング(タワー)', '階段(B段差)', []), ('階段(B段差)', 'Bサイト', []), ('階段(B段差)', 'キャット', ['小部屋']),
           ('CT階段', '1柱', ['4柱', '3柱', '2柱'])],
    attack=['Aロング出口', 'ショート', 'センター', 'Bロング(タワー)', '階段(B段差)', 'イナバ'],
    defend=['Aサイト', 'スナポジ', 'CT階段', '1柱', 'Bサイト'],
    calib={'start': [215, 112], 'goal': [180, 367], 'sec': KNIFE_SEC, 'note': '本人が calib.html で指定（2026-10-04）Bロング 攻め側の壁→B側の段差'}))

# ---------------- プロバンス（未校正） ----------------
GRAPHS.append(build('provence',
    nodes={'赤リスポ': '赤リスポ', 'A部屋': 'A部屋', 'Aロング出口': '三角', 'Aサイト': 'Aポイント', 'ダブルドア': 'ダブルドア', '青リスポ': '青リスポ',
           'A連通': 'A連通', 'センター': 'センター', 'S字': 'S字', 'B連通': 'B連通', 'Bサイト': 'Bポイント', 'Bロング出口': 'Bロング',
           'シリンダー': 'シリンダー', '裏道': '裏道'},
    edges=[('赤リスポ', 'A部屋', []), ('A部屋', 'Aロング出口', ['Aロング']), ('Aロング出口', 'Aサイト', []), ('Aサイト', 'ダブルドア', ['発電機']),
           ('ダブルドア', '青リスポ', []), ('ダブルドア', 'A連通', []), ('赤リスポ', 'センター', []), ('センター', 'A連通', []),
           ('センター', 'S字', []), ('S字', 'Bサイト', []), ('Bサイト', 'B連通', []), ('B連通', '青リスポ', []),
           ('赤リスポ', '裏道', []), ('裏道', 'シリンダー', []), ('シリンダー', 'Bロング出口', []), ('Bロング出口', 'Bサイト', ['1箱'])],
    attack=['Aロング出口', 'A連通', 'センター', 'S字', 'Bロング出口'],
    defend=['Aサイト', 'ダブルドア', 'B連通', 'Bサイト']))

# ---------------- クロスポート（未校正） ----------------
GRAPHS.append(build('crossport',
    nodes={'赤リス': '赤リス', 'ステージ': 'ステージ', 'Aロン出口': 'Aロン', 'Aサイト': 'A広場', 'Aダクト': 'Aダクト', 'ダクト': 'ダクト',
           '半地下': '半地下', 'ダクト部屋': 'ダクト部屋', 'ダブドア': 'ダブドア', 'チャンピオン': 'チャンピオン', '青リス': '青リス',
           'ショート部屋': 'ショート部屋', 'Bショート': 'Bショート', 'Bロング出口': 'Bロング', 'B箱': 'B箱', 'Bサイト': 'ホワイトハウス', '頭1個': '頭1個'},
    edges=[('赤リス', 'ステージ', []), ('ステージ', 'Aロン出口', []), ('Aロン出口', 'Aサイト', ['玉']), ('赤リス', 'Aダクト', []),
           ('Aダクト', 'ダクト', []), ('ダクト', '半地下', []), ('半地下', 'ダクト部屋', []), ('ダクト部屋', 'Aサイト', []),
           ('Aサイト', 'ダブドア', []), ('ダブドア', '青リス', []), ('青リス', 'チャンピオン', []), ('チャンピオン', 'Bショート', []),
           ('Bショート', 'Bサイト', []), ('チャンピオン', 'ダクト部屋', []), ('赤リス', '頭1個', []), ('頭1個', 'Bロング出口', []),
           ('Bロング出口', 'B箱', []), ('B箱', 'Bサイト', []), ('ダクト', 'ショート部屋', []), ('ショート部屋', 'Bショート', [])],
    attack=['Aロン出口', '半地下', 'ダクト部屋', 'ショート部屋', 'Bロング出口', 'B箱'],
    defend=['Aサイト', 'ダブドア', 'チャンピオン', 'Bショート', 'Bサイト']))

# ---------------- ドラゴンロード（未校正） ----------------
GRAPHS.append(build('dragonroad',
    nodes={'赤リスポ': '赤リスポ', 'ピンク': 'ピンク', '屋台': '屋台', 'Aサイト': 'Aポイント', 'トラック': 'トラック', 'テロ部屋': 'テロ部屋',
           'ふすま': 'ふすま', '広場': '広場', '連通': '連通', '裏広場': '裏広場', 'CT階段': 'CT階段', 'じゅうたん': 'じゅうたん', '青リスポ': '青リスポ',
           '橋': '橋上', 'テロ階段': 'テロ階段', 'Bロング': 'Bロング', '看板': '看板', 'Bサイト': 'Bポイント', 'B下': 'B下', 'ドラム缶': 'ドラム缶'},
    edges=[('赤リスポ', 'ピンク', []), ('ピンク', '屋台', []), ('屋台', 'Aサイト', []), ('Aサイト', 'トラック', []), ('トラック', '裏広場', ['1番']),
           ('裏広場', '青リスポ', ['CT階段']), ('赤リスポ', 'テロ部屋', []), ('テロ部屋', 'ふすま', []), ('ふすま', '広場', []), ('広場', 'Aサイト', []),
           ('広場', '連通', []), ('連通', '裏広場', ['2番']), ('テロ部屋', '橋', []), ('橋', 'じゅうたん', []), ('じゅうたん', 'CT階段', []),
           ('じゅうたん', '青リスポ', ['CT']), ('テロ部屋', 'テロ階段', []), ('テロ階段', 'Bロング', []), ('Bロング', '看板', []), ('看板', 'Bサイト', []),
           ('看板', 'B下', []), ('B下', 'ドラム缶', []), ('ドラム缶', 'Bサイト', []), ('青リスポ', 'B下', ['らせん'])],
    attack=['屋台', '広場', '連通', '橋', 'Bロング', '看板'],
    defend=['Aサイト', 'トラック', 'CT階段', 'じゅうたん', 'ドラム缶', 'Bサイト']))

# ---------------- 計算 ----------------
out_dir = os.path.join(ROOT, 'data', 'timemap'); os.makedirs(out_dir, exist_ok=True)
# 第3補給倉庫の校正
g0 = GRAPHS[0]; cb = g0['calib']
px = math.dist(cb['start'], cb['goal']); px_per_knife_sec = px / cb['sec']
print(f"校正: {cb['start']}→{cb['goal']} = {px:.0f}px = {cb['sec']}s → {px_per_knife_sec:.1f} px/秒（ナイフ）")
index = []
EDITS = os.path.join(ROOT, 'data', 'timemap', 'edits')
for G in GRAPHS:
    # 本人が editor.html で直した通路があれば、それを正とする
    ep = os.path.join(EDITS, G['map'] + '.json')
    if os.path.exists(ep):
        e = json.load(open(ep, encoding='utf-8'))
        G['nodes'] = {k: tuple(v) for k, v in e['nodes'].items()}
        G['edges'] = [{'a': x['a'], 'b': x['b'], 'pts': [tuple(p) for p in x['pts']], 'px': round(sum(math.dist(x['pts'][i], x['pts'][i+1]) for i in range(len(x['pts'])-1)), 1)} for x in e['edges']]
        if e.get('team'):
            G['attack'] = [n for n, t in e['team'].items() if t == 'atk' and n in G['nodes']]
            G['defend'] = [n for n, t in e['team'].items() if t == 'def' and n in G['nodes']]
        if e.get('attack'): G['attack'] = e['attack']
        if e.get('defend'): G['defend'] = e['defend']
        if e.get('ref'): G['ref'] = e['ref']
        if e.get('px_per_knife_sec'): G['pxs_override'] = e['px_per_knife_sec']; G['calib'] = e.get('calib')
        G['edited'] = True; print(G['map'], '← 本人の編集を使用', len(G['edges']), '通路')
    else:
        # 本人が置いた物だけを使う方針（2026-10-04）。私の仮の点は出さない
        G['nodes'] = {}; G['edges'] = []; G['attack'] = []; G['defend'] = []; G['edited'] = False
    G['px_per_knife_sec'] = round(px_per_knife_sec, 2)
    G['calibrated'] = G['calib'] is not None
    G['weapons'] = WEAPONS
    names = list(G['nodes'].keys())
    M = {}; paths = {}
    for s in names:
        dist, prev = dijkstra(G, s)
        M[s] = {t: (round(dist[t] / pxs, 1) if t in dist else None) for t in names}  # ナイフ秒。つながっていなければ None
        for t in names:
            if t == s or t not in dist: continue
            p = [t]
            while p[-1] != s: p.append(prev[p[-1]])
            paths[f'{s}|{t}'] = p[::-1]
    G['knife_sec'] = M; G['paths'] = paths
    # 要約表
    def rows(pairs):
        return [{'from': s, 'to': t, 'knife_sec': M[s][t]} for s, t in pairs if M[s][t] is not None]
    atk = G['attack']; dfn = G['defend']
    def nearest(s, pool):
        c = [(M[s][t], t) for t in pool if M[s][t] is not None and t != s]
        return {'from': s, 'to': min(c)[1], 'knife_sec': min(c)[0]} if c else None
    G['tables'] = {
        '通路ごと': [{'from': e['a'], 'to': e['b'], 'knife_sec': round(e['px'] / pxs, 1)} for e in G['edges']],
        '攻めポイント間': rows([(s, t) for i, s in enumerate(atk) for t in atk[i + 1:]]),
        '守りポイント間': rows([(s, t) for i, s in enumerate(dfn) for t in dfn[i + 1:]]),
        '攻め→一番近い守り': [r for r in (nearest(s, dfn) for s in atk) if r],
    }
    G['all_names'] = names
    json.dump(G, open(os.path.join(out_dir, G['map'] + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    index.append({'map': G['map'], 'name': MAPS[G['map']]['name'], 'calibrated': G['calibrated']})
    print(G['map'], 'nodes', len(names), 'edges', len(G['edges']), 'calibrated' if G['calibrated'] else '未校正')
    for r in G['tables']['攻めポイント間'][:3]: print('   ', r)
json.dump({'maps': index, 'weapons': WEAPONS, 'knife_sec_course': KNIFE_SEC}, open(os.path.join(out_dir, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
