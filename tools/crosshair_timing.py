# -*- coding: utf-8 -*-
"""撃ってからクロスヘアが閉じ切るまでの時間を動画から測る。
使い方:
  python tools/crosshair_timing.py 動画A.mp4 [動画B.mp4 ...] [--label A,B] [--out 出力フォルダ]
  任意: --roi 120   画面中央から何 px 四方を見るか（既定 160）
        --color auto|white|green|...  クロスヘアの色（既定 auto＝中央付近の目立つ色を自動で拾う）
        --axis h|v|both  横線の間隔(h)・縦線の間隔(v)・両方の平均(both、既定)
        --settle 0.15    閉じたと見なす「元の幅＋余裕」（px）。既定は撃つ前の幅の揺れから自動
出力: <out>/<動画名>_gap.csv（コマごとの開き）、<out>/<動画名>_gap.png（グラフ）、<out>/summary.json と画面に要約。
仕組み: 画面中央のクロスヘアの線を色で拾い、中心から左右（上下）の最も内側の線までの距離＝「開き」をコマごとに測る。
        撃つ＝開きが急に大きくなるコマ。閉じ切る＝開きが撃つ前の幅に戻って N コマ続いた最初のコマ。"""
import argparse, csv, json, os, sys, io
import numpy as np, cv2
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

COLORS = {  # HSV の範囲（OpenCV: H 0-179, S 0-255, V 0-255）
    'white': ((0, 0, 180), (179, 60, 255)),
    'green': ((40, 80, 120), (85, 255, 255)),
    'cyan': ((85, 80, 120), (105, 255, 255)),
    'red': ((0, 100, 120), (10, 255, 255)),
    'yellow': ((20, 100, 120), (35, 255, 255)),
    'magenta': ((140, 80, 120), (170, 255, 255)),
}

def auto_color(frames_hsv):
    """中央付近で「彩度か明度が高い」画素の色相を集計して一番多い色を選ぶ"""
    best, bestn = 'white', -1
    for name, (lo, hi) in COLORS.items():
        n = 0
        for hsv in frames_hsv:
            m = cv2.inRange(hsv, np.array(lo), np.array(hi)); n += int(m.sum() // 255)
        if n > bestn: best, bestn = name, n
    return best

def gap_of(mask, axis):
    """mask: 中央 ROI の 2 値。中心から外へ見て最初に線に当たる距離（左右/上下の平均）"""
    h, w = mask.shape; cy, cx = h // 2, w // 2
    def first_hit(line, start, step):
        i = start
        while 0 <= i < len(line):
            if line[i]: return abs(i - start)
            i += step
        return None
    vals = []
    if axis in ('h', 'both'):
        row = mask[cy - 1:cy + 2].max(axis=0)  # 中心の 3 行
        l = first_hit(row, cx - 2, -1); r = first_hit(row, cx + 2, 1)
        if l is not None and r is not None: vals.append((l + r) / 2)
    if axis in ('v', 'both'):
        col = mask[:, cx - 1:cx + 2].max(axis=1)
        u = first_hit(col, cy - 2, -1); d = first_hit(col, cy + 2, 1)
        if u is not None and d is not None: vals.append((u + d) / 2)
    return float(np.mean(vals)) if vals else None

def analyze(path, roi, color, axis, settle_arg, out):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened(): raise SystemExit(f'開けません: {path}')
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0; W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    x0, y0 = W // 2 - roi // 2, H // 2 - roi // 2
    frames = []; hsvs = []
    while True:
        ok, f = cap.read()
        if not ok: break
        frames.append(f[y0:y0 + roi, x0:x0 + roi])
    cap.release()
    if not frames: raise SystemExit('コマが読めません')
    hsvs = [cv2.cvtColor(f, cv2.COLOR_BGR2HSV) for f in frames]
    if color == 'auto': color = auto_color(hsvs[:: max(1, len(hsvs) // 20)])
    lo, hi = COLORS[color]
    gaps = []
    for hsv in hsvs:
        m = cv2.inRange(hsv, np.array(lo), np.array(hi))
        gaps.append(gap_of(m, axis))
    g = np.array([np.nan if v is None else v for v in gaps], dtype=float)
    # 欠けは前の値で埋める
    for i in range(len(g)):
        if np.isnan(g[i]): g[i] = g[i - 1] if i else np.nanmin(g)
    t = np.arange(len(g)) / fps
    # 撃つコマ: 1 コマで開きが「撃つ前の幅の揺れ」よりはっきり大きくなる
    base_n = max(5, int(fps * 0.5))
    shots = []
    i = base_n
    while i < len(g) - 1:
        base = g[max(0, i - base_n):i]; b_med = float(np.median(base)); b_sd = float(np.std(base))
        thr = max(2.0, 4 * b_sd)
        if g[i] - b_med > thr and g[i] >= g[i - 1] + 1.0:
            # 山の頂点まで進める
            j = i
            while j + 1 < len(g) and g[j + 1] >= g[j]: j += 1
            peak = float(g[j])
            settle = settle_arg if settle_arg is not None else (b_med + max(0.75, 2 * b_sd))
            need = max(3, int(fps * 0.1))
            k = j; closed = None
            while k < len(g):
                if g[k] <= settle and all(g[k:k + need] <= settle) and len(g[k:k + need]) == need: closed = k; break
                k += 1
            shots.append({'shot_frame': i, 'shot_t': round(t[i], 4), 'peak_frame': j, 'peak_px': peak, 'base_px': round(b_med, 2), 'settle_px': round(settle, 2),
                          'closed_frame': closed, 'closed_t': (round(t[closed], 4) if closed is not None else None),
                          'recover_s': (round(t[closed] - t[i], 4) if closed is not None else None)})
            i = (closed if closed is not None else j) + 1
        else: i += 1
    name = os.path.splitext(os.path.basename(path))[0]
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, f'{name}_gap.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['frame', 'time_s', 'gap_px']); [w.writerow([i, round(t[i], 4), round(g[i], 2)]) for i in range(len(g))]
    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        plt.rcParams['font.family'] = ['Yu Gothic', 'Meiryo', 'MS Gothic', 'sans-serif']
        fig, ax = plt.subplots(figsize=(10, 3.2)); ax.plot(t, g, lw=1)
        for s in shots:
            ax.axvline(s['shot_t'], color='r', lw=0.8); ax.axhline(s['settle_px'], color='g', lw=0.6, ls='--')
            if s['closed_t'] is not None: ax.axvline(s['closed_t'], color='g', lw=0.8); ax.text(s['shot_t'], s['peak_px'], f"{s['recover_s']:.3f}s", color='r', fontsize=9)
        ax.set_xlabel('秒'); ax.set_ylabel('クロスヘアの開き (px)'); ax.set_title(f'{name}  {fps:.0f}fps  色={color}  撃った数={len(shots)}'); fig.tight_layout(); fig.savefig(os.path.join(out, f'{name}_gap.png'), dpi=110); plt.close(fig)
    except Exception as e: print('グラフは作れませんでした:', e)
    return {'file': path, 'fps': fps, 'frames': len(g), 'color': color, 'roi': roi, 'shots': shots}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('videos', nargs='+'); ap.add_argument('--label', default=''); ap.add_argument('--out', default='tools/runs/crosshair')
    ap.add_argument('--roi', type=int, default=160); ap.add_argument('--color', default='auto'); ap.add_argument('--axis', default='both'); ap.add_argument('--settle', type=float, default=None)
    a = ap.parse_args(); labels = [x.strip() for x in a.label.split(',')] if a.label else []
    results = []
    for i, v in enumerate(a.videos):
        r = analyze(v, a.roi, a.color, a.axis, a.settle, a.out); r['label'] = labels[i] if i < len(labels) else os.path.basename(v); results.append(r)
        rec = [s['recover_s'] for s in r['shots'] if s['recover_s'] is not None]
        print(f"[{r['label']}] {r['fps']:.0f}fps 色={r['color']} 撃った数={len(r['shots'])}" + (f" 閉じるまで 平均 {np.mean(rec):.3f}s（中央値 {np.median(rec):.3f}s・最短 {min(rec):.3f}s・最長 {max(rec):.3f}s）" if rec else ' （撃ったコマが見つからない）'))
        for s in r['shots']: print(f"   撃つ {s['shot_t']:.3f}s → 閉じる {s['closed_t'] if s['closed_t'] is not None else '?'}s  = {s['recover_s'] if s['recover_s'] is not None else '?'}s  (開き {s['base_px']}→{s['peak_px']:.0f}px)")
    if len(results) >= 2:
        recs = [[s['recover_s'] for s in r['shots'] if s['recover_s'] is not None] for r in results]
        if all(recs):
            m = [float(np.mean(x)) for x in recs]
            print(f"比較: {results[0]['label']} {m[0]:.3f}s vs {results[1]['label']} {m[1]:.3f}s → 差 {m[1]-m[0]:+.3f}s（{(m[1]/m[0]-1)*100:+.1f}%）。1 コマ = {1/results[0]['fps']:.3f}s なので、差がこれより小さければ同じと見る")
    json.dump(results, open(os.path.join(a.out, 'summary.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

if __name__ == '__main__': main()
