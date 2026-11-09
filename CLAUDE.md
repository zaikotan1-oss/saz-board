# SAZ 作戦ボード（saz-board）

サドンアタック：ゼロポイントの爆破戦で「攻め方のバリエーション」を人の配置と動く順番つきで図にする道具。
入口はトップページ `index.html`（全ページへのリンク）。作戦ボードは `pattern.html`。見本パターンは生成スクリプトから作る。

## 入口
- 画面: `（このフォルダで）python -m http.server 8840` → http://localhost:8840 （launch.json の `saz-board`）
- 作業の記録・残件: `context/README.md`
- 利用者向けの使い方は画面右の「道具」の下に書いてある

## 構成
| 物 | 役目 |
|---|---|
| `index.html` | トップページ。感度（Aiming.Pro・確かめ方 aim/guide.html・感度くらべ aim/）／作戦（作戦ノート・動画置き場）／そのほか のリンク。こうさくさんの要件 1（11-09） |
| `pattern.html` | 作戦ボード本体（11-09 に index.html から改名）。canvas 1 枚に下地→地名→サイト→経路→印→駒の順で描く。`window.__board.exportDataURL()` が PNG 化の窓口 |
| `maps/maps.json` | マップ一覧（id・名前・画像・リスポ・サイト・地名の座標・`labelsInImage`）と役割一覧 |
| `maps/*.jpg,png` | 下地の俯瞰図（原作サドンアタックの 2012 年ブログ画像。`maps/raw/` に元と出所） |
| `tools/make_patterns.py` | 見本パターン（16 本）を地名から生成 → `patterns/*.json` と `patterns/index.json` |
| `editor.html` | 移動時間エディター（点・通路・縮尺・武器切替・全地点間の表・PNG）。保存は `tools/save_server.py`（8843、常駐）→ `data/timemap/edits/<map>.json`。Pages では JSON ファイルで受け渡し |
| `board.html` + `store.js` + `board-config.js` | クラン掲示板（スマホ向け）。地図の書き込み（⭐強ポジ/💨スモーク/⚠注意/👁待ち伏せ/💣爆弾/💥グレ/📝メモ を地図の場所に貼る）と検証メモ（項目ごとに 効く/効かない/不明）。書き込みごとに返信スレッド（置き場 `rep_<書き込みid>`）と画像（縮小 JPEG。本文に thumb、本体は `img/<id>` に base64 で別置き・タップで取る）。置き場は store.js が自動で選ぶ: board-config.js の Firebase URL → 手元 save_server（`data/board/<名前>.json`）→ Pages は data/board の写しを読むだけ。印は editor の地図と PNG にも出る |
| `tree.html` | 作戦ノート。マップを選ぶと地図が出て、**地図に印を打つとそれが大項目**（`x,y,kind`。印は上から見た銃を構えた人 `soldier`＝既定。印をタップでその大項目が開く・場所なしの大項目も可）。「大項目→中項目→小項目」のツリー（何段でも）に文（改行・インデントそのまま）と画像（複数・thumb＋`img/<id>`）をぶら下げる。置き場 `tree`（`parent` で親を指す平らな形。大項目だけ `map`）。直すのはだれでも（`update`＝PATCH）・消すのは自分の端末の分で下に項目が無い物だけ。開きぐあいは localStorage。クランの藤田さん・こうさくさんの要望の形（11-08）。11-09: **タグ**（置き場 `tags`＝名前と色、項目の `tags:[名前]`、何個でも・だれでも作れる）、**検索**（キーワード＋タグで全マップ・全階層を絞る → タップで飛ぶ。`?tag=赤` `?q=語` でも開ける）、**地名**（置き場 `places`＝`text,map,x,y`。maps.json の callouts を tools/seed_places.py で写した。地図の上に描き、タップでその地名の項目だけに絞る。「✏ 地名を直す」で名前・場所・追加・削除。大項目は `place` で地名を指す。印を打つと 45px 以内の地名が自動で付く）、並びは動きがあった順（新しい順・下の項目も含む） |
| `videos.html` | 動画置き場。YouTube 限定公開の URL を貼る（置き場 `videos`＝`name,text,url,memo`）。投稿した人ごと（大項目）→ タイトル（中項目）。小さい絵をタップでページ内再生（youtube-nocookie の埋め込み・`t=` の頭出しも）。YouTube 以外はリンクだけ。直す・消すは自分の端末の分 |
| `stats.html` + `data/stats.json` | ステータス図鑑。武器の基本 5 項目とパーツのオプションの意味（推測は「たぶん」）・検証状況・実測・測り方・出典。掲示板の検証メモを項目名で突き合わせて下に出す。検証したら stats.json の `measured`/`status` を直す |
| `tools/crosshair_timing.py` | 動画から「撃つ→クロスヘアが閉じ切る」までの秒数を測る（中央の線を色で拾って開きをコマごとに測る）。2 本渡すと比較も出す。合成動画で検証済み |
| `tools/timemap_build.py` / `tools/export_timemap.py` | edits から表を再計算 → `data/timemap/<map>.json`、editor.html を使って武器別 PNG → `data/timemap/png/` |
| `tools/export_png.py` | 見本を全部 PNG に（Playwright のヘッドレス Chromium、8841 を一時的に使う） → `patterns/png/` |

## 決まり
- 座標は maps.json の地名で書く（`C(map, '地名', dx, dy)`）。数字の直書きはしない
- 見本を直す時は `make_patterns.py` を直して `make_patterns.py` → `export_png.py` の順に流す
- 俯瞰図が無いマップ（地下鉄・シティキャット・ウェアハウス・サドン村）は格子の下地。利用者がゲーム内の全体図のスクショをボードにドロップすると差し替わる（ブラウザに記憶、マップごと）
- ゲーム本体のファイル（.pkg）を開いて絵を取り出すことはしない（アンチチート・規約の都合）
