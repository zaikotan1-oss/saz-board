// 掲示板の置き場（editor.html と board.html で共通）
//  手元: tools/save_server.py（8843）→ data/board/<名前>.json
//  公開: board-config.js の firebase の URL があれば Firebase Realtime Database（REST）
//  どちらも無い（GitHub Pages など）: data/board/<名前>.json を読むだけ（書けない）
window.SazStore = (() => {
  const LOCAL = 'http://127.0.0.1:8843';
  const CFG = window.BOARD_CONFIG || {};
  let mode = null;
  const dev = (() => { try { let d = localStorage.getItem('saz-dev'); if (!d) { d = Math.random().toString(36).slice(2) + Date.now().toString(36); localStorage.setItem('saz-dev', d); } return d; } catch (e) { return 'anon'; } })();
  const newId = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
  async function detect() {
    if (mode) return mode;
    if (CFG.firebase) { mode = 'firebase'; return mode; }
    try { const r = await fetch(LOCAL + '/ping', { signal: AbortSignal.timeout(1500) }); if (r.ok) { mode = 'local'; return mode; } } catch (e) {}
    mode = 'static'; return mode;
  }
  async function list(col) {
    const m = await detect();
    try {
      if (m === 'firebase') { const r = await fetch(`${CFG.firebase}/saz/${col}.json`); const o = (await r.json()) || {}; return Object.entries(o).map(([id, v]) => ({ ...v, id })).sort((a, b) => (a.t || 0) - (b.t || 0)); }
      if (m === 'local') { const r = await fetch(`${LOCAL}/kv?col=${col}&t=${Date.now()}`); return r.ok ? await r.json() : []; }
      const r = await fetch(`data/board/${col}.json?t=${Date.now()}`); return r.ok ? await r.json() : [];
    } catch (e) { return []; }
  }
  async function add(col, item) {
    const m = await detect(); item = { ...item, t: Date.now(), dev };
    if (m === 'firebase') { const r = await fetch(`${CFG.firebase}/saz/${col}.json`, { method: 'POST', body: JSON.stringify(item) }); if (!r.ok) throw new Error('save failed'); const { name } = await r.json(); return { ...item, id: name }; }
    if (m === 'local') { item.id = newId(); const r = await fetch(`${LOCAL}/kv?col=${col}`, { method: 'POST', body: JSON.stringify(item) }); if (!r.ok) throw new Error('save failed'); return item; }
    throw new Error('readonly');
  }
  async function remove(col, id) {
    const m = await detect();
    if (m === 'firebase') { const r = await fetch(`${CFG.firebase}/saz/${col}/${id}.json`, { method: 'DELETE' }); return r.ok; }
    if (m === 'local') { const r = await fetch(`${LOCAL}/kv?col=${col}&id=${id}&dev=${dev}`, { method: 'DELETE' }); return r.ok; }
    return false;
  }
  // 地図の書き込みの種類（絵で分かるように）
  const KINDS = [
    { k: 'star', label: '強ポジ', emoji: '⭐', color: '#c99a00' },
    { k: 'smoke', label: 'スモーク', emoji: '💨', color: '#6b7280' },
    { k: 'warn', label: '注意', emoji: '⚠️', color: '#c0392b' },
    { k: 'ambush', label: '待ち伏せ', emoji: '👁️', color: '#7d3c98' },
    { k: 'bomb', label: '爆弾', emoji: '💣', color: '#2c2c2c' },
    { k: 'nade', label: 'グレ/フラ', emoji: '💥', color: '#d35400' },
    { k: 'memo', label: 'メモ', emoji: '📝', color: '#2f7de1' },
  ];
  const kindOf = k => KINDS.find(x => x.k === k) || KINDS[KINDS.length - 1];
  // 地図の上に印を描く（editor の PNG にも同じ物が入る）。posts: 位置つきの物だけ描く
  function drawPins(c, posts, opt = {}) {
    const R = opt.r || 14, hi = opt.highlight;
    posts.forEach((p, i) => {
      if (p.x == null || p.y == null) return;
      const K = kindOf(p.kind);
      c.save();
      c.beginPath(); c.arc(p.x, p.y, R + 2, 0, Math.PI * 2); c.fillStyle = 'rgba(0,0,0,.55)'; c.fill();
      c.beginPath(); c.arc(p.x, p.y, R, 0, Math.PI * 2); c.fillStyle = K.color; c.fill();
      c.lineWidth = hi === p.id ? 4 : 2; c.strokeStyle = hi === p.id ? '#fff' : 'rgba(255,255,255,.85)'; c.stroke();
      c.font = `${Math.round(R * 1.15)}px "Segoe UI Emoji","Apple Color Emoji","Noto Color Emoji",sans-serif`; c.textAlign = 'center'; c.textBaseline = 'middle';
      c.fillStyle = '#fff'; c.fillText(K.emoji, p.x, p.y + 1);
      // 番号
      c.beginPath(); c.arc(p.x + R - 2, p.y - R + 2, 8, 0, Math.PI * 2); c.fillStyle = '#fff'; c.fill();
      c.font = 'bold 10px "Yu Gothic UI","Meiryo",sans-serif'; c.fillStyle = '#000'; c.fillText(String(i + 1), p.x + R - 2, p.y - R + 3);
      // 一言（短く）
      if (opt.labels !== false && p.text) {
        const t = p.text.length > 10 ? p.text.slice(0, 10) + '…' : p.text;
        c.font = 'bold 11px "Yu Gothic UI","Meiryo",sans-serif'; const w = c.measureText(t).width + 10;
        c.fillStyle = 'rgba(0,0,0,.7)'; c.beginPath(); c.roundRect(p.x - w / 2, p.y + R + 3, w, 16, 4); c.fill();
        c.fillStyle = '#fff'; c.fillText(t, p.x, p.y + R + 11);
      }
      c.restore();
    });
  }
  const fmtTime = t => { const d = new Date(t); return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`; };
  const esc = s => String(s ?? '').replace(/[&<>"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));
  return { detect, list, add, remove, dev, KINDS, kindOf, drawPins, fmtTime, esc, get mode() { return mode; } };
})();
