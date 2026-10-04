# SAZ 作戦ボード（saz-board）

サドンアタック：ゼロポイントの爆破戦で「攻め方のバリエーション」を人の配置と動く順番つきで図にする道具。
HTML 1 枚（`index.html`）。見本パターンは生成スクリプトから作る。

## 入口
- 画面: `python -m http.server 8840 --directory C:/Users/zaiko/saz-board` → http://localhost:8840 （launch.json の `saz-board`）
- 作業の記録・残件: `context/README.md`
- 利用者向けの使い方は画面右の「道具」の下に書いてある

## 構成
| 物 | 役目 |
|---|---|
| `index.html` | ボード本体。canvas 1 枚に下地→地名→サイト→経路→印→駒の順で描く。`window.__board.exportDataURL()` が PNG 化の窓口 |
| `maps/maps.json` | マップ一覧（id・名前・画像・リスポ・サイト・地名の座標・`labelsInImage`）と役割一覧 |
| `maps/*.jpg,png` | 下地の俯瞰図（原作サドンアタックの 2012 年ブログ画像。`maps/raw/` に元と出所） |
| `tools/make_patterns.py` | 見本パターン（16 本）を地名から生成 → `patterns/*.json` と `patterns/index.json` |
| `editor.html` | 移動時間エディター（点・通路・縮尺・武器切替・全地点間の表・PNG）。保存は `tools/save_server.py`（8843、常駐）→ `data/timemap/edits/<map>.json`。Pages では JSON ファイルで受け渡し |
| `tools/timemap_build.py` / `tools/export_timemap.py` | edits から表を再計算 → `data/timemap/<map>.json`、editor.html を使って武器別 PNG → `data/timemap/png/` |
| `tools/export_png.py` | 見本を全部 PNG に（Playwright のヘッドレス Chromium、8841 を一時的に使う） → `patterns/png/` |

## 決まり
- 座標は maps.json の地名で書く（`C(map, '地名', dx, dy)`）。数字の直書きはしない
- 見本を直す時は `make_patterns.py` を直して `make_patterns.py` → `export_png.py` の順に流す
- 俯瞰図が無いマップ（地下鉄・シティキャット・ウェアハウス・サドン村）は格子の下地。利用者がゲーム内の全体図のスクショをボードにドロップすると差し替わる（ブラウザに記憶、マップごと）
- ゲーム本体のファイル（.pkg）を開いて絵を取り出すことはしない（アンチチート・規約の都合）
