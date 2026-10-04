# -*- coding: utf-8 -*-
"""ミニマップのずれで移動距離を測る。
  python tools/minimap.py save a.png          … 今のミニマップ領域を保存
  python tools/minimap.py shift a.png b.png   … 2 枚のずれ（px）を出す
ミニマップは自機中心なので、自機が動くと下の地図がずれる。そのずれ量＝移動距離（ミニマップ px）。
"""
import sys, json, ctypes
import numpy as np, cv2
from PIL import ImageGrab
ctypes.windll.user32.SetProcessDPIAware()
BOX = (0, 130, 345, 370)  # 実座標（1920x1080）

def save(path):
    ImageGrab.grab(bbox=BOX).save(path); print(json.dumps({'saved': path}))

def shift(a, b):
    A = cv2.imread(a, cv2.IMREAD_GRAYSCALE).astype(np.float32)
    B = cv2.imread(b, cv2.IMREAD_GRAYSCALE).astype(np.float32)
    # 文字（地名）の部分は動かないので、下 60px を落とす
    A = A[:-60]; B = B[:-60]
    win = cv2.createHanningWindow(A.shape[::-1], cv2.CV_32F)
    (dx, dy), resp = cv2.phaseCorrelate(A, B, win)
    print(json.dumps({'dx': round(dx, 2), 'dy': round(dy, 2), 'dist': round(float(np.hypot(dx, dy)), 2), 'resp': round(resp, 3)}))

def rot(a, b):
    """2 枚のミニマップの回転角（度）と平行移動。ORB 特徴点で部分アフィンを推定"""
    A = cv2.imread(a, cv2.IMREAD_GRAYSCALE)[:-60]; B = cv2.imread(b, cv2.IMREAD_GRAYSCALE)[:-60]
    orb = cv2.ORB_create(1500)
    ka, da = orb.detectAndCompute(A, None); kb, db = orb.detectAndCompute(B, None)
    if da is None or db is None: print(json.dumps({'error': 'no features'})); return
    m = sorted(cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db), key=lambda x: x.distance)[:200]
    pa = np.float32([ka[x.queryIdx].pt for x in m]); pb = np.float32([kb[x.trainIdx].pt for x in m])
    M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=3)
    if M is None: print(json.dumps({'error': 'no model'})); return
    ang = float(np.degrees(np.arctan2(M[1, 0], M[0, 0]))); sc = float(np.hypot(M[0, 0], M[1, 0]))
    print(json.dumps({'angle_deg': round(ang, 1), 'scale': round(sc, 3), 'tx': round(float(M[0, 2]), 1), 'ty': round(float(M[1, 2]), 1), 'inliers': int(inl.sum()), 'matches': len(m)}))

if __name__ == '__main__':
    if sys.argv[1] == 'save': save(sys.argv[2])
    elif sys.argv[1] == 'rot': rot(sys.argv[2], sys.argv[3])
    else: shift(sys.argv[2], sys.argv[3])
