# -*- coding: utf-8 -*-
"""移動速度の実測（ゲーム窓が最前面・一人称で壁に向いている状態で使う）

やること: 指定キーを押しっぱなしにして、画面中央の世界の部分が変化しなくなる（壁に当たって止まる）までの秒数を測る。
  python tools/speedtest.py W            … W を押して止まるまでの秒数（1 本）
  python tools/speedtest.py W --hold shift   … Shift を押しながら W（歩き）
  python tools/speedtest.py W --hold ctrl    … Ctrl を押しながら W（しゃがみ）
  python tools/speedtest.py S            … 戻り（計測はするが使わない）
  python tools/speedtest.py --probe 3    … 3 秒間ただ撮って差分の値を見る（しきい値決め用）
結果は 1 行の JSON で標準出力に出す。 {"key":"W","hold":"shift","t_move":..,"t_stop":..,"dur":..}
"""
import ctypes, time, json, sys, argparse
from ctypes import wintypes
import numpy as np
from PIL import ImageGrab

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

# ---- SendInput（スキャンコード。DirectInput 系のゲームはこれでないと効かない事が多い）----
SC = {'W': 0x11, 'A': 0x1E, 'S': 0x1F, 'D': 0x20, 'shift': 0x2A, 'ctrl': 0x1D, '1': 0x02, '2': 0x03, '3': 0x04, 'space': 0x39}
KEYEVENTF_SCANCODE = 0x0008; KEYEVENTF_KEYUP = 0x0002
ULONG_PTR = ctypes.c_size_t
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]
class _I(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("pad", ctypes.c_byte * 32)]
class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _I)]
def key(name, down=True):
    inp = INPUT(); inp.type = 1
    inp.u.ki = KEYBDINPUT(0, SC[name], KEYEVENTF_SCANCODE | (0 if down else KEYEVENTF_KEYUP), 0, 0)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

# ---- 撮影（主モニタ 1920x1080 の中央・武器モデルと HUD を避けた上半分）----
BOX = (560, 200, 1360, 560)   # left, top, right, bottom（実座標）
def grab():
    im = ImageGrab.grab(bbox=BOX).convert('L').resize((160, 72))
    return np.asarray(im, dtype=np.int16)
def diff(a, b): return float(np.abs(a - b).mean())

def probe(sec):
    prev = grab(); t0 = time.perf_counter(); out = []
    while time.perf_counter() - t0 < sec:
        cur = grab(); out.append(round(diff(prev, cur), 2)); prev = cur
    print(json.dumps({'probe': out, 'fps': round(len(out) / sec, 1)}))

def record(sec, out):
    """キーは押さず、sec 秒のあいだ差分を記録して out に JSON で書く（キーは別の係が押す）"""
    prev = grab(); t0 = time.perf_counter(); frames = []
    while True:
        now = time.perf_counter() - t0
        if now > sec: break
        cur = grab(); frames.append((round(now, 3), round(diff(prev, cur), 2))); prev = cur
    json.dump({'t0_epoch': time.time() - frames[-1][0], 'frames': frames}, open(out, 'w'))
    print(json.dumps({'recorded': len(frames), 'sec': sec, 'out': out}))

def analyze2(frames, still=0.5):
    """動いている間の差分の中央値を基準に、その 40% を下回り続けた所を「壁に当たった」と見る。
    戻り値: {'t_move','t_stop','dur','level_move','level_stop'}（見つからなければ None）"""
    import statistics
    ts = [t for t, d in frames]; ds = [d for t, d in frames]
    n = len(ds)
    if n < 20: return None
    # 1) 動き出し: 差分が 1.5 を 3 フレーム続けて超えた所
    t_move = None
    for i in range(n - 3):
        if ds[i] > 1.5 and ds[i + 1] > 1.5 and ds[i + 2] > 1.5: t_move = ts[i]; i_move = i; break
    if t_move is None: return None
    # 2) 動いている間の水準: 動き出しから 1 秒間の中央値
    win = [d for t, d in frames if t_move + 0.2 <= t <= t_move + 1.2]
    lvl = statistics.median(win) if win else None
    if not lvl: return None
    thr = lvl * 0.4
    # 3) 止まり: thr を still 秒以上下回り続けた最初の時刻
    t_stop = None; since = None
    for t, d in frames[i_move + 3:]:
        if d < thr:
            if since is None: since = t
            elif t - since >= still: t_stop = since; break
        else: since = None
    stop_lvl = statistics.median([d for t, d in frames if t_stop is not None and t >= t_stop]) if t_stop is not None else None
    return {'t_move': round(t_move, 3), 't_stop': (round(t_stop, 3) if t_stop else None), 'dur': (round(t_stop - t_move, 3) if t_stop else None), 'level_move': round(lvl, 2), 'level_stop': (round(stop_lvl, 2) if stop_lvl is not None else None)}

def analyze3(frames):
    """壁に当たって止まった時刻を「キーを離す直前の水準」から逆算する。
    走行中の水準と、離す直前 1 秒の水準（壁でのボブ）の中間をしきい値にし、
    そこから後ろがずっとしきい値以下になる最初の時刻を到着とする（途中のラグの凹みに騙されない）"""
    import statistics
    ts = [t for t, d in frames]; ds = [d for t, d in frames]; n = len(ds)
    t_move = None
    for i in range(n - 3):
        if ds[i] > 1.5 and ds[i + 1] > 1.5 and ds[i + 2] > 1.5: t_move = ts[i]; i_move = i; break
    if t_move is None: return None
    # キーを離した時刻: 後ろから見て d<0.5 が続く区間の始まり
    # キーを離した時刻: 動き出しの後で、d<0.5 が 15 コマ（約0.5秒）続く最初の所（録画の終わりに本人が動いても平気）
    i_rel = None
    for i in range(i_move + 30, n - 15):
        if all(x < 0.5 for x in ds[i:i + 15]): i_rel = i; break
    if i_rel is None: i_rel = n - 1
    if i_rel - i_move < 30: return None
    t_release = ts[i_rel]
    lvl_move = statistics.median(ds[i_move + 6: i_move + 36])
    lvl_end = statistics.median(ds[max(i_move, i_rel - 30): i_rel])
    thr = (lvl_move + lvl_end) / 2
    # 単発のスパイク（ナイフの素振り等）に騙されないよう、9 コマの移動中央値で後ろから走査
    sm = [statistics.median(ds[max(0, i - 4): i + 5]) for i in range(n)]
    i_stop = i_rel
    while i_stop - 1 > i_move and sm[i_stop - 1] < thr: i_stop -= 1
    t_stop = ts[i_stop]
    return {'t_move': round(t_move, 3), 't_stop': round(t_stop, 3), 'dur': round(t_stop - t_move, 3), 't_release': round(t_release, 3),
            'level_move': round(lvl_move, 2), 'level_wall': round(lvl_end, 2), 'thr': round(thr, 2), 'wall_sec': round(t_release - t_stop, 2)}

def analyze(frames, thr=1.5, still=0.6, min_move=0.5):
    """差分列から 動き出し→止まり の区間を全部拾う。[(t_move, t_stop, dur), ...]"""
    segs = []; hot = 0; first_hot = None; t_move = None; still_since = None
    for now, d in frames:
        if t_move is None:
            if d > thr:
                hot += 1
                if hot == 1: first_hot = now
                if hot >= 3: t_move = first_hot
            else: hot = 0
        else:
            if d < thr:
                if still_since is None: still_since = now
                elif now - still_since >= still:
                    if still_since - t_move >= min_move: segs.append((round(t_move, 3), round(still_since, 3), round(still_since - t_move, 3)))
                    t_move = None; still_since = None; hot = 0
            else: still_since = None
    return segs

def run(k, hold, maxsec, thr, still):
    frames = []  # (t, diff)
    prev = grab()
    if hold: key(hold, True); time.sleep(0.15)
    t0 = time.perf_counter(); key(k, True)
    t_move = None; t_stop = None; still_since = None; hot = 0; first_hot = None
    try:
        while True:
            now = time.perf_counter() - t0
            cur = grab(); d = diff(prev, cur); prev = cur; frames.append((round(now, 3), round(d, 2)))
            if t_move is None:
                if d > thr:
                    hot += 1
                    if hot == 1: first_hot = now
                    if hot >= 3: t_move = first_hot
                else: hot = 0
            if t_move is not None:
                if d < thr:
                    if still_since is None: still_since = now
                    elif now - still_since >= still: t_stop = still_since; break
                else: still_since = None
            if now > maxsec: break
    finally:
        key(k, False)
        if hold: time.sleep(0.05); key(hold, False)
    fps = len(frames) / max(frames[-1][0], 1e-6)
    print(json.dumps({'key': k, 'hold': hold, 't_move': t_move, 't_stop': t_stop, 'dur': (None if t_stop is None or t_move is None else round(t_stop - t_move, 3)), 'fps': round(fps, 1), 'frames': frames}, ensure_ascii=False))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('key', nargs='?', default='W')
    ap.add_argument('--hold', default=None)
    ap.add_argument('--max', type=float, default=15)
    ap.add_argument('--thr', type=float, default=1.5)
    ap.add_argument('--still', type=float, default=0.6)
    ap.add_argument('--probe', type=float, default=0)
    ap.add_argument('--tap', default=None, help='1 キーだけ押して離す（武器切替など）')
    ap.add_argument('--record', type=float, default=0, help='この秒数だけ差分を記録（キーは押さない）')
    ap.add_argument('--out', default='tools/rec.json')
    ap.add_argument('--analyze', default=None, help='記録 JSON を解析して区間を出す')
    a = ap.parse_args()
    if a.tap: key(a.tap, True); time.sleep(0.08); key(a.tap, False); print(json.dumps({'tap': a.tap})); sys.exit()
    if a.probe: probe(a.probe); sys.exit()
    if a.record: record(a.record, a.out); sys.exit()
    if a.analyze:
        d = json.load(open(a.analyze)); print(json.dumps(analyze3(d['frames']))); sys.exit()
    run(a.key, a.hold, a.max, a.thr, a.still)
